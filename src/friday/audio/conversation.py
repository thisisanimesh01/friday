"""Unified Hands-Free Conversation Controller for FRIDAY.

Orchestrates:
1. Wake-Word standby ('Hey Friday').
2. Voice Activity Detection (VAD) & speech endpoint tracking.
3. Local Whisper Speech-to-Text.
4. AI Response Generation (streaming or complete).
5. Sentence-level incremental Text-to-Speech synthesis with emotional expression.
6. Spoken Barge-In during active audio playback with acoustic gating.
7. Hands-free follow-up conversational turns.
8. Controlled shutdown ('Stop listening') and session completion ('Goodbye Friday').
"""

import enum
import logging
import os
import threading
import time
from typing import Callable, Generator, Optional

from friday.audio.expression import select_expression_for_context
from friday.audio.playback import PlaybackManager
from friday.audio.recorder import AudioRecorder
from friday.audio.session import ConversationState
from friday.audio.speech_segmenter import SpeechSegmenter
from friday.audio.streaming_tts import StreamingTTSCoordinator
from friday.audio.stt import WhisperEngine
from friday.audio.tts import TTSEngine
from friday.audio.vad import SpeechEndpointDetector, VoiceActivityDetector
from friday.audio.voice_profile import VoiceProfile, VoiceRegistry
from friday.audio.wake_word import WakeWordEngine

logger = logging.getLogger(__name__)


