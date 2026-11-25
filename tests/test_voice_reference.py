import struct
import tempfile
import wave

from friday.audio.voice_reference import VoiceReferenceValidator


def _create_synthetic_wav(duration_s: float, sample_rate: int = 16000, amplitude: int = 5000) -> str:
    """Helper creating a temporary synthetic WAV file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()

    n_samples = int(duration_s * sample_rate)
    with wave.open(tmp_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = struct.pack(f"<{n_samples}h", *([amplitude] * n_samples))
        wf.writeframes(data)
    return tmp_path


def test_validator_nonexistent_file():
    validator = VoiceReferenceValidator()
    res = validator.validate_file("nonexistent_file_path.wav")
    assert not res.is_valid
    assert "does not exist" in res.error


def test_validator_duration_bounds():
    validator = VoiceReferenceValidator()

    # 1. Too short (0.5s < 2.0s minimum)
    short_wav = _create_synthetic_wav(duration_s=0.5)
    try:
        res_short = validator.validate_file(short_wav)
        assert not res_short.is_valid
        assert "outside allowed bounds" in res_short.error
    finally:
        import os
        os.unlink(short_wav)

    # 2. Valid duration (3.0s)
    valid_wav = _create_synthetic_wav(duration_s=3.0, amplitude=6000)
    try:
        res_valid = validator.validate_file(valid_wav)
        assert res_valid.is_valid
        assert res_valid.duration_s == 3.0
        assert res_valid.sample_rate == 16000
        assert res_valid.channels == 1
        assert res_valid.rms > 0.01
    finally:
        import os
        os.unlink(valid_wav)


def test_validator_silent_file():
    validator = VoiceReferenceValidator()
    silent_wav = _create_synthetic_wav(duration_s=3.0, amplitude=0)
    try:
        res = validator.validate_file(silent_wav)
        assert not res.is_valid
        assert "too silent" in res.error
    finally:
        import os
        os.unlink(silent_wav)
