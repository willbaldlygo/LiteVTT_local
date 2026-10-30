"""Main application controller for VTT Local.

Menu bar app that coordinates audio recording, transcription,
and text insertion using a global hotkey.
"""

import collections
import os
import numpy as np
import rumps
import sys
import threading
import time

from .audio import AudioRecorder
from . import login_item
from .config import load_config, save_config
from .models import get_model_path, list_models, models_dir
from .transcriber import Transcriber
from .hotkeys import create_hotkey_handler
from .text_insert import insert_text
from AppKit import NSSound
from ApplicationServices import AXIsProcessTrusted
from PyObjCTools import AppHelper

LOG_PATH = os.path.expanduser("~/Library/Logs/LiteType.log")

# Clips quieter than this (RMS) are treated as silence and not transcribed;
# otherwise Whisper tends to invent text like "Thank you." Kept low because
# Bluetooth headset mics are quiet: a spoken "Hello." measured 0.0038.
# Near-silence that gets past this is still caught by clean_transcript().
SILENCE_RMS = 0.001

# Recent transcriptions are kept in memory only, never written to disk.
HISTORY_SIZE = 5
MENU_TEXT_LEN = 40


class VTTApp(rumps.App):
    """Menu bar application for voice-to-text dictation."""

    def __init__(self):
        super().__init__(
            name="LiteType",
            title="VTT",
            quit_button=None
        )

        # Components
        self._audio_recorder = AudioRecorder()
        self._transcriber: Transcriber | None = None
        self._model_name: str | None = None
        self._hotkey_handler = None
        self.config = load_config()
        self._vocabulary = self.config.get("vocabulary", [])
        self._audio_recorder.preferred_mics = self.config.get("microphone", [])
        self._history: collections.deque[str] = collections.deque(maxlen=HISTORY_SIZE)

        # State
        self._is_recording = False
        self._is_processing = False
        self._init_done = False

        # Trigger help text
        self._trigger = self.config.get("hotkey", "Fn+Ctrl")

        # Build menu
        self._status_item = rumps.MenuItem("Status: Starting...")
        self._recent_menu = rumps.MenuItem("Recent")
        self._model_menu = rumps.MenuItem("Model")
        for name in list_models():
            self._model_menu.add(rumps.MenuItem(
                name, callback=lambda _, n=name: self._select_model(n)))
        self._mic_menu = rumps.MenuItem("Microphone")
        self._login_menu_item = rumps.MenuItem(
            "Start at Login", callback=self._toggle_login)
        self._login_menu_item.state = login_item.is_enabled()

        self.menu = [
            self._status_item,
            None,
            rumps.MenuItem("Paste Last Transcription", callback=self._paste_last),
            self._recent_menu,
            self._model_menu,
            self._mic_menu,
            None,
            rumps.MenuItem(f"Hotkey: {self._trigger} (hold to record)"),
            self._login_menu_item,
            None,
            rumps.MenuItem("Quit", callback=self._quit)
        ]
        self._populate_recent()
        self._populate_mics()

    @rumps.timer(1)
    def _init_timer(self, _):
        """Initialize everything on first timer tick."""
        if self._init_done:
            return
        self._init_done = True

        self._load_model()
        self._setup_hotkeys()
        self._check_accessibility()

    def _load_model(self):
        """Load the Whisper model."""
        try:
            self._update_status("Loading model...")

            model_path, model_name = get_model_path(self.config)

            if not model_path:
                self._update_status("Model not found!")
                return

            self._update_status(f"Loaded: {model_name}")
            self._transcriber = Transcriber(model_path, self._vocabulary)
            self._model_name = model_name
            self._refresh_model_checks()
            self.title = "🎙️"

        except Exception as e:
            self._update_status(f"Error: {str(e)[:30]}")

    def _setup_hotkeys(self):
        """Initialize hotkeys."""
        try:
            self._hotkey_handler = create_hotkey_handler(
                on_activate=self._on_hotkey_press,
                on_deactivate=self._on_hotkey_release,
                hotkey=self._trigger,
            )
            self._hotkey_handler.start()
            self._update_status(f"Ready - Hold {self._trigger}")
        except Exception as e:
            self._update_status(f"Hotkey error")

    def _check_accessibility(self):
        """Pasting needs Accessibility permission. Without it the Cmd+V is
        silently dropped, so say so up front instead."""
        try:
            trusted = AXIsProcessTrusted()
        except Exception as e:
            print(f"Warning: Could not check Accessibility permission: {e}")
            return
        print(f">>> Accessibility trusted: {bool(trusted)}")
        if not trusted:
            self._update_status("Needs Accessibility permission")
            rumps.notification(
                "LiteType",
                "Accessibility permission needed",
                "Add Terminal (or Python, if started at login) in System Settings > "
                "Privacy & Security > Accessibility so LiteType can paste."
            )

    def _play_sound(self, sound_name: str):
        """Play a system sound."""
        sound = NSSound.soundNamed_(sound_name)
        if sound:
            sound.play()

    def _on_hotkey_press(self):
        """Called when Fn+Ctrl is pressed."""
        print(">>> Recording started")
        if self._is_processing or self._transcriber is None:
            print(">>> Cannot record: processing or no model")
            return

        self._is_recording = True
        self._set_title("🔴 REC")
        self._play_sound("Tink")
        self._update_status("Recording...")

        try:
            self._audio_recorder.start_recording()
        except Exception as e:
            msg = str(e)
            print(f"Recording error: {msg}")
            self._update_status(f"Mic error")

            if "PortAudio" in msg or "PaErrorCode" in msg:
                 rumps.notification(
                    "LiteType Error",
                    "Audio Device Busy",
                    "Please restart LiteType to reset audio."
                )

    def _on_hotkey_release(self):
        """Called when Fn+Ctrl is released."""
        print(">>> Recording stopped, transcribing...")
        if not self._is_recording:
            return

        self._is_recording = False
        self._is_processing = True
        self._set_title("⏳ PROC")
        self._play_sound("Pop")
        self._update_status("Transcribing...")

        # Transcribe in background
        def process():
            try:
                print(">>> Stopping audio stream...")
                audio = self._audio_recorder.stop_recording()
                level = float(np.sqrt(np.mean(audio ** 2))) if audio.size else 0.0

                if audio.size > 0 and level < SILENCE_RMS:
                    print(f">>> Too quiet to transcribe (rms {level:.4f})")
                    self._update_status("No speech detected")
                elif audio.size > 0:
                    print(f">>> Transcribing {len(audio)} samples (rms {level:.4f})...")
                    text = self._transcriber.transcribe(audio)

                    if text:
                        text = text.strip()
                        print(f">>> Result: {text}")

                        # Check for voice shutdown command
                        clean_text = text.lower().replace(".", "").replace("!", "").replace(",", "").strip()
                        shutdown_phrases = [
                            "litetype shut down", "light type shut down", "lighttype shut down",
                            "light type shot down", "light time shutdown", "lite type shutdown",
                            "light type shutdown", "litetype shutdown"
                        ]

                        if any(phrase in clean_text for phrase in shutdown_phrases):
                            print(">>> Voice shutdown command received.")
                            self._update_status("Shutting down...")
                            rumps.notification("LiteType", "Shutting down", "Voice command received.")
                            time.sleep(1)
                            self._quit(None)
                            return

                        text = text.strip()

                        success = insert_text(text)
                        if success:
                            print(">>> Paste command sent successfully.")
                            self._remember(text)
                            self._update_status(f"✓ {text[:20]}...")
                        else:
                            print(">>> Paste FAILED.")
                            self._update_status("Paste failed")
                    else:
                        self._update_status("No speech detected")
                else:
                    self._update_status("No audio")

            except Exception as e:
                print(f">>> Transcription error: {e}")
                self._update_status("Error")

            finally:
                self._is_processing = False
                self._set_title("🎙️")
                time.sleep(2)
                if not self._is_recording and not self._is_processing:
                    self._update_status(f"Ready - Hold {self._trigger}")

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    # --- Recent transcriptions -------------------------------------------

    def _remember(self, text: str):
        """Add a transcription to the in-memory history (newest last)."""
        if text in self._history:
            self._history.remove(text)
        self._history.append(text)
        AppHelper.callAfter(self._populate_recent)

    def _populate_recent(self):
        """Rebuild the Recent submenu. Main thread only."""
        # Not .clear(): rumps only creates the submenu on first add, so
        # clearing an item with no children crashes
        for key in list(self._recent_menu.keys()):
            del self._recent_menu[key]
        if not self._history:
            self._recent_menu.add(rumps.MenuItem("(none yet)"))
            return
        # Numbered so menu titles stay unique (rumps keys items by title)
        for i, text in enumerate(reversed(self._history), start=1):
            label = text if len(text) <= MENU_TEXT_LEN else text[:MENU_TEXT_LEN - 1] + "…"
            self._recent_menu.add(rumps.MenuItem(
                f"{i}. {label}", callback=lambda _, t=text: self._repaste(t)))

    def _paste_last(self, _):
        if not self._history:
            self._update_status("Nothing to paste yet")
            return
        self._repaste(self._history[-1])

    def _repaste(self, text: str):
        """Paste a previous transcription into the frontmost app."""
        if self._is_recording or self._is_processing:
            return
        self._is_processing = True

        def run():
            try:
                # Let the menu close and focus return to the target app
                time.sleep(0.15)
                if insert_text(text):
                    print(">>> Re-pasted from history.")
                    self._update_status(f"✓ {text[:20]}...")
                else:
                    self._update_status("Paste failed")
            finally:
                self._is_processing = False

        threading.Thread(target=run, daemon=True).start()

    # --- Model switching -------------------------------------------------

    def _refresh_model_checks(self):
        def apply():
            for item in self._model_menu.values():
                item.state = item.title == self._model_name
        AppHelper.callAfter(apply)

    def _select_model(self, name: str):
        if name == self._model_name or self._is_recording or self._is_processing:
            return
        self._is_processing = True
        self._set_title("⏳")
        self._update_status(f"Loading {name}...")

        def load():
            try:
                self._transcriber = Transcriber(
                    os.path.join(models_dir(), name), self._vocabulary)
                self._model_name = name
                model_cfg = self.config.setdefault("model", {})
                model_cfg["default_model"] = name
                # Otherwise use_small_en would override the choice on restart
                model_cfg["use_small_en"] = False
                save_config(self.config)
                self._update_status(f"Ready - Hold {self._trigger}")
            except Exception as e:
                print(f">>> Model load failed: {e}")
                self._update_status("Model load failed")
            finally:
                self._is_processing = False
                self._set_title("🎙️")
                self._refresh_model_checks()

        threading.Thread(target=load, daemon=True).start()

    # --- Microphone choice -----------------------------------------------

    def _populate_mics(self):
        """Rebuild the Microphone submenu. Main thread only."""
        for key in list(self._mic_menu.keys()):
            del self._mic_menu[key]

        preferred = self._audio_recorder.preferred_mics
        current = preferred[0].lower() if preferred else None

        default_item = rumps.MenuItem(
            "System Default", callback=lambda _: self._select_mic(None))
        default_item.state = current is None
        self._mic_menu.add(default_item)
        self._mic_menu.add(rumps.separator)
        for name in self._audio_recorder.list_input_devices():
            item = rumps.MenuItem(name, callback=lambda _, n=name: self._select_mic(n))
            item.state = current is not None and current in name.lower()
            self._mic_menu.add(item)
        self._mic_menu.add(rumps.separator)
        self._mic_menu.add(rumps.MenuItem("Refresh List", callback=self._refresh_mics))

    def _select_mic(self, name: str | None):
        """Make a mic the first choice (None = follow the system default).
        Other saved preferences stay as fallbacks."""
        if name is None:
            preferred = []
        else:
            preferred = [name] + [p for p in self._audio_recorder.preferred_mics if p != name]
        self._audio_recorder.preferred_mics = preferred
        self.config["microphone"] = preferred
        save_config(self.config)
        self._populate_mics()
        self._update_status(f"Mic: {name or 'System Default'}")

    def _refresh_mics(self, _):
        # Re-scanning tears down PortAudio, so never while a stream is open
        if self._is_recording or self._is_processing:
            self._update_status("Busy - try again in a moment")
            return
        try:
            self._audio_recorder.refresh_devices()
        except Exception as e:
            print(f"Warning: Could not refresh audio devices: {e}")
        self._populate_mics()

    # --- Start at login --------------------------------------------------

    def _toggle_login(self, sender):
        if sender.state:
            login_item.disable()
        elif login_item.enable():
            rumps.notification(
                "LiteType",
                "Will start at login",
                "After your next login, allow Python under Microphone and "
                "Accessibility in System Settings > Privacy & Security."
            )
        sender.state = login_item.is_enabled()

    # --- UI helpers ------------------------------------------------------

    def _set_title(self, title: str):
        """Update the menu bar title. AppKit is not thread-safe, so this is
        always marshalled onto the main thread -- touching the status item
        from the transcription thread can wedge the whole app."""
        def apply():
            self.title = title
        AppHelper.callAfter(apply)

    def _update_status(self, status: str):
        """Update the status menu item (on the main thread, see _set_title)."""
        def apply():
            try:
                self._status_item.title = f"Status: {status}"
            except Exception as e:
                print(f"Warning: Failed to update status: {e}")
        AppHelper.callAfter(apply)

    def _quit(self, _):
        """Quit the application."""
        if self._hotkey_handler:
            self._hotkey_handler.stop()
        rumps.quit_application()


