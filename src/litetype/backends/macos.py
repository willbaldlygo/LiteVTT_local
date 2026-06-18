"""macOS backend for LiteType.

Implements the contract in base.py using native macOS frameworks:
  - hotkey listening via NSEvent / Quartz
  - text insertion via the pbcopy/pbpaste clipboard tools and an AppleScript
    Cmd+V keystroke
  - feedback sounds via NSSound
"""

import os
import time
import subprocess
from typing import Callable

from AppKit import NSEvent, NSFlagsChangedMask, NSSound
from Quartz import (
    kCGEventFlagMaskControl,
    kCGEventFlagMaskSecondaryFn,
    kCGEventFlagMaskShift,
    kCGEventFlagMaskAlternate,
    kCGEventFlagMaskCommand,
)

from .base import HotkeyHandler as HotkeyHandlerBase


# --- Hotkey listening -----------------------------------------------------

# Maps the modifier names users type in config.json to macOS flag values.
# Each operating system exposes a different set of usable modifiers — note
# macOS has "Fn" and "Cmd", which Windows keyboards do not surface the same
# way — so this map is genuinely platform-specific.
FLAG_MAP = {
    "Fn":    kCGEventFlagMaskSecondaryFn,
    "Ctrl":  kCGEventFlagMaskControl,
    "Shift": kCGEventFlagMaskShift,
    "Opt":   kCGEventFlagMaskAlternate,
    "Alt":   kCGEventFlagMaskAlternate,
    "Cmd":   kCGEventFlagMaskCommand,
}


def parse_hotkey(hotkey_str: str) -> int:
    """Parse a 'Fn+Ctrl' style string into a combined macOS modifier mask.

    Supported keys: Fn, Ctrl, Shift, Opt, Alt, Cmd.
    Raises ValueError for unrecognised key names.
    """
    mask = 0
    for part in hotkey_str.split("+"):
        key = part.strip()
        if key not in FLAG_MAP:
            supported = ", ".join(sorted(set(FLAG_MAP)))
            raise ValueError(f"Unknown modifier key: '{key}'. Supported: {supported}")
        mask |= FLAG_MAP[key]
    return mask


class MacHotkeyHandler(HotkeyHandlerBase):
    """Handles global hotkeys using macOS NSEvent."""

    def __init__(self,
                 on_activate: Callable[[], None],
                 on_deactivate: Callable[[], None],
                 required_flags: int):
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate
        self._required_flags = required_flags

        self._hotkey_active = False
        self._flags_monitor = None
        self._running = False

    def _handle_flags_changed(self, event):
        """Handle modifier key changes."""
        flags = event.modifierFlags()
        should_be_active = (flags & self._required_flags) == self._required_flags

        if should_be_active and not self._hotkey_active:
            self._hotkey_active = True
            self._on_activate()

        elif not should_be_active and self._hotkey_active:
            self._hotkey_active = False
            self._on_deactivate()

        return event

    def start(self) -> None:
        """Start listening for hotkeys."""
        if self._running:
            return

        self._running = True
        self._flags_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSFlagsChangedMask,
            self._handle_flags_changed
        )

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        self._running = False

        if self._flags_monitor:
            NSEvent.removeMonitor_(self._flags_monitor)
            self._flags_monitor = None

    def is_running(self) -> bool:
        """Check if listener is running."""
        return self._running


def create_hotkey_handler(on_activate: Callable[[], None],
                          on_deactivate: Callable[[], None],
                          hotkey: str = "Fn+Ctrl") -> MacHotkeyHandler:
    """Create a hotkey handler for the given modifier combination.

    Args:
        on_activate: Called when all required modifiers are held.
        on_deactivate: Called when any required modifier is released.
        hotkey: '+'-separated modifier names, e.g. 'Fn+Ctrl', 'Ctrl+Shift'.
    """
    required_flags = parse_hotkey(hotkey)
    return MacHotkeyHandler(
        on_activate=on_activate,
        on_deactivate=on_deactivate,
        required_flags=required_flags,
    )


# --- Text insertion -------------------------------------------------------

def insert_text(text: str) -> bool:
    """Insert text at the current cursor position.

    Saves and restores the clipboard around the paste operation.

    Returns True if successful, False otherwise.
    """
    if not text:
        return False

    # Save existing clipboard contents before overwriting
    original_clipboard = None
    try:
        result = subprocess.run(
            ['pbpaste'],
            capture_output=True,
            timeout=2
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
        process.communicate(text.encode('utf-8'))

        if process.returncode != 0:
            print("Failed to copy to clipboard")
            return False

        # Small delay to ensure clipboard is updated and app is ready
        time.sleep(0.2)

        # Paste using AppleScript and System Events
        script = '''
        tell application "System Events"
            keystroke "v" using command down
        end tell
        '''

        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Failed to paste: {result.stderr}")
            return False

        # Small delay to let the paste complete before restoring
        time.sleep(0.1)

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
                restore.communicate(original_clipboard)
            except Exception as e:
                print(f"Warning: Could not restore clipboard: {e}")


# --- Feedback sounds ------------------------------------------------------

# LiteType asks for sounds by intent ("start"/"stop"); each backend maps
# those to its own named system sounds.
SOUND_MAP = {
    "start": "Tink",
    "stop": "Pop",
}


def play_sound(event: str) -> None:
    """Play a short macOS system sound for the given event name."""
    name = SOUND_MAP.get(event)
    if not name:
        return
    sound = NSSound.soundNamed_(name)
    if sound:
        sound.play()
