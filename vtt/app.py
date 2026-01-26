"""Main application controller for VTT Local.

Menu bar app that coordinates audio recording, transcription,
and text insertion using a global hotkey.
"""

import rumps
import threading
import time
import os

from .audio import AudioRecorder
from .transcriber import Transcriber
from .hotkeys import create_option_s_handler
from .text_insert import insert_text
from AppKit import NSSound


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
        
        # State
        self._is_recording = False
        self._is_processing = False
        self._init_done = False
        
        # Build menu
        self._status_item = rumps.MenuItem("Status: Starting...")
        self.menu = [
            self._status_item,
            None,
            rumps.MenuItem("Hotkey: Fn+Ctrl (hold to record)"),
            None,
            rumps.MenuItem("Quit", callback=self._quit)
        ]
    
    @rumps.timer(1)
    def _init_timer(self, _):
        """Initialize everything on first timer tick."""
        if self._init_done:
            return
        self._init_done = True
        
        # Load model and setup hotkeys
        self._load_model()
        self._setup_hotkeys()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            self._update_status("Loading model...")
            
            # Try to load best available model
            models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
            
            # Priority list: small.en (accurate) > base.en (balanced) > base (current)
            candidates = ["ggml-small.en.bin", "ggml-base.en.bin", "ggml-base.bin"]
            
            model_path = None
            for name in candidates:
                path = os.path.join(models_dir, name)
                if os.path.exists(path):
                    model_path = path
                    self._update_status(f"Loaded: {name}")
                    break
            
            if not model_path:
                model_path = os.path.join(models_dir, "ggml-base.bin")
            
            if not os.path.exists(model_path):
                self._update_status("Model not found!")
                return
            
            self._transcriber = Transcriber(model_path)
            self.title = "🎙️"
            
        except Exception as e:
            self._update_status(f"Error: {str(e)[:30]}")
            print(f"Error loading model: {e}")
    
    def _setup_hotkeys(self):
        """Initialize hotkeys."""
        try:
            self._hotkey_handler = create_option_s_handler(
                on_activate=self._on_hotkey_press,
                on_deactivate=self._on_hotkey_release
            )
            self._hotkey_handler.start()
            self._update_status("Ready - Hold Option+S")
        except Exception as e:
            print(f"Failed to start hotkey listener: {e}")
            self._update_status(f"Hotkey error: {e}")

    def _play_sound(self, sound_name: str):
        """Play a system sound."""
        sound = NSSound.soundNamed_(sound_name)
        if sound:
            sound.play()
    
    def _on_hotkey_press(self):
        """Called when Option+S is pressed."""
        print(">>> Recording started")
        if self._is_processing or self._transcriber is None:
            print(">>> Cannot record: processing or no model")
            return
        
        self._is_recording = True
        self.title = "🔴 REC"
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
        """Called when Option+S is released."""
        print(">>> Recording stopped, transcribing...")
        if not self._is_recording:
            return
        
        self._is_recording = False
        self._is_processing = True
        self.title = "⏳ PROC"
        self._play_sound("Pop")
        self._update_status("Transcribing...")
        
        # Transcribe in background
        def process():
            try:
                # Stop recording in background thread to prevent blocking main loop
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
                        
                        # Cleanup text (standard whitespace)
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
                self.title = "🎙️"
                time.sleep(2)
                if not self._is_recording and not self._is_processing:
                    self._update_status("Ready - Hold Option+S")
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _update_status(self, status: str):
        """Update the status menu item."""
        try:
            self._status_item.title = f"Status: {status}"
        except:
            pass
    
    def _quit(self, _):
        """Quit the application."""
        if self._hotkey_handler:
            self._hotkey_handler.stop()
        rumps.quit_application()


def main():
    """Entry point for the application."""
    print("Starting VTT Local...")
    print("=" * 40)
    print("Menu bar icon: VTT (or 🎙️ when ready)")
    print("Hold Option+S to record, release to transcribe.")
    print("=" * 40)
    
    app = VTTApp()
    app.run()


if __name__ == "__main__":
    main()
