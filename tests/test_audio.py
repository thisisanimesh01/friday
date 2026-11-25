import struct

from friday.audio import (
    AudioConfig,
    AudioRecorder,
    calculate_rms_and_peak,
    get_default_microphone,
    list_microphones,
    pcm16_to_wav_bytes,
)


def test_audio_config_defaults():
    cfg = AudioConfig()
    assert cfg.sample_rate == 16000
    assert cfg.channels == 1
    assert cfg.sample_width_bytes == 2


def test_calculate_rms_and_peak_silent():
    pcm = struct.pack("<100h", *([0] * 100))
    rms, peak, clipped = calculate_rms_and_peak(pcm)
    assert rms == 0.0
    assert peak == 0.0
    assert clipped is False


def test_calculate_rms_and_peak_clipping():
    # 32767 is max signed 16-bit int
    pcm = struct.pack("<10h", *([32767] * 10))
    rms, peak, clipped = calculate_rms_and_peak(pcm)
    assert peak >= 0.99
    assert clipped is True


def test_pcm16_to_wav_bytes():
    pcm = struct.pack("<50h", *([1000] * 50))
    wav_bytes = pcm16_to_wav_bytes(pcm, sample_rate=16000, channels=1)
    assert wav_bytes.startswith(b"RIFF")
    assert b"WAVE" in wav_bytes


def test_audio_recorder_buffer_and_metrics():
    rec = AudioRecorder(AudioConfig(max_duration_seconds=1.0, sample_rate=16000))
    chunk = struct.pack("<100h", *([500] * 100))
    rec.record_chunk(chunk)
    metrics = rec.get_metrics()
    assert metrics["bytes_recorded"] == 200
    assert metrics["duration_s"] > 0
    wav = rec.get_wav_bytes()
    assert wav.startswith(b"RIFF")
    rec.reset()
    assert rec.get_metrics()["bytes_recorded"] == 0


def test_list_microphones_without_sounddevice():
    # In CI without audio hardware/sounddevice, returns empty list gracefully
    mics = list_microphones()
    assert isinstance(mics, list)
    assert get_default_microphone() is None or hasattr(get_default_microphone(), "name")
