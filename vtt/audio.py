"""Audio capture module for LiteType.

Captures audio from the microphone and returns numpy arrays
suitable for Whisper transcription (16kHz mono float32).
"""

import numpy as np
import sounddevice as sd
from typing import Optional
import threading


class AudioRecorder:
    """Records audio from the default microphone."""

    SAMPLE_RATE = 16000  # Whisper expects 16kHz
    CHANNELS = 1  # Mono

    def __init__(self):
        self._recording = False
        self._audio_buffer: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()
        self._device_sample_rate = self.SAMPLE_RATE

    def _audio_callback(self, indata: np.ndarray, frames: int,
                        time_info, status) -> None:
        """Called by sounddevice for each audio chunk."""
        if status:
            print(f"Audio status: {status}")
        if self._recording:
            with self._lock:
                self._audio_buffer.append(indata.copy())

    def _open_stream(self) -> sd.InputStream:
        """Open a new input stream at the current default device's own
        native sample rate, rather than forcing SAMPLE_RATE on the
        hardware. Demanding a fixed rate the device doesn't currently
        support is a common trigger for PortAudio's "Invalid Property
        Value" error, especially right after the OS has changed what the
        default input device is. stop_recording() resamples to
        SAMPLE_RATE in software afterwards."""
        try:
            device_info = sd.query_devices(kind='input')
            self._device_sample_rate = int(device_info['default_samplerate'])
        except Exception as e:
            print(f"Warning: Could not query default input device samplerate: {e}")
            self._device_sample_rate = self.SAMPLE_RATE

        stream = sd.InputStream(
            samplerate=self._device_sample_rate,
            channels=self.CHANNELS,
            dtype='float32',
            callback=self._audio_callback
        )
        stream.start()
        return stream

    def start_recording(self) -> None:
        """Start capturing audio from the microphone."""
        # Ensure previous stream is closed
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                print(f"Warning: Failed to close previous stream: {e}")
            finally:
                self._stream = None

        with self._lock:
            self._audio_buffer = []

        try:
            self._stream = self._open_stream()
            self._recording = True
        except Exception as first_error:
            # PortAudio only enumerates audio devices once, at process
            # start, so it can hold a stale view of the world after a
            # device change (a call app switching devices, a sleep/wake
            # cycle). Force it to re-scan and retry once before giving up
            # -- without this, every future attempt fails identically,
            # forever, until the process is restarted.
            print(f"Error starting recording stream: {first_error}")
            print("Refreshing audio devices and retrying once...")
            try:
                sd._terminate()
                sd._initialize()
                self._stream = self._open_stream()
                self._recording = True
            except Exception as retry_error:
                print(f"!!! LiteType: microphone failed to open twice in a row "
                      f"({retry_error}). Try restarting LiteType, or check "
                      f"System Settings > Sound.")
                self._recording = False
                self._stream = None
                raise retry_error

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return the captured audio as float32 at 16kHz."""
        self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._audio_buffer:
                return np.array([], dtype=np.float32)

            # Concatenate all chunks and flatten to 1D
            audio = np.concatenate(self._audio_buffer, axis=0)
            audio = audio.flatten()
            self._audio_buffer = []

        return self._resample_to_target(audio, self._device_sample_rate)

    def _resample_to_target(self, audio: np.ndarray, orig_rate: int) -> np.ndarray:
        """Resample captured audio to SAMPLE_RATE (Whisper expects 16kHz)."""
        if orig_rate == self.SAMPLE_RATE or audio.size == 0:
            return audio
        duration = audio.shape[0] / orig_rate
        target_len = int(round(duration * self.SAMPLE_RATE))
        orig_x = np.linspace(0, duration, num=audio.shape[0], endpoint=False)
        target_x = np.linspace(0, duration, num=target_len, endpoint=False)
        return np.interp(target_x, orig_x, audio).astype(np.float32)

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording
