"""Shared config loading for LiteType."""

import os
import json


def load_config() -> dict:
    """Load configuration from config.json in the project root."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
    return {}
