"""High-level neural TTS entry point and helpers.

Maintains direct backward-compatibility for Friday audio components.
"""

from typing import Optional
import numpy as np

from friday.audio.engines.neural import NeuralTTSEngine, NeuralVoiceInfo
from friday.audio.voice_manager import VoiceManager

__all__ = ["NeuralTTSEngine", "NeuralVoiceInfo", "VoiceManager"]
