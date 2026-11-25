"""In-memory bounded audio recorder."""

import threading
import time
from typing import Callable, Optional

from friday.audio.config import AudioConfig, DEFAULT_AUDIO_CONFIG
from friday.audio.processing import calculate_rms_and_peak, pcm16_to_wav_bytes


class AudioRecorder:
    def __init__(self, config: AudioConfig = DEFAULT_AUDIO_CONFIG):
        self.config = config
        self._buffer = bytearray()
        self._lock = threading.Lock()
        self._recording = False
        self._stream: Optional[object] = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    def record_chunk(self, data: bytes) -> None:
        """Append raw pcm bytes into bounded in-memory buffer."""
        max_bytes = int(
            self.config.sample_rate
            * self.config.channels
            * self.config.sample_width_bytes
            * self.config.max_duration_seconds
        )
        with self._lock:
            if len(self._buffer) + len(data) > max_bytes:
                # Discard overflow to keep memory strictly bounded
                allowed = max_bytes - len(self._buffer)
                if allowed > 0:
                    self._buffer.extend(data[:allowed])
            else:
                self._buffer.extend(data)

    def get_raw_pcm16(self) -> bytes:
        with self._lock:
            return bytes(self._buffer)

    def get_wav_bytes(self) -> bytes:
        raw = self.get_raw_pcm16()
        return pcm16_to_wav_bytes(
            raw,
            sample_rate=self.config.sample_rate,
            channels=self.config.channels,
        )

    def get_metrics(self) -> dict[str, float | bool]:
        raw = self.get_raw_pcm16()
        rms, peak, clipped = calculate_rms_and_peak(raw)
        duration_s = (
            len(raw) / (self.config.sample_rate * self.config.channels * self.config.sample_width_bytes)
            if self.config.sample_rate
            else 0.0
        )
        return {
            "duration_s": round(duration_s, 2),
            "rms": rms,
            "peak": peak,
            "clipped": clipped,
            "bytes_recorded": len(raw),
        }

    def reset(self) -> None:
        with self._lock:
            self._buffer.clear()
            self._recording = False
