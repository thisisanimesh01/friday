"""Audio speech synthesis engines package.

Provides modular backends:
- NativeTTSEngine: macOS `say`CoreAudio synthesis (explicit fallback).
- NeuralTTSEngine: Kokoro-82M ONNX local neural voice synthesis with custom Hinata conditioning.
"""

from friday.audio.engines.native import NativeTTSEngine
from friday.audio.engines.neural import NeuralTTSEngine

__all__ = ["NativeTTSEngine", "NeuralTTSEngine"]
