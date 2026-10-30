"""Start-at-login support for LiteType.

Installs a per-user LaunchAgent that starts LiteType in the background
when you log in, with no Terminal window. Takes effect at next login.
"""

import os
import plistlib

LABEL = "info.baldlygo.litetype"
PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{LABEL}.plist")
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_plist(python_path: str, project_dir: str) -> dict:
    """Return the LaunchAgent definition for running LiteType."""
    return {
        "Label": LABEL,
        "ProgramArguments": [python_path, os.path.join(project_dir, "litetype.py")],
        "WorkingDirectory": project_dir,
        "RunAtLoad": True,
        # Quit from the menu should stay quit
        "KeepAlive": False,
        "ProcessType": "Interactive",
        "LimitLoadToSessionType": "Aqua",
        # The app already writes a timestamped ~/Library/Logs/LiteType.log
        "StandardOutPath": "/dev/null",
        "StandardErrorPath": "/dev/null",
    }


def is_enabled() -> bool:
    return os.path.exists(PLIST_PATH)


def enable() -> bool:
    """Write the LaunchAgent plist. Returns True on success."""
    python_path = os.path.join(PROJECT_DIR, "venv", "bin", "python")
    try:
        os.makedirs(os.path.dirname(PLIST_PATH), exist_ok=True)
        with open(PLIST_PATH, "wb") as f:
            plistlib.dump(build_plist(python_path, PROJECT_DIR), f)
        return True
    except OSError as e:
        print(f"Warning: Could not enable start at login: {e}")
        return False


def disable() -> bool:
    """Remove the LaunchAgent plist. Returns True on success."""
    try:
        if os.path.exists(PLIST_PATH):
            os.remove(PLIST_PATH)
        return True
    except OSError as e:
        print(f"Warning: Could not disable start at login: {e}")
        return False
