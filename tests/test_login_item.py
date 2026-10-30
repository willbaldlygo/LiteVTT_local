"""Tests for the start-at-login LaunchAgent."""

import plistlib
import pytest
import vtt.login_item as li


class TestBuildPlist:
    def test_runs_litetype_with_project_python(self):
        plist = li.build_plist("/proj/venv/bin/python", "/proj")
        assert plist["Label"] == li.LABEL
        assert plist["ProgramArguments"] == ["/proj/venv/bin/python", "/proj/litetype.py"]
        assert plist["WorkingDirectory"] == "/proj"

    def test_starts_at_login_but_quit_stays_quit(self):
        plist = li.build_plist("/p", "/proj")
        assert plist["RunAtLoad"] is True
        assert plist["KeepAlive"] is False

    def test_output_not_duplicated_into_launchd_logs(self):
        plist = li.build_plist("/p", "/proj")
        assert plist["StandardOutPath"] == "/dev/null"
        assert plist["StandardErrorPath"] == "/dev/null"


class TestEnableDisable:
    @pytest.fixture(autouse=True)
    def temp_plist(self, tmp_path, monkeypatch):
        path = tmp_path / "LaunchAgents" / f"{li.LABEL}.plist"
        monkeypatch.setattr(li, "PLIST_PATH", str(path))
        return path

    def test_enable_writes_valid_plist(self, temp_plist):
        assert li.is_enabled() is False
        assert li.enable() is True
        assert li.is_enabled() is True
        with open(temp_plist, "rb") as f:
            assert plistlib.load(f)["Label"] == li.LABEL

    def test_disable_removes_plist(self):
        li.enable()
        assert li.disable() is True
        assert li.is_enabled() is False

    def test_disable_when_not_enabled_is_ok(self):
        assert li.disable() is True
