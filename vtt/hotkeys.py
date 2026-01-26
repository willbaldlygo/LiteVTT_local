"""Hotkey handler module for VTT Local.

Uses native macOS NSEvent global monitoring.
Refactored to trigger on Fn+Ctrl modifier combination.
"""

from typing import Callable
from AppKit import NSEvent, NSFlagsChangedMask
from Quartz import kCGEventFlagMaskControl, kCGEventFlagMaskSecondaryFn


class HotkeyHandler:
    """Handles global hotkeys using macOS NSEvent."""
    
    def __init__(self,
                 on_activate: Callable[[], None],
                 on_deactivate: Callable[[], None]):
        """Initialize the hotkey handler for Fn+Ctrl.
        
        Args:
            on_activate: Called when Fn+Ctrl are pressed
            on_deactivate: Called when either is released
        """
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate
        
        self._hotkey_active = False
        self._flags_monitor = None
        self._running = False
    
    def _handle_flags_changed(self, event):
        """Handle modifier key changes."""
        flags = event.modifierFlags()
        
        # Check if BOTH Control and Fn are pressed
        ctrl_pressed = bool(flags & kCGEventFlagMaskControl)
        fn_pressed = bool(flags & kCGEventFlagMaskSecondaryFn)
        
        should_be_active = ctrl_pressed and fn_pressed
        
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
        
        # Monitor modifier key changes
        self._flags_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSFlagsChangedMask,
            self._handle_flags_changed
        )
        
        print("Hotkey listener started (Fn+Ctrl)")
    
    def stop(self) -> None:
        """Stop listening for hotkeys."""
        self._running = False
            
        if self._flags_monitor:
            NSEvent.removeMonitor_(self._flags_monitor)
            self._flags_monitor = None
    
    def is_running(self) -> bool:
        """Check if listener is running."""
        return self._running


def create_option_s_handler(on_activate: Callable[[], None],
                            on_deactivate: Callable[[], None]) -> HotkeyHandler:
    """Create the Fn+Ctrl handler.
    
    Kept name for compatibility but updated logic.
    """
    return HotkeyHandler(
        on_activate=on_activate,
        on_deactivate=on_deactivate
    )
