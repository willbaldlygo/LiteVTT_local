"""Tests for user-global path resolution in litetype.paths."""

import os
import pytest

from litetype import paths


class TestXdgOverrides:
    def test_config_path_uses_xdg_config_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        expected = os.path.join(str(tmp_path), "litetype", "config.json")
        assert paths.config_path() == expected

    def test_models_dir_uses_xdg_data_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        expected = os.path.join(str(tmp_path), "litetype", "models")
        assert paths.models_dir() == expected


class TestDefaults:
    def test_config_dir_defaults_under_home(self, tmp_path, monkeypatch):
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        expected = os.path.join(str(tmp_path), ".config", "litetype")
        assert paths.config_dir() == expected

    def test_data_dir_defaults_under_home(self, tmp_path, monkeypatch):
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        expected = os.path.join(str(tmp_path), ".local", "share", "litetype")
        assert paths.data_dir() == expected
