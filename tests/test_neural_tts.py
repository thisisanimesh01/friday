"""Unit and regression tests for Neural Voice and Voice Manager integration."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from friday.audio.engines.native import NativeTTSEngine
from friday.audio.engines.neural import NeuralTTSEngine, NeuralVoiceInfo
from friday.audio.voice_manager import VoiceManager, VoiceSystemStatus
from friday.audio.voice_profile import VoiceProfile, VoiceRegistry


def test_neural_engine_initialization_and_availability():
    tmp_dir = Path("/tmp/friday_test_voices_empty")
    engine = NeuralTTSEngine(model_dir=tmp_dir)

    # Empty dir means unavailable
    assert engine.is_available() is False
    info = engine.get_info()
    assert isinstance(info, NeuralVoiceInfo)
    assert info.is_available is False
    assert "Hinata Hyuga" in info.model_name
    assert "Apple Silicon" in info.device


def test_voice_manager_status_reporting():
    mock_neural = MagicMock(spec=NeuralTTSEngine)
    mock_neural.is_available.return_value = True
    mock_neural.model_path = Path("/path/to/model.onnx")
    mock_neural.reference_wav_path = Path("/nonexistent/ref.wav")
    mock_neural.get_info.return_value = NeuralVoiceInfo(
        engine_name="Kokoro-82M ONNX",
        model_name="Hinata Hyuga",
        model_path="/path/to/model.onnx",
        voices_path="/path/to/voices.bin",
        hinata_vector_path="/path/to/vector.npy",
        is_available=True,
        sample_rate=24000,
        device="Apple Silicon ARM64",
        supported_languages=["en", "hi", "ja"],
    )

    mock_native = MagicMock(spec=NativeTTSEngine)
    mock_native.is_available.return_value = True
    mock_native.voice = "Samantha"

    manager = VoiceManager(neural_engine=mock_neural, native_engine=mock_native)
    status = manager.get_status()

    assert isinstance(status, VoiceSystemStatus)
    assert "neural" in status.active_engine
    assert status.is_fallback_active is False
    assert status.fallback_voice == "Samantha"
    assert "Hinata" in status.active_model


def test_voice_manager_explicit_fallback_when_neural_unavailable():
    mock_neural = MagicMock(spec=NeuralTTSEngine)
    mock_neural.is_available.return_value = False
    mock_neural.model_path = Path("/path/to/model.onnx")
    mock_neural.reference_wav_path = Path("/path/to/ref.wav")
    mock_neural.get_info.return_value = NeuralVoiceInfo(
        engine_name="Kokoro-82M ONNX",
        model_name="Hinata Hyuga",
        model_path="/path/to/model.onnx",
        voices_path="/path/to/voices.bin",
        hinata_vector_path="/path/to/vector.npy",
        is_available=False,
        sample_rate=24000,
        device="Apple Silicon ARM64",
        supported_languages=["en", "hi", "ja"],
    )

    mock_native = MagicMock(spec=NativeTTSEngine)
    mock_native.is_available.return_value = True
    mock_native.voice = "Samantha"
    mock_native.speak.return_value = True

    manager = VoiceManager(neural_engine=mock_neural, native_engine=mock_native)
    status = manager.get_status()

    assert status.is_fallback_active is True
    assert "native" in status.active_engine

    # speak should route directly to native with explicit fallback log
    success = manager.speak("Hello there")
    assert success is True
    mock_native.speak.assert_called_once()
    mock_neural.speak.assert_not_called()


def test_voice_manager_neural_speech_execution():
    mock_neural = MagicMock(spec=NeuralTTSEngine)
    mock_neural.is_available.return_value = True
    mock_neural.speak.return_value = True

    mock_native = MagicMock(spec=NativeTTSEngine)

    manager = VoiceManager(neural_engine=mock_neural, native_engine=mock_native)
    success = manager.speak("Test sentence", rate=165)

    assert success is True
    mock_neural.speak.assert_called_once_with("Test sentence", speed=0.89)
    mock_native.speak.assert_not_called()


def test_voice_manager_stop_stops_both_backends():
    mock_neural = MagicMock(spec=NeuralTTSEngine)
    mock_native = MagicMock(spec=NativeTTSEngine)

    manager = VoiceManager(neural_engine=mock_neural, native_engine=mock_native)
    manager.stop()

    mock_neural.stop.assert_called_once()
    mock_native.stop.assert_called_once()
