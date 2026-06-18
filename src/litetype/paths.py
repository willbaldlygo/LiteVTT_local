"""User-global filesystem locations for LiteType.

Models and configuration live in standard per-user directories rather than
next to the installed package, so LiteType works when installed via pip.

Locations follow the XDG Base Directory convention and honour the
XDG_DATA_HOME / XDG_CONFIG_HOME environment variables when set:

    config:  ~/.config/litetype/config.json
    models:  ~/.local/share/litetype/models/
"""

import os

APP_NAME = "litetype"


def _app_dir(env_var: str, *default_parts: str) -> str:
    """Return APP_NAME under an XDG base dir, honouring an override env var."""
    base = os.environ.get(env_var)
    if base:
        return os.path.join(base, APP_NAME)
    return os.path.join(os.path.expanduser("~"), *default_parts, APP_NAME)


def config_dir() -> str:
    """Directory holding config.json."""
    return _app_dir("XDG_CONFIG_HOME", ".config")


def data_dir() -> str:
    """Directory holding application data (e.g. models)."""
    return _app_dir("XDG_DATA_HOME", ".local", "share")


def config_path() -> str:
    """Full path to config.json."""
    return os.path.join(config_dir(), "config.json")


def models_dir() -> str:
    """Directory holding downloaded Whisper model files."""
    return os.path.join(data_dir(), "models")
