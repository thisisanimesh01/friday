"""Continuous conversational listening and voice interruption session manager.

Coordinates:
- Wake-word detection standby ('Hey Friday').
- Follow-up conversational listening without repeating wake word.
- Voice activity and speech endpoint detection.
- Command capture and transcription.
- Response generation with interruption handling ('Stop', 'Cancel', 'Wait').
- Explicit session termination ('Goodbye Friday') and microphone shutdown ('Stop listening').
"""

from dataclasses import dataclass
import enum
import logging
import os
import threading
import time
from typing import Callable, Optional

from friday.audio.recorder import AudioRecorder
from friday.audio.stt import WhisperEngine
from friday.audio.vad import SpeechEndpointDetector, VoiceActivityDetector
from friday.audio.wake_word import ListenerState, WakeWordEngine, WakeWordEvent

logger = logging.getLogger(__name__)


class ConversationState(enum.Enum):
    """Lifecycle states for continuous conversational sessions."""
    DISABLED = "disabled"
    STANDBY = "standby"
    LISTENING = "listening"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    RESPONDING = "responding"
    FOLLOW_UP = "follow_up"
    INTERRUPTED = "interrupted"
    MUTED = "muted"
    STOPPED = "stopped"


class ContinuousListener:
    """Manages continuous conversational voice sessions and interruption handling."""

    def __init__(
        self,
        wake_engine: Optional[WakeWordEngine] = None,
        stt_engine: Optional[WhisperEngine] = None,
        vad: Optional[VoiceActivityDetector] = None,
        session_timeout: float = 30.0,
        follow_up_window: float = 10.0,
        response_handler: Optional[Callable[[str], str]] = None,
    ):
        self.wake_engine = wake_engine or WakeWordEngine()
        self.stt_engine = stt_engine or WhisperEngine()
        self.vad = vad or VoiceActivityDetector()
        self.endpoint_detector = SpeechEndpointDetector(vad=self.vad)
        self.recorder = AudioRecorder()

        self.session_timeout = session_timeout
        self.follow_up_window = follow_up_window
        self.response_handler = response_handler

        self.state: ConversationState = ConversationState.DISABLED
        self._running: bool = False
        self._active_stream: Optional[object] = None
        self._last_interaction_time: float = 0.0
        self._interrupted: bool = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start continuous listener in wake-word standby."""
        with self._lock:
            self._running = True
            self.state = ConversationState.STANDBY
            self._last_interaction_time = time.time()
            self._interrupted = False
            self.endpoint_detector.reset()

    def stop(self) -> None:
        """Completely shut down continuous listener and release audio resources."""
        with self._lock:
            self._running = False
            self.state = ConversationState.STOPPED
            self.recorder.reset()
            self.endpoint_detector.reset()

    def mute(self) -> None:
        """Mute the microphone, disabling further automatic voice processing."""
        with self._lock:
            self.state = ConversationState.MUTED
            self.recorder.reset()

    def is_interruption_command(self, text: str) -> bool:
        """Check if recognized phrase is an explicit cancellation/interruption command."""
        cleaned = text.strip().lower()
        interruption_keywords = [
            "stop",
            "cancel",
            "wait",
            "shutup",
            "shut up",
            "chup",
            "ruk",
            "ruko",
            "bas",
        ]
        return any(cleaned == kw or cleaned.startswith(f"{kw} ") for kw in interruption_keywords)

    def is_session_end_command(self, text: str) -> bool:
        """Check if recognized phrase requests ending continuous conversational session."""
        cleaned = text.strip().lower()
        return cleaned in [
            "goodbye",
            "goodbye friday",
            "bye friday",
            "alvida",
            "alvida friday",
            "exit conversation",
        ]

    def is_mic_shutdown_command(self, text: str) -> bool:
        """Check if recognized phrase requests completely stopping microphone monitoring."""
        cleaned = text.strip().lower()
        return cleaned in [
            "stop listening",
            "mute microphone",
            "turn off mic",
            "mic band karo",
            "stop listening friday",
        ]

    def handle_audio_frame(self, pcm_chunk: bytes) -> Optional[str]:
        """Process an audio frame according to the current conversation state."""
        with self._lock:
            if not self._running or self.state in (ConversationState.DISABLED, ConversationState.MUTED, ConversationState.STOPPED):
                return None

            now = time.time()

            # 1. STANDBY: Listen for wake word 'Hey Friday'
            if self.state == ConversationState.STANDBY:
                event = self.wake_engine.process_frame(pcm_chunk)
                if event is not None:
                    self.state = ConversationState.LISTENING
                    self._last_interaction_time = now
                    self.recorder.reset()
                    self.endpoint_detector.reset()
                    return f"Wake-word '{event.phrase}' detected. Listening for command..."
                return None

            # 2. FOLLOW_UP / LISTENING / RECORDING: VAD and speech capture
            if self.state in (ConversationState.LISTENING, ConversationState.FOLLOW_UP, ConversationState.RECORDING):
                # Check for session timeout
                if (now - self._last_interaction_time) > self.session_timeout:
                    self.state = ConversationState.STANDBY
                    self.recorder.reset()
                    self.endpoint_detector.reset()
                    return "Session timed out. Returning to wake-word standby."

                # Append chunk to recorder
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

                    result = self.stt_engine.transcribe_pcm16(raw_audio)
                    text = result.text.strip()

                    if not text:
                        self.state = ConversationState.FOLLOW_UP
                        return None

                    # Check for explicit microphone shutdown
                    if self.is_mic_shutdown_command(text):
                        self.stop()
                        return "Microphone monitoring stopped. Say or press a key to restart."

                    # Check for session goodbye
                    if self.is_session_end_command(text):
                        self.state = ConversationState.STANDBY
                        return "Goodbye! Returning to wake-word standby."

                    # Check for interruption command
                    if self.is_interruption_command(text):
                        self._interrupted = True
                        self.state = ConversationState.INTERRUPTED
                        return "Interrupted active response."

                    # Normal command execution
                    self.state = ConversationState.THINKING
                    response = ""
                    if self.response_handler:
                        response = self.response_handler(text)

                    self.state = ConversationState.FOLLOW_UP
                    self._last_interaction_time = time.time()
                    return response

            return None
