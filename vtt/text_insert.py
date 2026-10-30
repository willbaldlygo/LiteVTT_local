"""Text insertion module for VTT Local.

Inserts transcribed text at the current cursor position
in any application using clipboard and paste.
"""

import os
import subprocess
import time

from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    CGEventSetFlags,
    CGEventSourceCreate,
    kCGEventFlagMaskCommand,
    kCGEventSourceStatePrivate,
    kCGHIDEventTap,
)

# Virtual keycode for the "V" key (ANSI layout).
KEYCODE_V = 9

# How long to leave our text on the clipboard after sending Cmd+V before
# putting the user's original clipboard back. The target app reads the
# pasteboard whenever it gets round to handling the keystroke, not when we
# send it -- busy apps (browsers, Electron apps) can take well over 100ms,
# and if we restore first they paste the *old* clipboard instead.
PASTE_SETTLE_SECONDS = 0.6

# Guard against pbcopy/pbpaste ever hanging and wedging the app.
SUBPROCESS_TIMEOUT = 2


def _send_cmd_v() -> None:
    """Post a Cmd+V keystroke directly via Quartz.

    Uses a private event source and sets the flags explicitly, so modifier
    keys the user is still physically holding (e.g. Fn or Ctrl from the
    record hotkey) are not merged into the paste shortcut.
    """
    source = CGEventSourceCreate(kCGEventSourceStatePrivate)
    key_down = CGEventCreateKeyboardEvent(source, KEYCODE_V, True)
    key_up = CGEventCreateKeyboardEvent(source, KEYCODE_V, False)
    if key_down is None or key_up is None:
        raise RuntimeError("Could not create keyboard events")
    CGEventSetFlags(key_down, kCGEventFlagMaskCommand)
    CGEventSetFlags(key_up, kCGEventFlagMaskCommand)
    CGEventPost(kCGHIDEventTap, key_down)
    CGEventPost(kCGHIDEventTap, key_up)


def insert_text(text: str) -> bool:
    """Insert text at the current cursor position.

    Saves and restores the clipboard around the paste operation.

    Args:
        text: The text to insert

    Returns:
        True if successful, False otherwise
    """
    if not text:
        return False

    # Save existing clipboard contents before overwriting
    original_clipboard = None
    try:
        result = subprocess.run(
            ['pbpaste'],
            capture_output=True,
            timeout=SUBPROCESS_TIMEOUT
        )
        if result.returncode == 0:
            original_clipboard = result.stdout
    except Exception as e:
        print(f"Warning: Could not save clipboard: {e}")

    try:
        # Copy text to clipboard using pbcopy
        process = subprocess.Popen(
            ['pbcopy'],
            stdin=subprocess.PIPE,
            env={**os.environ, 'LANG': 'en_US.UTF-8'}
        )
        process.communicate(text.encode('utf-8'), timeout=SUBPROCESS_TIMEOUT)

        if process.returncode != 0:
            print("Failed to copy to clipboard")
            return False

        # Small delay to ensure clipboard is updated and app is ready
        time.sleep(0.2)

        _send_cmd_v()

        # Let the target app actually read the clipboard before restoring
        time.sleep(PASTE_SETTLE_SECONDS)

        return True

    except Exception as e:
        print(f"Error inserting text: {e}")
        return False

    finally:
        # Restore the original clipboard contents
        if original_clipboard is not None:
            try:
                restore = subprocess.Popen(
                    ['pbcopy'],
                    stdin=subprocess.PIPE
                )
                restore.communicate(original_clipboard, timeout=SUBPROCESS_TIMEOUT)
            except Exception as e:
                print(f"Warning: Could not restore clipboard: {e}")
