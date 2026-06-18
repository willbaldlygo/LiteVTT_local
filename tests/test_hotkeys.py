"""Tests for hotkey string parsing in litetype.hotkeys.parse_hotkey.

Quartz is mocked in conftest, so the combined flag value itself is opaque;
these tests cover the parsing/validation logic, which is what matters.
"""

import pytest

from litetype.hotkeys import parse_hotkey


class TestParseHotkey:
    def test_known_combination_does_not_raise(self):
        parse_hotkey("Fn+Ctrl")

    def test_whitespace_around_keys_is_tolerated(self):
        parse_hotkey(" Fn + Ctrl ")

    def test_all_supported_keys_accepted(self):
        for combo in ["Fn", "Ctrl", "Shift", "Opt", "Alt", "Cmd", "Ctrl+Shift+Opt"]:
            parse_hotkey(combo)

    def test_unknown_key_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_hotkey("Fn+Banana")

    def test_error_message_lists_supported_keys(self):
        with pytest.raises(ValueError) as exc:
            parse_hotkey("Z")
        msg = str(exc.value)
        assert "Ctrl" in msg and "Shift" in msg
