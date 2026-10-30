"""Shared config loading for LiteType."""

import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


def load_config() -> dict:
    """Load configuration from config.json in the project root."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
    return {}


def save_config(config: dict) -> bool:
    """Write configuration back to config.json. Returns True on success."""
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
            f.write("\n")
        return True
    except Exception as e:
        print(f"Warning: Failed to save config: {e}")
        return False
