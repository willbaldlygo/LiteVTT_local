"""Transcription module for VTT Local.

Wraps pywhispercpp for speech-to-text transcription.
"""

import os
import numpy as np
from pywhispercpp.model import Model
from typing import Optional


class Transcriber:
    """Whisper-based speech-to-text transcriber."""
    
    def __init__(self, model_path: str):
        """Initialize the transcriber with a Whisper model.
        
        Args:
            model_path: Path to the GGML Whisper model file (.bin)
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        print(f"Loading Whisper model from {model_path}...")
        self._model = Model(model_path)
        print("Model loaded successfully!")
    
    def transcribe(self, audio: np.ndarray, language: str = "en") -> str:
        """Transcribe audio to text.
        
        Args:
            audio: numpy array of float32 audio samples at 16kHz
            language: Language code (default: "en" for English)
        
        Returns:
            Transcribed text as a string
        """
        if audio.size == 0:
            return ""
        
        # Ensure audio is float32 and normalized
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        # Normalize if needed (should be in [-1, 1] range)
        max_val = np.abs(audio).max()
        if max_val > 1.0:
            audio = audio / max_val
        
        # Transcribe using pywhispercpp
        # Returns list of segments, each with text attribute
        segments = self._model.transcribe(audio, language=language)
        
        # Combine all segment texts
        text_parts = [segment.text for segment in segments]
        result = " ".join(text_parts).strip()
        
        return result


# Global transcriber instance (lazy-loaded)
_transcriber: Optional[Transcriber] = None

def get_transcriber(model_path: Optional[str] = None) -> Transcriber:
    """Get or create the global transcriber instance.
    
    Args:
        model_path: Path to model (only used on first call)
    
    Returns:
        Transcriber instance
    """
    global _transcriber
    
    if _transcriber is None:
        if model_path is None:
            # Default model path
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "models", "ggml-base.bin"
            )
        _transcriber = Transcriber(model_path)
    
    return _transcriber

def transcribe(audio: np.ndarray, language: str = "en") -> str:
    """Transcribe audio using the global transcriber.
    
    Args:
        audio: numpy array of float32 audio samples at 16kHz
        language: Language code (default: "en")
    
    Returns:
        Transcribed text
    """
    return get_transcriber().transcribe(audio, language)
