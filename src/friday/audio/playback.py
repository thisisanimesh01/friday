"""Audio playback manager and microphone coordination.

Provides safe half-duplex coordination:
- Gating / suspending microphone listeners during audio playback to prevent self-triggering.
- Playback cancellation and cleanup.
- Resuming the appropriate listening state once playback completes.
"""

import logging
import threading
from typing import Optional

from friday.audio.tts import TTSEngine

logger = logging.getLogger(__name__)


class PlaybackManager:
    """Coordinates audio playback with microphone gating to prevent acoustic loopback."""

    def __init__(self, tts_engine: Optional[TTSEngine] = None):
        self.tts = tts_engine or TTSEngine()
        self._is_playing: bool = False
        self._lock = threading.Lock()

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def speak(self, text: str, listener: Optional[object] = None) -> bool:
        """Speak response text while gating the microphone listener if provided."""
        if not text:
            return False

        # Half-duplex coordination: mute or pause listener during playback
        prior_state = None
        if listener and hasattr(listener, "state"):
            prior_state = getattr(listener, "state")
            if hasattr(listener, "mute"):
                listener.mute()

        with self._lock:
            self._is_playing = True

        success = False
        try:
            success = self.tts.speak(text)
        finally:
            with self._lock:
                self._is_playing = False

            # Restore listener state after playback finishes
            if listener and prior_state and hasattr(listener, "state"):
                # If the listener was previously in STANDBY or FOLLOW_UP, resume safely
                from friday.audio.session import ConversationState
                if prior_state in (ConversationState.STANDBY, ConversationState.FOLLOW_UP, ConversationState.LISTENING):
                    setattr(listener, "state", prior_state)

        return success

    def stop(self) -> None:
        """Immediately stop playback and cancel TTS subprocess."""
        self.tts.stop()
        with self._lock:
            self._is_playing = False