class HandsFreeController:
    """Coordinates hands-free voice conversations, spoken barge-in, and playback gating."""

    def __init__(
        self,
        wake_engine: Optional[WakeWordEngine] = None,
        stt_engine: Optional[WhisperEngine] = None,
        tts_engine: Optional[TTSEngine] = None,
        vad: Optional[VoiceActivityDetector] = None,
        voice_profile: Optional[VoiceProfile] = None,
        response_handler: Optional[Callable[[str], str]] = None,
        session_timeout: float = 30.0,
        enable_barge_in: bool = True,
    ):
        self.wake_engine = wake_engine or WakeWordEngine()
        self.stt_engine = stt_engine or WhisperEngine()
        self.tts_engine = tts_engine or TTSEngine()
        self.vad = vad or VoiceActivityDetector()
        self.endpoint_detector = SpeechEndpointDetector(vad=self.vad)
        self.recorder = AudioRecorder()
        self.profile = voice_profile or VoiceRegistry().get_profile()

        self.playback_manager = PlaybackManager(tts_engine=self.tts_engine)
        self.streaming_tts = StreamingTTSCoordinator(
            playback_manager=self.playback_manager,
            tts_engine=self.tts_engine,
            voice_profile=self.profile,
        )

        self.response_handler = response_handler
        self.session_timeout = session_timeout
        self.enable_barge_in = enable_barge_in

        self.state: ConversationState = ConversationState.DISABLED
        self._running: bool = False
        self._last_interaction_time: float = 0.0
        self._is_speaking: bool = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start hands-free controller in wake-word standby."""
        with self._lock:
            self._running = True
            self.state = ConversationState.STANDBY
            self._last_interaction_time = time.time()
            self._is_speaking = False
            self.recorder.reset()
            self.endpoint_detector.reset()

    def stop(self) -> None:
        """Completely shut down controller and audio resources."""
        with self._lock:
            self._running = False
            self.state = ConversationState.STOPPED
            self._is_speaking = False
        self.streaming_tts.cancel()
        self.playback_manager.stop()
        self.recorder.reset()
        self.endpoint_detector.reset()

    def mute(self) -> None:
        """Mute controller, stopping audio capture until explicit unmute."""
        with self._lock:
            self.state = ConversationState.MUTED
            self.recorder.reset()

    def is_barge_in_phrase(self, text: str) -> bool:
        """Check if recognized phrase requests spoken barge-in / interruption."""
        cleaned = text.strip().lower()
        return any(
            cleaned == kw or cleaned.startswith(f"{kw} ")
            for kw in ["stop", "cancel", "wait", "ruko", "ruk", "chup", "shut up", "bas"]
        )

    def is_session_end(self, text: str) -> bool:
        """Check if recognized phrase requests ending hands-free conversation."""
        cleaned = text.strip().lower()
        return cleaned in ["goodbye friday", "bye friday", "goodbye", "alvida friday", "alvida"]

    def is_mic_shutdown(self, text: str) -> bool:
        """Check if recognized phrase requests complete microphone shutdown."""
        cleaned = text.strip().lower()
        return cleaned in ["stop listening", "turn off mic", "mute mic", "mic band karo"]

    def handle_audio_frame(self, pcm_chunk: bytes) -> Optional[str]:
        """Process incoming 16kHz mono PCM16 audio frame."""
        with self._lock:
            if not self._running or self.state in (ConversationState.DISABLED, ConversationState.MUTED, ConversationState.STOPPED):
                return None

            now = time.time()

            # 1. Active speech playback state: handle spoken barge-in if enabled
            if self.state == ConversationState.RESPONDING:
                if not self.enable_barge_in:
                    # Half-duplex: ignore microphone during playback to prevent acoustic echo
                    return None

                # Controlled Duplex: check for spoken barge-in
                decision = self.vad.is_speech(pcm_chunk)
                if decision.is_speech and decision.energy > 0.03:
                    # User interrupted speaking
                    self.streaming_tts.cancel()
                    self.playback_manager.stop()
                    self.state = ConversationState.INTERRUPTED
                    self.recorder.reset()
                    self.endpoint_detector.reset()
                    return "Spoken barge-in detected. Interrupted playback."
                return None

            # 2. STANDBY state: wake-word detection ('Hey Friday')
            if self.state == ConversationState.STANDBY:
                event = self.wake_engine.process_frame(pcm_chunk)
                if event is not None:
                    self.state = ConversationState.LISTENING
                    self._last_interaction_time = now
                    self.recorder.reset()
                    self.endpoint_detector.reset()
                    return f"Wake-word '{event.phrase}' detected. Listening for command..."
                return None

            # 3. LISTENING / FOLLOW_UP / RECORDING states
            if self.state in (ConversationState.LISTENING, ConversationState.FOLLOW_UP, ConversationState.RECORDING):
                # Inactivity session timeout
                if (now - self._last_interaction_time) > self.session_timeout:
                    self.state = ConversationState.STANDBY
                    self.recorder.reset()
                    self.endpoint_detector.reset()
                    return "Session timed out. Returning to wake-word standby."

                self.recorder.record_chunk(pcm_chunk)
                in_progress, completed = self.endpoint_detector.process_chunk(pcm_chunk)

                if in_progress:
                    self.state = ConversationState.RECORDING
                    self._last_interaction_time = now

                if completed:
                    self.state = ConversationState.TRANSCRIBING
                    raw_audio = self.recorder.get_raw_pcm16()
                    self.recorder.reset()
                    self.endpoint_detector.reset()

                    transcription = self.stt_engine.transcribe_pcm16(raw_audio)
                    text = transcription.text.strip()

                    if not text:
                        self.state = ConversationState.FOLLOW_UP
                        return None

                    # Check for microphone shutdown
                    if self.is_mic_shutdown(text):
                        self.stop()
                        return "Microphone monitoring stopped. Say or press a key to restart."

                    # Check for goodbye
                    if self.is_session_end(text):
                        self.state = ConversationState.STANDBY
                        return "Goodbye! Returning to wake-word standby."

                    # Check for interruption command
                    if self.is_barge_in_phrase(text):
                        self.streaming_tts.cancel()
                        self.playback_manager.stop()
                        self.state = ConversationState.INTERRUPTED
                        return "Interrupted active response."

                    # Execute command
                    self.state = ConversationState.THINKING
                    response = ""
                    if self.response_handler:
                        response = self.response_handler(text)

                    # Transition to RESPONDING while playback occurs
                    self.state = ConversationState.RESPONDING
                    exp = select_expression_for_context(response)
                    effective_rate = int(self.profile.speech_rate * exp.rate_multiplier)

                    # Speak completed response with acoustic loopback safety
                    self.tts_engine.speak(response, rate=effective_rate)

                    # Return to follow-up listening window
                    self.state = ConversationState.FOLLOW_UP
                    self._last_interaction_time = time.time()
                    return response

            return None
