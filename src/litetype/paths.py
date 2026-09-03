"""User-global filesystem locations for LiteType.

Models and configuration live in standard per-user directories rather than
next to the installed package, so LiteType works when installed via pip.

On macOS and Linux this follows the XDG Base Directory convention, honouring
the XDG_DATA_HOME / XDG_CONFIG_HOME environment variables when set:

    config:  ~/.config/litetype/config.json
    models:  ~/.local/share/litetype/models/

On Windows there is no XDG convention — the platform equivalents are the
roaming and local app-data folders Windows already exposes via the APPDATA /
LOCALAPPDATA environment variables (roaming for small settings that follow a
user between machines, local for large per-machine files like models):

    config:  %APPDATA%\\litetype\\config.json
    models:  %LOCALAPPDATA%\\litetype\\models\\
"""

import os
import sys

APP_NAME = "litetype"


def _is_windows() -> bool:
    return sys.platform == "win32"


def _app_dir(env_var: str, *default_parts: str) -> str:
    """Return APP_NAME under an XDG base dir, honouring an override env var."""
    base = os.environ.get(env_var)
    if base:
        return os.path.join(base, APP_NAME)
    return os.path.join(os.path.expanduser("~"), *default_parts, APP_NAME)


def _windows_app_dir(env_var: str, *default_parts: str) -> str:
    """Return APP_NAME under a Windows app-data folder, honouring its env var."""
    base = os.environ.get(env_var)
    if base:
        return os.path.join(base, APP_NAME)
    return os.path.join(os.path.expanduser("~"), *default_parts, APP_NAME)


def config_dir() -> str:
    """Directory holding config.json."""
    if _is_windows():
        return _windows_app_dir("APPDATA", "AppData", "Roaming")
    return _app_dir("XDG_CONFIG_HOME", ".config")


def data_dir() -> str:
    """Directory holding application data (e.g. models)."""
    if _is_windows():
        return _windows_app_dir("LOCALAPPDATA", "AppData", "Local")
    return _app_dir("XDG_DATA_HOME", ".local", "share")


def config_path() -> str:
    """Full path to config.json."""
    return os.path.join(config_dir(), "config.json")


def models_dir() -> str:
    """Directory holding downloaded Whisper model files."""
    return os.path.join(data_dir(), "models")
