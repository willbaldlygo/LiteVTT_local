"""
Pytest configuration: mock hardware and macOS-only dependencies so the
pure-logic unit tests can run anywhere (including Linux CI).
"""

import sys
import os
from unittest.mock import MagicMock

# Ensure the project root is importable (litescribe, vtt.*)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock every module that requires macOS frameworks or physical hardware.
# Use setdefault so a real install isn't clobbered if somehow present.
for _mod in [
    'numpy',
    'sounddevice',
    'soundfile',
    'rumps',
    'AppKit',
    'Quartz',
    'pywhispercpp',
    'pywhispercpp.model',
]:
    sys.modules.setdefault(_mod, MagicMock())
