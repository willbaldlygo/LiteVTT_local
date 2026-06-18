"""Configuration loading for LiteType.

Config lives at ~/.config/litetype/config.json (see paths.py). On first run
the file is created with sensible defaults so users never have to author it
by hand.
"""

import os
import json

from .paths import config_path

DEFAULT_CONFIG = {
    "hotkey": "Fn+Ctrl",
    "model": {
        "default_model": "ggml-base.bin",
        "use_small_en": False,
    },
}


def load_config() -> dict:
    """Load configuration, creating a default file on first run.

    Returns the parsed config. If the file is missing it is created with
    DEFAULT_CONFIG and those defaults are returned. If it exists but cannot
    be read or parsed, an empty dict is returned (callers fall back to their
    own defaults).
    """
    path = config_path()

    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
            return {}

    # First run: write defaults so the user has something to edit.
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print(f"Created default config at {path}")
    except Exception as e:
        print(f"Warning: Failed to write default config: {e}")

    # Return a copy so callers can't mutate the module-level default.
    return json.loads(json.dumps(DEFAULT_CONFIG))
