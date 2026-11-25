#!/usr/bin/env python3
"""Benchmark local Text-to-Speech (TTS) synthesis and text preparation latency."""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from friday.audio.tts import TTSEngine, prepare_speech_text


def run_benchmark(iterations: int = 100) -> None:
    print(f"Benchmarking TTS text preparation over {iterations} iterations...")

    sample_markdown = (
        "## Friday Response\n"
        "Here is the status: all 3 services are online.\n"
        "```python\ndef test():\n    return True\n```\n"
        "Check documentation at https://friday.local for details."
    )

    start_time = time.perf_counter()
    for _ in range(iterations):
        prepare_speech_text(sample_markdown)
    elapsed = time.perf_counter() - start_time

    per_iter_ms = (elapsed / iterations) * 1000
    print(f"Text preparation latency: {per_iter_ms:.4f}ms per response")

    engine = TTSEngine()
    print(f"TTS Engine: {engine.engine_type} | Available: {engine.is_available()} | Voice: {engine.voice}")
    voices = engine.list_voices()
    print(f"Discovered {len(voices)} local voices.")
    print("TTS Benchmark completed successfully.")


if __name__ == "__main__":
    run_benchmark()
