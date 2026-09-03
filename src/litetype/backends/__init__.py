"""Select the platform backend for the current operating system.

The three names exported here — create_hotkey_handler, insert_text and
play_sound — always come from exactly one backend module, chosen by
sys.platform. See base.py for the contract each backend implements.
"""

import sys

if sys.platform == "darwin":
    from .macos import create_hotkey_handler, insert_text, play_sound
elif sys.platform == "win32":
    from .windows import create_hotkey_handler, insert_text, play_sound
else:
    # Other platforms (e.g. the Linux test runner) have no GUI backend.
    # The shared, OS-independent parts of LiteType still import and run.
    pass
