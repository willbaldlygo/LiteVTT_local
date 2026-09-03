"""Tests for user-global path resolution in litetype.paths."""

import os
import sys
import pytest

from litetype import paths


class TestUnix:
    """XDG-style paths, forced even when CI runs on Windows."""

    @pytest.fixture(autouse=True)
    def force_unix(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")

    def test_config_path_uses_xdg_config_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        expected = os.path.join(str(tmp_path), "litetype", "config.json")
        assert paths.config_path() == expected

    def test_models_dir_uses_xdg_data_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        expected = os.path.join(str(tmp_path), "litetype", "models")
        assert paths.models_dir() == expected

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


class TestWindows:
    """APPDATA / LOCALAPPDATA-style paths, forced even when CI runs on Unix."""

    @pytest.fixture(autouse=True)
    def force_windows(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")

    def test_config_path_uses_appdata(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        expected = os.path.join(str(tmp_path), "litetype", "config.json")
        assert paths.config_path() == expected

    def test_models_dir_uses_localappdata(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        expected = os.path.join(str(tmp_path), "litetype", "models")
        assert paths.models_dir() == expected

    def test_config_dir_defaults_under_home_when_appdata_unset(self, tmp_path, monkeypatch):
        monkeypatch.delenv("APPDATA", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        expected = os.path.join(str(tmp_path), "AppData", "Roaming", "litetype")
        assert paths.config_dir() == expected

    def test_data_dir_defaults_under_home_when_localappdata_unset(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        expected = os.path.join(str(tmp_path), "AppData", "Local", "litetype")
        assert paths.data_dir() == expected
