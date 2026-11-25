#!/usr/bin/env python3
"""Benchmark voice pipeline latency across VAD, wake-word, and continuous session."""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from friday.audio.session import ContinuousListener
from friday.audio.vad import SpeechEndpointDetector, VoiceActivityDetector
from friday.audio.wake_word import WakeWordEngine


def run_benchmark(iterations: int = 100) -> None:
    print(f"Benchmarking Voice Pipeline over {iterations} iterations...")

    vad = VoiceActivityDetector()
    endpoint = SpeechEndpointDetector(vad=vad)
    wake = WakeWordEngine()
    session = ContinuousListener(wake_engine=wake, vad=vad)
    session.start()

    dummy_chunk = b"\x00\x00" * 320

    start_time = time.perf_counter()
    for _ in range(iterations):
        vad.is_speech(dummy_chunk)
        endpoint.process_chunk(dummy_chunk)
        session.handle_audio_frame(dummy_chunk)
    elapsed = time.perf_counter() - start_time

    per_frame_ms = (elapsed / iterations) * 1000
    print(f"Total time: {elapsed:.4f}s")
    print(f"Average frame pipeline latency: {per_frame_ms:.4f}ms per 20ms audio frame")
    session.stop()
    print("Voice pipeline benchmark completed successfully.")


if __name__ == "__main__":
    run_benchmark()
