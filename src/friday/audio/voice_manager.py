"""Unified Neural TTS and Voice Manager for FRIDAY.

Coordinates:
- Primary Neural TTS backend (Kokoro-82M with Hinata neural voice vector).
- Native macOS fallback backend (explicitly logged when active, never silent).
- Voice enumeration, switching, and configuration inspection.
- Audio synthesis with custom voice vector conditioning and emotional tuning.
"""

from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import Optional, Union

import numpy as np

from friday.audio.engines.native import NativeTTSEngine, Voice
from friday.audio.engines.neural import NeuralTTSEngine, NeuralVoiceInfo
from friday.audio.voice_profile import VoiceProfile, VoiceRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VoiceSystemStatus:
    """Consolidated voice system information for CLI and diagnosis."""
    active_engine: str
    active_model: str
    model_weights_path: str
    reference_audio_status: str
    voice_profile: str
    inference_device: str
    supported_languages: list[str]
    is_fallback_active: bool
    fallback_engine: str
    fallback_voice: str


class VoiceManager:
    """Manages neural voice synthesis, profiles, and explicit native fallback."""

    def __init__(
        self,
        neural_engine: Optional[NeuralTTSEngine] = None,
        native_engine: Optional[NativeTTSEngine] = None,
        profile_registry: Optional[VoiceRegistry] = None,
    ):
        self.neural = neural_engine or NeuralTTSEngine()
        self.native = native_engine or NativeTTSEngine()
        self.registry = profile_registry or VoiceRegistry()

        # Engine selection preference: neural unless forced to native
        env_engine = os.getenv("TTS_ENGINE", "neural").lower()
        self.preferred_engine = env_engine

    @property
    def is_neural_ready(self) -> bool:
        """Return True if neural TTS model and weights are ready."""
        return self.neural.is_available()

    def get_status(self, profile_id: Optional[str] = None) -> VoiceSystemStatus:
        """Return comprehensive voice status matching milestone requirements."""
        profile = self.registry.get_profile(profile_id)
        neural_info = self.neural.get_info()

        is_fallback = not self.is_neural_ready or self.preferred_engine == "native"
        active_engine = "native (CoreAudio say)" if is_fallback else "neural (Kokoro-82M ONNX)"
        active_model = profile.primary_voice if is_fallback else neural_info.model_name

        ref_path = self.neural.reference_wav_path
        if ref_path.is_file():
            ref_status = f"Available ({ref_path})"
        else:
            ref_status = "Not found (using default style vector)"

        return VoiceSystemStatus(
            active_engine=active_engine,
            active_model=active_model,
            model_weights_path=str(self.neural.model_path) if not is_fallback else "N/A (Built-in macOS)",
            reference_audio_status=ref_status,
            voice_profile=f"{profile.display_name} ({profile.profile_id})",
            inference_device=neural_info.device if not is_fallback else "macOS CoreAudio",
            supported_languages=neural_info.supported_languages if not is_fallback else ["en", "hi"],
            is_fallback_active=is_fallback,
            fallback_engine="native (CoreAudio say)",
            fallback_voice=profile.fallback_voice if hasattr(profile, "fallback_voice") else "Samantha",
        )

    def speak(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        force_native: bool = False,
    ) -> bool:
        """Synthesize and speak text, prioritizing neural voice with explicit fallback."""
        if not text:
            return False

        # If forced or preferred native, or if neural is unavailable, explicitly use native
        if force_native or self.preferred_engine == "native" or not self.is_neural_ready:
            if not force_native and self.preferred_engine != "native":
                logger.warning(
                    "NOTICE: Neural TTS weights unavailable at %s. Falling back to native %s voice.",
                    self.neural.model_path,
                    self.native.voice,
                )
            return self.native.speak(text, voice=voice, rate=rate)

        # Primary neural synthesis
        # Calculate speed from rate if rate provided (standard ~180 wpm = speed 1.0)
        speed = 0.95
        if rate:
            speed = round(rate / 185.0, 2)

        success = self.neural.speak(text, speed=speed)
        if not success:
            logger.warning("Neural speech synthesis failed. Falling back to native macOS voice.")
            return self.native.speak(text, voice=voice, rate=rate)

        return True

    def stop(self) -> None:
        """Stop playback across both engines immediately."""
        self.neural.stop()
        self.native.stop()

    def list_voices(self) -> list[Voice]:
        """List available voices from both neural and native backends."""
        voices = [
            Voice(
                name="hinata",
                locale="en_US",
                example="Hello! I am Friday, your personal AI assistant.",
            )
        ]
        voices.extend(self.native.list_voices())
        return voices
