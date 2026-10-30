"""Transcription module for VTT Local.

Wraps pywhispercpp for speech-to-text transcription.
"""

import os
import re
import numpy as np
from pywhispercpp.model import Model

# Non-speech tags Whisper emits, e.g. [BLANK_AUDIO], (music), [inaudible].
_TAG_RE = re.compile(r"\[[^\]]*\]|\([^)]*\)")

# Phrases Whisper is known to "hear" in silence or near-silence. Only
# dropped when they are the entire transcript.
PHANTOM_PHRASES = {
    "thank you",
    "thanks for watching",
    "thank you for watching",
    "you",
}


def build_prompt(vocabulary: list[str] | None) -> str:
    """Build a Whisper initial prompt that nudges spelling of custom terms."""
    words = [w.strip() for w in (vocabulary or []) if w and w.strip()]
    if not words:
        return ""
    return "Glossary: " + ", ".join(words) + "."


def _normalise(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text).strip().lower()


def clean_transcript(text: str, prompt: str = "") -> str:
    """Strip non-speech tags and drop known silence hallucinations.

    Returns "" if nothing real is left.
    """
    text = _TAG_RE.sub("", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    norm = _normalise(text)
    if not norm or norm in PHANTOM_PHRASES:
        return ""
    # Whisper occasionally echoes its initial prompt back on silence
    if prompt and norm == _normalise(prompt):
        return ""
    return text


class Transcriber:
    """Whisper-based speech-to-text transcriber."""

    def __init__(self, model_path: str, vocabulary: list[str] | None = None):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")

        print(f"Loading Whisper model from {model_path}...")
        self._model = Model(model_path)
        self._prompt = build_prompt(vocabulary)
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

        segments = self._model.transcribe(
            audio,
            language=language,
            initial_prompt=self._prompt,
            print_progress=False,
        )

        text_parts = [segment.text for segment in segments]
        result = " ".join(text_parts).strip()

        return clean_transcript(result, self._prompt)
