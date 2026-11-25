#!/usr/bin/env python3
"""Benchmark end-to-end hands-free conversational pipeline latency."""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from friday.audio.conversation import HandsFreeController


def benchmark_hands_free() -> None:
    print("=" * 60)
    print("FRIDAY Hands-Free Conversation Benchmark")
    print("=" * 60)

    controller = HandsFreeController()
    controller.start()
    print(f"Controller state: {controller.state.value}")

    # Benchmark frame routing latency over 100 frames
    dummy_frame = b"\x00\x00" * 320
    start = time.perf_counter()
    for _ in range(100):
        controller.handle_audio_frame(dummy_frame)
    elapsed = time.perf_counter() - start

    per_frame_ms = (elapsed / 100) * 1000
    print(f"Frame handling latency in STANDBY: {per_frame_ms:.4f}ms per 20ms frame")

    controller.stop()
    print(f"Controller shut down: {controller.state.value}")
    print("Hands-free benchmark completed successfully.")


if __name__ == "__main__":
    benchmark_hands_free()
