#!/usr/bin/env python3
"""Benchmark wake-word detection latency and resource usage."""

import os
import sys
import time

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from friday.audio.wake_word import WakeWordEngine


def run_benchmark(iterations: int = 100) -> None:
    print(f"Benchmarking WakeWordEngine over {iterations} iterations...")
    engine = WakeWordEngine(phrase="Hey Friday", cooldown=0.0)

    # Synthetic 16kHz mono audio chunk (0.1s = 1600 samples = 3200 bytes)
    dummy_audio = b"\x00\x00" * 1600

    start_time = time.perf_counter()
    for _ in range(iterations):
        engine.process_frame(dummy_audio)
    total_elapsed = time.perf_counter() - start_time

    avg_latency_ms = (total_elapsed / iterations) * 1000
    print(f"Total time: {total_elapsed:.4f}s")
    print(f"Average frame processing latency: {avg_latency_ms:.4f}ms")
    print("Benchmark completed successfully.")


if __name__ == "__main__":
    run_benchmark()
