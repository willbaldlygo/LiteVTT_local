"""Tests for microphone capture and recovery logic in litetype.audio.AudioRecorder."""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from litetype.audio import AudioRecorder


# ---------------------------------------------------------------------------
# Resampling to Whisper's expected 16kHz
# ---------------------------------------------------------------------------

class TestResampleToTarget:
    def test_same_rate_returns_audio_unchanged(self):
        recorder = AudioRecorder()
        audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        result = recorder._resample_to_target(audio, AudioRecorder.SAMPLE_RATE)
        assert result is audio

    def test_empty_audio_returns_unchanged(self):
        recorder = AudioRecorder()
        audio = np.array([], dtype=np.float32)
        result = recorder._resample_to_target(audio, 48000)
        assert result.size == 0

    def test_downsamples_to_expected_length(self):
        recorder = AudioRecorder()
        # 1 second of audio at 48kHz should become ~1 second at 16kHz.
        audio = np.linspace(-1, 1, 48000, dtype=np.float32)
        result = recorder._resample_to_target(audio, 48000)
        assert result.dtype == np.float32
        assert abs(len(result) - 16000) <= 1

    def test_upsamples_to_expected_length(self):
        recorder = AudioRecorder()
        audio = np.linspace(-1, 1, 8000, dtype=np.float32)
        result = recorder._resample_to_target(audio, 8000)
        assert abs(len(result) - 16000) <= 1

    def test_resampled_values_stay_within_original_range(self):
        recorder = AudioRecorder()
        audio = np.sin(np.linspace(0, 2 * np.pi, 4000)).astype(np.float32)
        result = recorder._resample_to_target(audio, 8000)
        assert result.max() <= audio.max() + 1e-3
        assert result.min() >= audio.min() - 1e-3


# ---------------------------------------------------------------------------
# Recovery when opening the microphone fails
# ---------------------------------------------------------------------------

class TestStartRecordingRetry:
    def test_opens_successfully_on_first_try(self):
        recorder = AudioRecorder()
        mock_stream = MagicMock()
        with patch('litetype.audio.sd.query_devices', return_value={'default_samplerate': 16000}), \
             patch('litetype.audio.sd.InputStream', return_value=mock_stream) as mock_input_stream, \
             patch('litetype.audio.sd._terminate') as mock_terminate:
            recorder.start_recording()

        mock_input_stream.assert_called_once()
        mock_terminate.assert_not_called()
        assert recorder.is_recording()
        assert recorder._stream is mock_stream

    def test_refreshes_devices_and_retries_once_on_failure(self):
        recorder = AudioRecorder()
        good_stream = MagicMock()
        with patch('litetype.audio.sd.query_devices', return_value={'default_samplerate': 16000}), \
             patch('litetype.audio.sd.InputStream',
                   side_effect=[RuntimeError("Invalid Property Value"), good_stream]) as mock_input_stream, \
             patch('litetype.audio.sd._terminate') as mock_terminate, \
             patch('litetype.audio.sd._initialize') as mock_initialize:
            recorder.start_recording()

        assert mock_input_stream.call_count == 2
        mock_terminate.assert_called_once()
        mock_initialize.assert_called_once()
        assert recorder.is_recording()
        assert recorder._stream is good_stream

    def test_raises_and_does_not_loop_when_both_attempts_fail(self):
        recorder = AudioRecorder()
        with patch('litetype.audio.sd.query_devices', return_value={'default_samplerate': 16000}), \
             patch('litetype.audio.sd.InputStream',
                   side_effect=RuntimeError("Invalid Property Value")) as mock_input_stream, \
             patch('litetype.audio.sd._terminate') as mock_terminate, \
             patch('litetype.audio.sd._initialize') as mock_initialize:
            with pytest.raises(RuntimeError):
                recorder.start_recording()

        # Exactly one retry -- not an infinite loop.
        assert mock_input_stream.call_count == 2
        mock_terminate.assert_called_once()
        mock_initialize.assert_called_once()
        assert not recorder.is_recording()
        assert recorder._stream is None


# ---------------------------------------------------------------------------
# start_recording -> stop_recording integration: the captured device rate
# is what stop_recording resamples from.
# ---------------------------------------------------------------------------

class TestStartStopIntegration:
    def test_stop_recording_resamples_using_the_rate_start_recording_opened_at(self):
        recorder = AudioRecorder()
        mock_stream = MagicMock()
        with patch('litetype.audio.sd.query_devices', return_value={'default_samplerate': 48000}), \
             patch('litetype.audio.sd.InputStream', return_value=mock_stream):
            recorder.start_recording()

        # Simulate the callback having captured 48kHz audio.
        chunk = np.zeros((4800, 1), dtype=np.float32)  # 0.1s at 48kHz
        recorder._audio_buffer.append(chunk)

        audio = recorder.stop_recording()
        # 0.1s should resample down to ~1600 samples at 16kHz.
        assert abs(len(audio) - 1600) <= 1
