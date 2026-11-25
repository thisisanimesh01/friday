import struct
from unittest.mock import MagicMock

from friday.audio.stt import TranscriptionResult, WhisperEngine


def test_whisper_engine_defaults():
    engine = WhisperEngine(language="en")
    assert engine.language == "en"
    assert engine.model_name == "base"


def test_transcribe_pcm16_empty():
    engine = WhisperEngine()
    result = engine.transcribe_pcm16(b"")
    assert result.text == ""
    assert result.duration_s == 0.0


def test_transcribe_pcm16_mocked_subprocess(monkeypatch):
    engine = WhisperEngine(binary_path="/bin/echo", model_path="/fake/model.bin")
    monkeypatch.setattr("os.path.exists", lambda path: True)

    mock_run = MagicMock()
    mock_run.stdout = "hello friday\n"
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_run)

    pcm_data = struct.pack("<16000h", *([100] * 16000))  # 1 second of audio
    result = engine.transcribe_pcm16(pcm_data, sample_rate=16000)
    assert result.text == "hello friday"
    assert result.duration_s == 1.0


def test_transcribe_pcm16_unconfigured_fallback():
    engine = WhisperEngine(binary_path=None, model_path=None)
    pcm_data = struct.pack("<1600h", *([0] * 1600))
    result = engine.transcribe_pcm16(pcm_data, sample_rate=16000)
    assert "not configured" in result.text.lower()
