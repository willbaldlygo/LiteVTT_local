"""Tests for config loading in vtt.recorder._load_config."""

import json
import pytest
from unittest.mock import patch, mock_open
from vtt.recorder import LiteRecorder


def bare_recorder():
    """LiteRecorder instance with __init__ skipped."""
    return LiteRecorder.__new__(LiteRecorder)


class TestRecorderLoadConfig:
    def test_returns_parsed_dict_on_valid_json(self):
        data = {"model": {"default_model": "ggml-base.bin", "use_small_en": True}}
        r = bare_recorder()
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(data))):
            result = r._load_config()
        assert result == data

    def test_returns_empty_dict_when_file_missing(self):
        r = bare_recorder()
        with patch('os.path.exists', return_value=False):
            result = r._load_config()
        assert result == {}

    def test_returns_empty_dict_on_invalid_json(self, capsys):
        r = bare_recorder()
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="not valid json {")):
            result = r._load_config()
        assert result == {}
        assert "Warning" in capsys.readouterr().out

    def test_returns_empty_dict_on_read_error(self, capsys):
        r = bare_recorder()
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("disk error")):
            result = r._load_config()
        assert result == {}
        assert "Warning" in capsys.readouterr().out

    def test_nested_config_values_preserved(self):
        data = {
            "hotkeys": {"trigger": "Fn+Ctrl"},
            "storage": {"path": "~/Documents/LiteVTT"},
            "model": {"default_model": "ggml-small.en.bin", "use_small_en": True},
        }
        r = bare_recorder()
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(data))):
            result = r._load_config()
        assert result["model"]["use_small_en"] is True
        assert result["storage"]["path"] == "~/Documents/LiteVTT"
