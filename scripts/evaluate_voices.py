#!/usr/bin/env python3
"""Standardized voice evaluation dataset and comparison utility for FRIDAY."""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from friday.audio.tts import TTSEngine, prepare_speech_text
from friday.audio.voice_profile import VoiceRegistry

# Standardized multi-lingual non-sensitive evaluation corpus
EVALUATION_DATASET = [
    {
        "category": "English - Conversational",
        "text": "Hello, I am Friday. How can I help you today?",
    },
    {
        "category": "English - Gentle Explanation",
        "text": "Of course. Let me explain that in a simpler way.",
    },
    {
        "category": "English - Technical Confirmation",
        "text": "The Python function returns a list of dictionaries with all active processes.",
    },
    {
        "category": "Hindi - Greeting",
        "text": "नमस्ते, मैं फ्राइडे हूँ। मैं आपकी क्या सहायता कर सकती हूँ?",
    },
    {
        "category": "Hinglish - Conversational",
        "text": "Hello, aaj main aapki kya help kar sakti hoon? Aapka project ready hai.",
    },
]


def evaluate_profiles() -> None:
    print("=" * 60)
    print("FRIDAY Voice Profile & Model Feasibility Evaluation")
    print("=" * 60)

    registry = VoiceRegistry()
    profiles = registry.list_profiles()
    print(f"Registered Voice Profiles: {len(profiles)}")
    for p in profiles:
        print(f"  - [{p.profile_id}] {p.display_name} (Rate: {p.speech_rate} wpm, Style: {p.target_style})")

    engine = TTSEngine()
    print(f"\nBackend TTS Engine: {engine.engine_type} (Available: {engine.is_available()})")

    print("\nBenchmarking Evaluation Corpus Preprocessing Latency:")
    start_time = time.perf_counter()
    for item in EVALUATION_DATASET:
        cleaned = prepare_speech_text(item["text"])
        voice_selected = engine.select_voice_for_text(cleaned)
        print(f"  [{item['category']}] -> Voice: {voice_selected} | Len: {len(cleaned)} chars")
    elapsed = time.perf_counter() - start_time
    print(f"\nTotal Corpus Processing Time: {elapsed * 1000:.3f} ms")
    print("Voice evaluation run completed successfully.")


if __name__ == "__main__":
    evaluate_profiles()
