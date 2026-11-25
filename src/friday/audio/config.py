"""Audio configuration and format standards for Friday.

Target format matches Whisper and speech processing requirements:
16,000 Hz sample rate, mono (1 channel), 16-bit signed PCM.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    sample_width_bytes: int = 2  # 16-bit signed PCM
    max_duration_seconds: float = 30.0
    chunk_size: int = 1024


DEFAULT_AUDIO_CONFIG = AudioConfig()
