"""Windows backend for LiteType.

Implements the contract in base.py using cross-platform Python libraries
(Windows has no built-in equivalent of macOS's NSEvent / pbcopy / NSSound):
  - hotkey listening via pynput's global keyboard listener
  - text insertion via pyperclip for the clipboard and pynput to simulate
    the Ctrl+V keystroke
  - feedback sounds via the stdlib winsound module

There is no Windows equivalent of macOS's "Fn" modifier: on Windows
keyboards, Fn is handled entirely in hardware/firmware and never reaches
the OS as a key event, so it cannot appear in a Windows hotkey.
"""

import threading
import winsound
from typing import Callable

import pyperclip
from pynput import keyboard
from pynput.keyboard import Controller as KeyboardController

from .base import HotkeyHandler as HotkeyHandlerBase


# --- Hotkey listening -----------------------------------------------------

# Maps the modifier names users type in config.json to the set of pynput
# key codes that satisfy them (left/right variants both count). There is no
# "Fn" entry: unlike macOS, Windows keyboards handle Fn in hardware, so it
# never reaches pynput as a key event and can't be used as a hotkey here.
MODIFIER_KEYS = {
    "Ctrl":  {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
    "Alt":   {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr},
    "Shift": {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r},
    "Win":   {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r},
}


def parse_hotkey(hotkey_str: str) -> set:
    """Parse a 'Ctrl+Alt' style string into the set of modifier names required.

    Supported keys: Ctrl, Alt, Shift, Win.
    Raises ValueError for unrecognised or unsupported (e.g. "Fn") key names.
    """
    required = set()
    for part in hotkey_str.split("+"):
        key = part.strip()
        if key not in MODIFIER_KEYS:
            supported = ", ".join(sorted(MODIFIER_KEYS))
            raise ValueError(f"Unknown modifier key: '{key}'. Supported: {supported}")
        required.add(key)
    return required


class WindowsHotkeyHandler(HotkeyHandlerBase):
    """Handles global hotkeys using a pynput keyboard listener."""

    def __init__(self,
                 on_activate: Callable[[], None],
                 on_deactivate: Callable[[], None],
                 required_names: set):
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate
        self._required_names = required_names

        self._pressed = set()
        self._hotkey_active = False
        self._listener = None
        self._running = False

    def _held_modifier_names(self) -> set:
        """Which required modifier names are currently satisfied by held keys."""
        held = set()
        for name in self._required_names:
            if MODIFIER_KEYS[name] & self._pressed:
                held.add(name)
        return held

    def _on_press(self, key):
        self._pressed.add(key)
        should_be_active = self._held_modifier_names() == self._required_names

        if should_be_active and not self._hotkey_active:
            self._hotkey_active = True
            self._on_activate()

    def _on_release(self, key):
        self._pressed.discard(key)
        should_be_active = self._held_modifier_names() == self._required_names

        if not should_be_active and self._hotkey_active:
            self._hotkey_active = False
            self._on_deactivate()

    def start(self) -> None:
        """Start listening for hotkeys."""
        if self._running:
            return

        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        self._running = False

        if self._listener:
            self._listener.stop()
            self._listener = None

    def is_running(self) -> bool:
        """Check if listener is running."""
        return self._running


def create_hotkey_handler(on_activate: Callable[[], None],
                          on_deactivate: Callable[[], None],
                          hotkey: str = "Ctrl+Alt") -> WindowsHotkeyHandler:
    """Create a hotkey handler for the given modifier combination.

    Args:
        on_activate: Called when all required modifiers are held.
        on_deactivate: Called when any required modifiers is released.
        hotkey: '+'-separated modifier names, e.g. 'Ctrl+Alt', 'Ctrl+Shift'.
    """
    required_names = parse_hotkey(hotkey)
    return WindowsHotkeyHandler(
        on_activate=on_activate,
        on_deactivate=on_deactivate,
        required_names=required_names,
    )


# --- Text insertion -------------------------------------------------------

_controller = KeyboardController()


def insert_text(text: str) -> bool:
    """Insert text at the current cursor position.

    Saves and restores the clipboard around the paste operation.

    Returns True if successful, False otherwise.
    """
    if not text:
        return False

    original_clipboard = None
    try:
        original_clipboard = pyperclip.paste()
    except Exception as e:
        print(f"Warning: Could not save clipboard: {e}")

    try:
        pyperclip.copy(text)

        with _controller.pressed(keyboard.Key.ctrl):
            _controller.press('v')
            _controller.release('v')

        return True

    except Exception as e:
        print(f"Error inserting text: {e}")
        return False

    finally:
        if original_clipboard is not None:
            try:
                pyperclip.copy(original_clipboard)
            except Exception as e:
                print(f"Warning: Could not restore clipboard: {e}")


# --- Feedback sounds ------------------------------------------------------

# LiteType asks for sounds by intent ("start"/"stop"); each backend maps
# those to its own sound. winsound.Beep blocks the calling thread, so it
# runs on a daemon thread to match the non-blocking behaviour of NSSound.
SOUND_MAP = {
    "start": 880,
    "stop": 440,
}
_BEEP_DURATION_MS = 120


def play_sound(event: str) -> None:
    """Play a short feedback beep for the given event name."""
    frequency = SOUND_MAP.get(event)
    if not frequency:
        return
    thread = threading.Thread(
        target=winsound.Beep, args=(frequency, _BEEP_DURATION_MS), daemon=True
    )
    thread.start()
