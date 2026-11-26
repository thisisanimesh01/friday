"""Voice Profile abstraction and registry for FRIDAY.

Defines parameters for stylistic voice presentation (e.g. 'friday-gentle'
inspired by gentle, warm, and soft conversational delivery), managing voice
selection, speech rate, pitch/tone hints, language fallbacks, and engine routing.
"""

from dataclasses import dataclass, field
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VoiceProfile:
    """Configuration profile defining acoustic and stylistic voice characteristics."""
    profile_id: str
    display_name: str
    engine: str
    primary_voice: str
    hindi_voice: str
    speech_rate: int
    fallback_voice: str = "Samantha"
    volume: float = 1.0
    pitch_adjustment: float = 0.0  # Semitone offset where supported (-5.0 to +5.0)
    style_strength: float = 1.0    # Conditioning/style strength (0.0 to 1.0)
    reference_path: Optional[str] = None
    description: str = ""
    target_style: str = "gentle"
    supported_languages: list[str] = field(default_factory=lambda: ["en", "hi", "ja"])


class VoiceRegistry:
    """Manages available voice profiles and defaults."""

    def __init__(self) -> None:
        self._profiles: dict[str, VoiceProfile] = {}
        self._register_default_profiles()

    def _register_default_profiles(self) -> None:
        # 1. hinata / friday-gentle: Default Hinata Hyuga neural voice
        # Soft, warm, calm feminine voice with gentle conversational pacing
        self.register(
            VoiceProfile(
                profile_id="hinata",
                display_name="Hinata Hyuga (Neural Conditioning)",
                engine="neural",
                primary_voice="hinata",
                hindi_voice="Lekha",
                speech_rate=165,
                fallback_voice="Samantha",
                volume=1.0,
                description="Soft, gentle, warm feminine voice with calm delivery conditioned for Hinata Hyuga.",
                target_style="gentle",
            )
        )

        # Alias friday-gentle -> hinata
        self.register(
            VoiceProfile(
                profile_id="friday-gentle",
                display_name="Friday Gentle (Hinata Hyuga Neural)",
                engine="neural",
                primary_voice="hinata",
                hindi_voice="Lekha",
                speech_rate=165,
                fallback_voice="Samantha",
                volume=1.0,
                description="Soft, calm, and reassuring feminine voice with gentle conversational pacing.",
                target_style="gentle",
            )
        )

        # 2. friday-standard: Standard assistant voice
        self.register(
            VoiceProfile(
                profile_id="friday-standard",
                display_name="Friday Standard",
                engine="native",
                primary_voice="Samantha",
                hindi_voice="Lekha",
                speech_rate=185,
                fallback_voice="Samantha",
                volume=1.0,
                description="Clear, articulate, standard assistant voice.",
                target_style="standard",
            )
        )

    def register(self, profile: VoiceProfile) -> None:
        """Register a voice profile."""
        self._profiles[profile.profile_id] = profile

    def get_profile(self, profile_id: Optional[str] = None) -> VoiceProfile:
        """Retrieve voice profile by ID, falling back to environment or default."""
        target_id = profile_id or os.getenv("TTS_VOICE_PROFILE", "hinata")
        if target_id in self._profiles:
            return self._profiles[target_id]
        logger.warning(f"Voice profile '{target_id}' not found. Falling back to 'hinata'.")
        return self._profiles["hinata"]

    def list_profiles(self) -> list[VoiceProfile]:
        """Return list of all registered voice profiles."""
        return list(self._profiles.values())
