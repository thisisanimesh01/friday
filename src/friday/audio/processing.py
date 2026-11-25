"""Audio signal processing utilities for raw PCM16 bytes without heavy DSP dependencies."""

import math
import struct
import wave
from io import BytesIO


def calculate_rms_and_peak(pcm16_data: bytes) -> tuple[float, float, bool]:
    """Calculate RMS volume, peak amplitude (0.0 to 1.0), and clipping flag.

    pcm16_data must be 16-bit signed little-endian PCM bytes.
    """
    if not pcm16_data:
        return 0.0, 0.0, False

    sample_count = len(pcm16_data) // 2
    if sample_count == 0:
        return 0.0, 0.0, False

    fmt = f"<{sample_count}h"
    samples = struct.unpack(fmt, pcm16_data[: sample_count * 2])

    max_possible = 32768.0
    sum_squares = 0.0
    peak_val = 0

    clipped = False
    for s in samples:
        abs_s = abs(s)
        if abs_s > peak_val:
            peak_val = abs_s
        if abs_s >= 32760:
            clipped = True
        sum_squares += s * s

    mean_square = sum_squares / sample_count
    rms = math.sqrt(mean_square) / max_possible
    peak = peak_val / max_possible

    return round(rms, 4), round(peak, 4), clipped


def pcm16_to_wav_bytes(pcm16_data: bytes, sample_rate: int = 16000, channels: int = 1) -> bytes:
    """Pack raw PCM16 mono bytes into standard RIFF WAV container bytes in-memory."""
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16_data)
    return buf.getvalue()
