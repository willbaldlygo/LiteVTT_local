"""Audio capture module for VTT Local.

Captures audio from the microphone and returns numpy arrays
suitable for Whisper transcription (16kHz mono float32).
"""

import numpy as np
import sounddevice as sd
from typing import Optional
import threading


class AudioRecorder:
    """Records audio from the default microphone."""
    
    WHISPER_SAMPLE_RATE = 16000  # Whisper expects 16kHz
    CHANNELS = 1  # Mono
    
    def __init__(self):
        self._recording = False
        self._audio_buffer: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()
        self._device_sample_rate = 16000
    
    def _audio_callback(self, indata: np.ndarray, frames: int, 
                        time_info, status) -> None:
        """Called by sounddevice for each audio chunk."""
        if status:
            print(f"Audio status: {status}")
        if self._recording:
            with self._lock:
                self._audio_buffer.append(indata.copy())
    
    def start_recording(self) -> None:
        """Start capturing audio from the microphone."""
        try:
            current_default_device = sd.default.device[0]
        except Exception as e:
            print(f"Error getting default input device: {e}")
            raise e

        # Recreate stream if device changed or it hasn't been created yet
        need_new_stream = (
            self._stream is None or 
            self._stream.closed or 
            self._stream.device != current_default_device
        )

        if need_new_stream:
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    print(f"Warning: Failed to close previous stream: {e}")
                finally:
                    self._stream = None

            try:
                device_info = sd.query_devices(current_default_device, 'input')
                self._device_sample_rate = int(device_info['default_samplerate'])
            except Exception as e:
                print(f"Warning: Could not query default input device samplerate: {e}")
                self._device_sample_rate = 16000

            try:
                self._stream = sd.InputStream(
                    device=current_default_device,
                    samplerate=self._device_sample_rate,
                    channels=self.CHANNELS,
                    dtype='float32',
                    callback=self._audio_callback
                )
            except Exception as e:
                print(f"Error creating recording stream: {e}")
                self._stream = None
                self._recording = False
                raise e

        with self._lock:
            self._audio_buffer = []
            self._recording = True
        
        try:
            if not self._stream.active:
                self._stream.start()
        except Exception as e:
            print(f"Error starting recording stream: {e}")
            self._recording = False
            raise e
    
    def stop_recording(self) -> np.ndarray:
        """Stop recording and return the captured audio.
        
        Returns:
            numpy array of float32 audio samples at 16kHz
        """
        self._recording = False
        
        if self._stream:
            try:
                self._stream.stop()
            except Exception as e:
                print(f"Warning: Failed to stop stream: {e}")
        
        with self._lock:
            if not self._audio_buffer:
                return np.array([], dtype=np.float32)
            
            # Concatenate all chunks and flatten to 1D
            audio = np.concatenate(self._audio_buffer, axis=0)
            audio = audio.flatten()
            self._audio_buffer = []
            
        # Resample from native device sample rate to 16000 Hz if needed
        if self._device_sample_rate != self.WHISPER_SAMPLE_RATE:
            try:
                audio = self._resample(audio, self._device_sample_rate, self.WHISPER_SAMPLE_RATE)
            except Exception as e:
                print(f"Warning: Resampling failed: {e}")
        
        return audio
        
    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate using linear interpolation."""
        if orig_sr == target_sr or len(audio) == 0:
            return audio
        num_samples = int(len(audio) * target_sr / orig_sr)
        indices = np.linspace(0, len(audio) - 1, num_samples)
        return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
    
    def close(self) -> None:
        """Close the audio stream and release resources."""
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                print(f"Warning: Failed to close stream: {e}")
            finally:
                self._stream = None

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording
