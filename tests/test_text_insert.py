"""Tests for clipboard save/restore behaviour in insert_text."""

import time
import pytest
from unittest.mock import MagicMock, patch
from vtt.text_insert import insert_text, SUBPROCESS_TIMEOUT


def _popen(returncode=0):
    m = MagicMock()
    m.returncode = returncode
    m.communicate.return_value = (b'', b'')
    return m


def _run(returncode=0, stdout=b'', stderr=''):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Skip all time.sleep calls to keep tests fast."""
    monkeypatch.setattr(time, 'sleep', lambda _: None)


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

class TestBasic:
    def test_empty_string_returns_false_immediately(self):
        assert insert_text("") is False

    def test_none_returns_false_immediately(self):
        assert insert_text(None) is False

    def test_successful_insert_returns_true(self):
        runs = iter([_run(stdout=b'old'), _run()])   # pbpaste
        with patch('vtt.text_insert.subprocess.Popen', return_value=_popen()), \
             patch('vtt.text_insert.subprocess.run', side_effect=runs):
            assert insert_text("hello") is True

    def test_pbcopy_failure_returns_false(self):
        runs = iter([_run(stdout=b'')])               # pbpaste
        with patch('vtt.text_insert.subprocess.Popen', return_value=_popen(returncode=1)), \
             patch('vtt.text_insert.subprocess.run', side_effect=runs):
            assert insert_text("hello") is False

    def test_keystroke_failure_returns_false(self):
        runs = iter([_run(stdout=b'old')])
        with patch('vtt.text_insert.subprocess.Popen', return_value=_popen()), \
             patch('vtt.text_insert.subprocess.run', side_effect=runs), \
             patch('vtt.text_insert.CGEventPost', side_effect=RuntimeError("denied")):
            assert insert_text("hello") is False

    def test_paste_shortcut_is_command_only(self):
        """Held hotkey modifiers (Fn/Ctrl) must not leak into Cmd+V."""
        runs = iter([_run(stdout=b'old')])
        with patch('vtt.text_insert.subprocess.Popen', return_value=_popen()), \
             patch('vtt.text_insert.subprocess.run', side_effect=runs), \
             patch('vtt.text_insert.CGEventSetFlags') as set_flags, \
             patch('vtt.text_insert.CGEventPost') as post:
            assert insert_text("hello") is True
        import vtt.text_insert as ti
        assert post.call_count == 2                       # key down + key up
        for call in set_flags.call_args_list:
            assert call.args[1] is ti.kCGEventFlagMaskCommand

    def test_clipboard_not_restored_until_paste_settles(self, monkeypatch):
        """Restoring too soon makes slow apps paste the old clipboard."""
        events = []
        monkeypatch.setattr(time, 'sleep', lambda s: events.append(('sleep', s)))

        def mock_popen(cmd, **kwargs):
            m = _popen()
            m.communicate.side_effect = lambda data, **kw: events.append(('pbcopy', data))
            return m

        runs = iter([_run(stdout=b'old')])
        with patch('vtt.text_insert.subprocess.Popen', side_effect=mock_popen), \
             patch('vtt.text_insert.subprocess.run', side_effect=runs), \
             patch('vtt.text_insert.CGEventPost', side_effect=lambda *a: events.append(('post',))):
            insert_text("hello")

        from vtt.text_insert import PASTE_SETTLE_SECONDS
        last_post = max(i for i, e in enumerate(events) if e[0] == 'post')
        restore = events.index(('pbcopy', b'old'))
        assert ('sleep', PASTE_SETTLE_SECONDS) in events[last_post:restore]
        assert PASTE_SETTLE_SECONDS >= 0.5


# ---------------------------------------------------------------------------
# Clipboard save / restore
# ---------------------------------------------------------------------------

class TestClipboardRestore:
    def test_text_encoded_utf8_into_clipboard(self):
        popen_mock = _popen()
        runs = iter([_run(stdout=b''), _run()])
        with patch('vtt.text_insert.subprocess.Popen', return_value=popen_mock), \
             patch('vtt.text_insert.subprocess.run', side_effect=runs):
            insert_text("héllo")
        popen_mock.communicate.assert_any_call("héllo".encode('utf-8'), timeout=SUBPROCESS_TIMEOUT)

    def test_original_clipboard_restored_after_paste(self):
        original = b"original content"
        popen_instances = []

        def mock_popen(cmd, **kwargs):
            m = _popen()
            popen_instances.append(m)
            return m

        runs = iter([_run(stdout=original), _run()])  # pbpaste
        with patch('vtt.text_insert.subprocess.Popen', side_effect=mock_popen), \
             patch('vtt.text_insert.subprocess.run', side_effect=runs):
            result = insert_text("hello world")

        assert result is True
        assert len(popen_instances) == 2                                  # text + restore
        popen_instances[0].communicate.assert_called_once_with(b"hello world", timeout=SUBPROCESS_TIMEOUT)
        popen_instances[1].communicate.assert_called_once_with(original, timeout=SUBPROCESS_TIMEOUT)

    def test_empty_clipboard_is_restored(self):
        """A clipboard that was already empty (b'') should still be restored."""
        popen_instances = []

        def mock_popen(cmd, **kwargs):
            m = _popen()
            popen_instances.append(m)
            return m

        runs = iter([_run(stdout=b''), _run()])
        with patch('vtt.text_insert.subprocess.Popen', side_effect=mock_popen), \
             patch('vtt.text_insert.subprocess.run', side_effect=runs):
            insert_text("hello")

        assert len(popen_instances) == 2
        popen_instances[1].communicate.assert_called_once_with(b'', timeout=SUBPROCESS_TIMEOUT)

    def test_no_restore_when_pbpaste_fails(self):
        """If pbpaste exits non-zero, we never attempt a restore."""
        popen_instances = []

        def mock_popen(cmd, **kwargs):
            m = _popen()
            popen_instances.append(m)
            return m

        runs = iter([_run(returncode=1), _run()])  # pbpaste fails, no further runs
        with patch('vtt.text_insert.subprocess.Popen', side_effect=mock_popen), \
             patch('vtt.text_insert.subprocess.run', side_effect=runs):
            insert_text("hello")

        assert len(popen_instances) == 1   # only the text pbcopy, no restore

    def test_no_restore_when_pbpaste_raises(self, capsys):
        """If pbpaste raises an exception, we skip restore and log a warning."""
        popen_instances = []

        def mock_popen(cmd, **kwargs):
            m = _popen()
            popen_instances.append(m)
            return m

        def mock_run(cmd, **kwargs):
            if cmd[0] == 'pbpaste':
                raise OSError("command not found")
            return _run()

        with patch('vtt.text_insert.subprocess.Popen', side_effect=mock_popen), \
             patch('vtt.text_insert.subprocess.run', side_effect=mock_run):
            result = insert_text("hello")

        assert result is True
        assert len(popen_instances) == 1
        assert "Warning" in capsys.readouterr().out

    def test_restore_runs_even_when_paste_fails(self):
        """Clipboard is restored even if the keystroke step fails."""
        original = b"my data"
        popen_instances = []

        def mock_popen(cmd, **kwargs):
            m = _popen()
            popen_instances.append(m)
            return m

        runs = iter([_run(stdout=original)])
        with patch('vtt.text_insert.subprocess.Popen', side_effect=mock_popen), \
             patch('vtt.text_insert.subprocess.run', side_effect=runs), \
             patch('vtt.text_insert.CGEventPost', side_effect=RuntimeError("denied")):
            result = insert_text("hello")

        assert result is False
        assert len(popen_instances) == 2                           # text + restore
        popen_instances[1].communicate.assert_called_once_with(original, timeout=SUBPROCESS_TIMEOUT)

    def test_restore_failure_does_not_raise(self):
        """A broken restore (e.g. disk full) must never propagate an exception."""
        call_count = [0]

        def mock_popen(cmd, **kwargs):
            call_count[0] += 1
            m = MagicMock()
            m.returncode = 0
            if call_count[0] == 2:   # restore call
                m.communicate.side_effect = OSError("disk full")
            else:
                m.communicate.return_value = (b'', b'')
            return m

        runs = iter([_run(stdout=b'old'), _run()])
        with patch('vtt.text_insert.subprocess.Popen', side_effect=mock_popen), \
             patch('vtt.text_insert.subprocess.run', side_effect=runs):
            result = insert_text("hello")   # must not raise

        assert result is True
