"""Tests for config loading in litetype.config.load_config.

Config resolution is driven through paths.config_path(), which honours
XDG_CONFIG_HOME — so each test points that at a tmp dir and exercises the
real file behaviour rather than mocking open().
"""

import os
import json
import pytest

from litetype.config import load_config, DEFAULT_CONFIG
from litetype.paths import config_path


@pytest.fixture(autouse=True)
def tmp_config_home(tmp_path, monkeypatch):
    """Redirect config to a throwaway dir for every test."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return tmp_path


class TestLoadConfig:
    def test_creates_default_file_on_first_run(self):
        path = config_path()
        assert not os.path.exists(path)

        result = load_config()

        assert result == DEFAULT_CONFIG
        assert os.path.exists(path)
        with open(path) as f:
            assert json.load(f) == DEFAULT_CONFIG

    def test_returns_existing_config_when_present(self):
        path = config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        custom = {"hotkey": "Ctrl+Shift", "model": {"use_small_en": True}}
        with open(path, "w") as f:
            json.dump(custom, f)

        result = load_config()

        assert result == custom

    def test_returns_empty_dict_on_invalid_json(self, capsys):
        path = config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("not valid json {")

        result = load_config()

        assert result == {}
        assert "Warning" in capsys.readouterr().out

    def test_returns_empty_dict_on_read_error(self, capsys):
        # A directory where the config file should be makes open() fail.
        path = config_path()
        os.makedirs(path, exist_ok=True)

        result = load_config()

        assert result == {}
        assert "Warning" in capsys.readouterr().out

    def test_returned_default_is_a_fresh_copy(self):
        result = load_config()
        result["hotkey"] = "MUTATED"
        result["model"]["use_small_en"] = True

        # Module-level default must be untouched.
        assert DEFAULT_CONFIG["hotkey"] == "Fn+Ctrl"
        assert DEFAULT_CONFIG["model"]["use_small_en"] is False

    def test_default_config_has_expected_shape(self):
        assert DEFAULT_CONFIG["hotkey"] == "Fn+Ctrl"
        assert DEFAULT_CONFIG["model"]["default_model"] == "ggml-base.bin"
        assert DEFAULT_CONFIG["model"]["use_small_en"] is False
