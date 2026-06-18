"""Tests for config loading in vtt.config.load_config."""

import json
import pytest
from unittest.mock import patch, mock_open
from vtt.config import load_config


class TestLoadConfig:
    def test_returns_parsed_dict_on_valid_json(self):
        data = {"model": {"default_model": "ggml-base.bin", "use_small_en": True}}
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(data))):
            result = load_config()
        assert result == data

    def test_returns_empty_dict_when_file_missing(self):
        with patch('os.path.exists', return_value=False):
            result = load_config()
        assert result == {}

    def test_returns_empty_dict_on_invalid_json(self, capsys):
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="not valid json {")):
            result = load_config()
        assert result == {}
        assert "Warning" in capsys.readouterr().out

    def test_returns_empty_dict_on_read_error(self, capsys):
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("disk error")):
            result = load_config()
        assert result == {}
        assert "Warning" in capsys.readouterr().out

    def test_nested_config_values_preserved(self):
        data = {
            "hotkey": "Fn+Ctrl",
            "model": {"default_model": "ggml-small.en.bin", "use_small_en": True},
        }
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(data))):
            result = load_config()
        assert result["model"]["use_small_en"] is True
        assert result["hotkey"] == "Fn+Ctrl"
