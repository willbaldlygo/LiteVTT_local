"""
Pytest configuration: mock hardware and macOS-only dependencies so the
pure-logic unit tests can run anywhere (including Linux CI).
"""

import sys
import os
from unittest.mock import MagicMock

# Ensure the src/ layout is importable (litetype.*) without an install.
# Mirrors the pythonpath setting in pyproject.toml so tests run either way.
_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, _SRC)

# Mock every module that requires macOS frameworks or physical hardware.
# Use setdefault so a real install isn't clobbered if somehow present.
for _mod in [
    'numpy',
    'sounddevice',
    'rumps',
    'AppKit',
    'Quartz',
    'pywhispercpp',
    'pywhispercpp.model',
    'pynput',
    'pynput.keyboard',
    'pyperclip',
]:
    sys.modules.setdefault(_mod, MagicMock())
