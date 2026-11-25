"""Streaming Text-to-Speech coordinator.

Consumes streaming text generators (e.g. from Ollama or brain.ask_friday_stream),
segments text at natural sentence boundaries, and synthesizes completed segments
progressively while applying context-aware expression tuning and half-duplex mic gating.
"""

from collections.abc import Generator, Iterable
import logging
import threading
import time
from typing import Optional

from friday.audio.expression import ExpressionTuning, select_expression_for_context
from friday.audio.playback import PlaybackManager
from friday.audio.speech_segmenter import SpeechSegmenter
from friday.audio.tts import TTSEngine
from friday.audio.voice_profile import VoiceProfile, VoiceRegistry

logger = logging.getLogger(__name__)


class StreamingTTSCoordinator:
    """Coordinates incremental speech synthesis and ordered playback for streaming responses."""

    def __init__(
        self,
        playback_manager: Optional[PlaybackManager] = None,
        tts_engine: Optional[TTSEngine] = None,
        voice_profile: Optional[VoiceProfile] = None,
        min_segment_chars: int = 25,
    ):
        self.tts = tts_engine or TTSEngine()
        self.playback = playback_manager or PlaybackManager(tts_engine=self.tts)
        self.profile = voice_profile or VoiceRegistry().get_profile()
        self.segmenter = SpeechSegmenter(min_chars=min_segment_chars)

        self._cancelled: bool = False
        self._lock = threading.Lock()

    def cancel(self) -> None:
        """Immediately cancel active synthesis and playback."""
        with self._lock:
            self._cancelled = True
        self.playback.stop()
        self.segmenter.reset()

    def stream_and_speak(
        self,
        token_stream: Iterable[str],
        listener: Optional[object] = None,
        explicit_style: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Process streaming tokens: yields text to caller while speaking segments in order."""
        with self._lock:
            self._cancelled = False
        self.segmenter.reset()

        accumulated_text = ""
        first_segment_spoken = False
        expression: Optional[ExpressionTuning] = None

        for chunk in token_stream:
            with self._lock:
                if self._cancelled:
                    break

            accumulated_text += chunk
            yield chunk

            # Lazy expression detection once sufficient context is available
            if expression is None and len(accumulated_text) >= 20:
                expression = select_expression_for_context(
                    accumulated_text,
                    explicit_style=explicit_style,
                )

            # Check for completed speakable segments
            new_segments = self.segmenter.add_chunk(chunk)
            for seg in new_segments:
                with self._lock:
                    if self._cancelled:
                        break

                effective_rate = int(self.profile.speech_rate * (expression.rate_multiplier if expression else 1.0))
                # Speak segment locally
                self.tts.speak(seg, rate=effective_rate)
                first_segment_spoken = True

        # Flush final remaining sentence segment
        final_segments = self.segmenter.flush()
        for seg in final_segments:
            with self._lock:
                if self._cancelled:
                    break
            effective_rate = int(self.profile.speech_rate * (expression.rate_multiplier if expression else 1.0))
            self.tts.speak(seg, rate=effective_rate)
