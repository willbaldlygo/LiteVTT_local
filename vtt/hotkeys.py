"""Hotkey handler module for VTT Local.

Uses native macOS NSEvent global monitoring.
Triggers on a configurable modifier-key combination (default: Fn+Ctrl).
"""

from typing import Callable
from AppKit import NSEvent, NSFlagsChangedMask
from Quartz import (
    kCGEventFlagMaskControl,
    kCGEventFlagMaskSecondaryFn,
    kCGEventFlagMaskShift,
    kCGEventFlagMaskAlternate,
    kCGEventFlagMaskCommand,
)

FLAG_MAP = {
    "Fn":    kCGEventFlagMaskSecondaryFn,
    "Ctrl":  kCGEventFlagMaskControl,
    "Shift": kCGEventFlagMaskShift,
    "Opt":   kCGEventFlagMaskAlternate,
    "Alt":   kCGEventFlagMaskAlternate,
    "Cmd":   kCGEventFlagMaskCommand,
}


def parse_hotkey(hotkey_str: str) -> int:
    """Parse a 'Fn+Ctrl' style string into a combined Quartz modifier flag mask.

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


class HotkeyHandler:
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
                          hotkey: str = "Fn+Ctrl") -> HotkeyHandler:
    """Create a hotkey handler for the given modifier combination.

    Args:
        on_activate: Called when all required modifiers are held.
        on_deactivate: Called when any required modifier is released.
        hotkey: '+'-separated modifier names, e.g. 'Fn+Ctrl', 'Ctrl+Shift'.
    """
    required_flags = parse_hotkey(hotkey)
    return HotkeyHandler(
        on_activate=on_activate,
        on_deactivate=on_deactivate,
        required_flags=required_flags,
    )
