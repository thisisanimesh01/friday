#!/usr/bin/env python3
"""Benchmark voice tuning parameter permutations and reference validation latency."""

import os
import sys
import tempfile
import time
import wave
import struct

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from friday.audio.voice_profile import VoiceProfile, VoiceRegistry
from friday.audio.voice_reference import VoiceReferenceValidator


def benchmark_voice_tuning() -> None:
    print("=" * 60)
    print("FRIDAY Voice Reference & Tuning Benchmark")
    print("=" * 60)

    # 1. Profile Registry Performance
    registry = VoiceRegistry()
    tuning_variants = [
        {"rate": 150, "style": "whispery_calm"},
        {"rate": 165, "style": "gentle_hinata"},
        {"rate": 180, "style": "conversational"},
        {"rate": 200, "style": "brisk_clarity"},
    ]

    for idx, v in enumerate(tuning_variants):
        profile = VoiceProfile(
            profile_id=f"variant-{idx}",
            display_name=f"Variant {idx}",
            engine="native",
            primary_voice="Samantha",
            hindi_voice="Lekha",
            speech_rate=v["rate"],
            target_style=v["style"],
        )
        registry.register(profile)

    print(f"Registered {len(registry.list_profiles())} voice profile variants.")

    # 2. Reference Audio Validation Latency
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()

    # Create 4.0s synthetic WAV
    with wave.open(tmp_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(struct.pack("<64000h", *([4000] * 64000)))

    validator = VoiceReferenceValidator()
    iterations = 50
    start = time.perf_counter()
    for _ in range(iterations):
        res = validator.validate_file(tmp_path)
    elapsed = time.perf_counter() - start

    os.unlink(tmp_path)
    avg_ms = (elapsed / iterations) * 1000
    print(f"Validation latency: {avg_ms:.4f}ms per 4.0s audio reference (Valid: {res.is_valid})")
    print("Benchmark completed successfully.")


if __name__ == "__main__":
    benchmark_voice_tuning()
