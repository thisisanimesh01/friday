#!/usr/bin/env python3
"""Benchmark complete-response speech vs incremental streaming speech latency."""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from friday.audio.speech_segmenter import SpeechSegmenter
from friday.audio.expression import select_expression_for_context


def benchmark_streaming_speech() -> None:
    print("=" * 60)
    print("FRIDAY Streaming Speech & Expression Benchmark")
    print("=" * 60)

    # Simulated LLM streaming response chunks
    llm_tokens = [
        "Hello, ", "I am Friday. ", "All systems ", "are running smoothly.\n",
        "Here is the ", "status of your background ", "tasks: everything passed! ",
        "Would you like ", "to proceed with the deployment?"
    ]

    segmenter = SpeechSegmenter(min_chars=20)
    start_time = time.perf_counter()

    first_segment_time = None
    emitted_segments = []

    for chunk in llm_tokens:
        segs = segmenter.add_chunk(chunk)
        if segs:
            if first_segment_time is None:
                first_segment_time = time.perf_counter() - start_time
            emitted_segments.extend(segs)

    final_segs = segmenter.flush()
    emitted_segments.extend(final_segs)
    total_time = time.perf_counter() - start_time

    print(f"Total simulated tokens: {len(llm_tokens)}")
    print(f"Emitted speech segments: {len(emitted_segments)}")
    for i, seg in enumerate(emitted_segments):
        exp = select_expression_for_context(seg)
        print(f"  Segment {i+1}: '{seg}' [Style: {exp.expression.value}, Rate mult: {exp.rate_multiplier}]")

    print(f"\nTime to first speakable segment: {first_segment_time * 1000:.3f}ms" if first_segment_time else "N/A")
    print(f"Total segmentation elapsed time: {total_time * 1000:.3f}ms")
    print("Streaming speech benchmark completed successfully.")


if __name__ == "__main__":
    benchmark_streaming_speech()
