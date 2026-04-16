"""Tests for LiteRecorder storage path resolution and subdirectory creation."""

import os
import pytest
from vtt.recorder import LiteRecorder


def make_recorder(config):
    """Construct a LiteRecorder with a given config, bypassing __init__ IO."""
    r = LiteRecorder.__new__(LiteRecorder)
    r.sample_rate = 16000
    r.channels = 1
    r._recording = False
    r._audio_buffer = []
    r._stream = None
    r.base_path = None
    r.config = config
    return r


class TestStoragePath:
    def test_default_when_no_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        r = make_recorder({})
        assert r._find_storage_path() == str(tmp_path / "Documents" / "LiteVTT")

    def test_default_when_path_is_empty_string(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        r = make_recorder({"storage": {"path": ""}})
        assert r._find_storage_path() == str(tmp_path / "Documents" / "LiteVTT")

    def test_default_when_path_is_whitespace(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        r = make_recorder({"storage": {"path": "   "}})
        assert r._find_storage_path() == str(tmp_path / "Documents" / "LiteVTT")

    def test_custom_absolute_path(self, tmp_path):
        custom = str(tmp_path / "custom_storage")
        r = make_recorder({"storage": {"path": custom}})
        assert r._find_storage_path() == custom

    def test_tilde_expanded_in_custom_path(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        r = make_recorder({"storage": {"path": "~/my_vtt"}})
        assert r._find_storage_path() == str(tmp_path / "my_vtt")

    def test_storage_directory_is_created(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        r = make_recorder({})
        path = r._find_storage_path()
        assert os.path.isdir(path)

    def test_custom_directory_is_created(self, tmp_path):
        custom = str(tmp_path / "brand_new_dir")
        assert not os.path.exists(custom)
        r = make_recorder({"storage": {"path": custom}})
        r._find_storage_path()
        assert os.path.isdir(custom)


class TestSubdirectories:
    def test_recordings_dir_created_on_save(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        r = make_recorder({})
        r.base_path = r._find_storage_path()
        # sf.write is a MagicMock (mocked in conftest), so any audio_data works
        r.save([0.0] * 100, "test.wav")
        assert os.path.isdir(os.path.join(r.base_path, "Recordings"))

    def test_transcripts_dir_created_on_save_transcript(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        r = make_recorder({})
        r.base_path = r._find_storage_path()
        r.save_transcript("hello world", "test.wav")
        assert os.path.isdir(os.path.join(r.base_path, "Transcripts"))

    def test_transcript_content_is_written(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        r = make_recorder({})
        r.base_path = r._find_storage_path()
        r.save_transcript("hello world", "recording_2026.wav")
        txt = os.path.join(r.base_path, "Transcripts", "recording_2026.txt")
        assert open(txt).read() == "hello world"

    def test_transcript_filename_uses_audio_stem(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        r = make_recorder({})
        r.base_path = r._find_storage_path()
        r.save_transcript("text", "session_2026-04-16.mp3")
        txt = os.path.join(r.base_path, "Transcripts", "session_2026-04-16.txt")
        assert os.path.exists(txt)