class _TimestampedTee:
    """Mirror stdout/stderr into a timestamped log file, so failures can be
    diagnosed after the launcher's Terminal window is gone."""

    def __init__(self, stream, log_file):
        self._stream = stream
        self._log = log_file
        self._at_line_start = True

    def write(self, data):
        self._stream.write(data)
        try:
            for chunk in data.splitlines(keepends=True):
                if self._at_line_start:
                    self._log.write(time.strftime("%Y-%m-%d %H:%M:%S "))
                self._log.write(chunk)
                self._at_line_start = chunk.endswith("\n")
            self._log.flush()
        except Exception:
            pass
        return len(data)

    def flush(self):
        self._stream.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)


def _start_logging():
    try:
        log_file = open(LOG_PATH, "a", encoding="utf-8")
    except OSError as e:
        print(f"Warning: Could not open log file {LOG_PATH}: {e}")
        return
    sys.stdout = _TimestampedTee(sys.stdout, log_file)
    sys.stderr = _TimestampedTee(sys.stderr, log_file)


def main():
    """Entry point for the application."""
    _start_logging()
    print("Starting LiteType...")
    print("=" * 40)
    print("Menu bar icon: VTT (or 🎙️ when ready)")
    print("Hold Fn+Ctrl to record, release to transcribe.")
    print("=" * 40)

    app = VTTApp()
    app.run()


if __name__ == "__main__":
    main()
