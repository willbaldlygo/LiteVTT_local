"""The contract every platform backend must fulfil.

LiteType's shared code (audio capture, transcription, config, models) is the
same on every operating system. Only a few things genuinely differ per OS:
listening for the hotkey, pasting text into the focused app, and playing a
feedback sound.

Those OS-specific bits live in one module per platform — macos.py, and later
windows.py — and `backends/__init__.py` picks the right one at runtime. The
rest of LiteType imports from `litetype.backends` and never needs to know
which operating system it is running on.

Every backend module must provide:

    create_hotkey_handler(on_activate, on_deactivate, hotkey) -> HotkeyHandler
        Build a handler that calls on_activate() when `hotkey` (e.g.
        "Fn+Ctrl") is held down and on_deactivate() when it is released.

    insert_text(text: str) -> bool
        Paste `text` at the current cursor position in whatever app has
        focus, restoring the user's clipboard afterwards. Returns True on
        success, False otherwise.

    play_sound(event: str) -> None
        Play a short feedback sound. `event` is a platform-neutral name —
        currently "start" (recording began) or "stop" (recording ended).
        Each backend maps these to its own system sounds.
"""

from abc import ABC, abstractmethod


class HotkeyHandler(ABC):
    """Listens for a global hotkey and fires callbacks on press / release."""

    @abstractmethod
    def start(self) -> None:
        """Begin listening for the hotkey."""

    @abstractmethod
    def stop(self) -> None:
        """Stop listening and release any operating-system resources."""
