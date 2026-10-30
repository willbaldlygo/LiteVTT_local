"""Main application controller for VTT Local.

Menu bar app that coordinates audio recording, transcription,
and text insertion using a global hotkey.
"""

import os
import rumps
import sys
import threading
import time

from .audio import AudioRecorder
from .config import load_config
from .models import get_model_path
from .transcriber import Transcriber
from .hotkeys import create_hotkey_handler
from .text_insert import insert_text
from AppKit import NSSound
from PyObjCTools import AppHelper

LOG_PATH = os.path.expanduser("~/Library/Logs/LiteType.log")


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
        self._hotkey_handler = None
        self.config = load_config()

        # State
        self._is_recording = False
        self._is_processing = False
        self._init_done = False

        # Trigger help text
        self._trigger = self.config.get("hotkey", "Fn+Ctrl")

        # Build menu
        self._status_item = rumps.MenuItem("Status: Starting...")
        self.menu = [
            self._status_item,
            None,
            rumps.MenuItem(f"Hotkey: {self._trigger} (hold to record)"),
            None,
            rumps.MenuItem("Quit", callback=self._quit)
        ]

    @rumps.timer(1)
    def _init_timer(self, _):
        """Initialize everything on first timer tick."""
        if self._init_done:
            return
        self._init_done = True

        self._load_model()
        self._setup_hotkeys()

    def _load_model(self):
        """Load the Whisper model."""
        try:
            self._update_status("Loading model...")

            model_path, model_name = get_model_path(self.config)

            if not model_path:
                self._update_status("Model not found!")
                return

            self._update_status(f"Loaded: {model_name}")
            self._transcriber = Transcriber(model_path)
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

                if audio.size > 0:
                    print(f">>> Transcribing {len(audio)} samples...")
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
