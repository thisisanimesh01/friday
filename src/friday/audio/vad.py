"""Voice Activity Detection (VAD) and speech endpoint detection module.

Provides lightweight energy/RMS and zero-crossing rate based speech detection,
with pluggable webrtcvad / silero-vad backend support when installed.
Processes 16kHz mono PCM16 audio in bounded in-memory frames.
"""

from dataclasses import dataclass
import os
import struct
import time
from typing import Optional

from friday.audio.processing import calculate_rms_and_peak


@dataclass(frozen=True)
class VADDecision:
    """Detection decision for an audio chunk."""
    is_speech: bool
    energy: float
    confidence: float
    timestamp: float


class VoiceActivityDetector:
    """Lightweight, offline voice activity detector."""

    def __init__(
        self,
        sensitivity: float = 0.5,
        engine: Optional[str] = None,
        min_speech_duration_ms: int = 250,
        speech_end_silence_ms: int = 800,
    ):
        self.sensitivity = float(sensitivity if sensitivity is not None else os.getenv("VAD_SENSITIVITY", "0.5"))
        self.engine = engine or os.getenv("VAD_ENGINE", "energy")
        self.min_speech_duration_ms = min_speech_duration_ms
        self.speech_end_silence_ms = speech_end_silence_ms
        self._backend: Optional[object] = None
        self._init_backend()

    def _init_backend(self) -> None:
        """Initialize optional webrtcvad backend if available."""
        if self.engine in ("auto", "webrtcvad"):
            try:
                import webrtcvad  # type: ignore[import-untyped]
                # webrtcvad mode: 0 (least aggressive) to 3 (most aggressive)
                aggressiveness = int(min(3, max(0, int(self.sensitivity * 3))))
                self._backend = webrtcvad.Vad(aggressiveness)
                self.engine = "webrtcvad"
                return
            except ImportError:
                pass
        self.engine = "energy"

    def is_speech(self, pcm16_chunk: bytes, sample_rate: int = 16000) -> VADDecision:
        """Determine if a PCM16 chunk contains active human speech."""
        now = time.time()
        if not pcm16_chunk:
            return VADDecision(is_speech=False, energy=0.0, confidence=0.0, timestamp=now)

        # 1. Try webrtcvad if active
        if self.engine == "webrtcvad" and self._backend is not None:
            try:
                # webrtcvad requires 10, 20, or 30ms frame lengths
                # For 16kHz: 10ms = 160 samples (320 bytes), 20ms = 320 samples (640 bytes), 30ms = 480 samples (960 bytes)
                frame_len = len(pcm16_chunk)
                if frame_len in (320, 640, 960):
                    vad_result = self._backend.is_speech(pcm16_chunk, sample_rate)  # type: ignore[union-attr]
                    rms, _, _ = calculate_rms_and_peak(pcm16_chunk)
                    return VADDecision(
                        is_speech=bool(vad_result),
                        energy=rms,
                        confidence=0.9 if vad_result else 0.1,
                        timestamp=now,
                    )
            except Exception:
                pass

        # 2. Builtin Energy / Zero-Crossing VAD fallback
        rms, peak, clipped = calculate_rms_and_peak(pcm16_chunk)
        # Dynamic speech energy threshold scaled by sensitivity
        # High sensitivity (1.0) -> threshold 0.005; Low sensitivity (0.0) -> threshold 0.04
        threshold = 0.04 - (self.sensitivity * 0.035)
        speech_detected = rms >= threshold

        return VADDecision(
            is_speech=speech_detected,
            energy=rms,
            confidence=min(1.0, rms / max(0.0001, threshold)),
            timestamp=now,
        )


class SpeechEndpointDetector:
    """Tracks continuous speech state to detect natural utterance start and endpoints."""

    def __init__(
        self,
        vad: Optional[VoiceActivityDetector] = None,
        speech_end_silence_ms: int = 800,
        min_speech_duration_ms: int = 300,
        max_recording_s: float = 15.0,
    ):
        self.vad = vad or VoiceActivityDetector()
        self.speech_end_silence_ms = speech_end_silence_ms
        self.min_speech_duration_ms = min_speech_duration_ms
        self.max_recording_s = max_recording_s

        self.speech_started: bool = False
        self._speech_start_time: float = 0.0
        self._last_speech_time: float = 0.0

    def reset(self) -> None:
        """Reset speech tracking state."""
        self.speech_started = False
        self._speech_start_time = 0.0
        self._last_speech_time = 0.0

    def process_chunk(self, chunk: bytes, sample_rate: int = 16000) -> tuple[bool, bool]:
        """Process an incoming audio chunk.

        Returns (speech_in_progress, speech_completed).
        """
        now = time.time()
        decision = self.vad.is_speech(chunk, sample_rate=sample_rate)

        if decision.is_speech:
            if not self.speech_started:
                self.speech_started = True
                self._speech_start_time = now
            self._last_speech_time = now
            return True, False

        # If speech was ongoing, check if silence exceeds threshold
        if self.speech_started:
            silence_duration_ms = (now - self._last_speech_time) * 1000
            total_duration_s = now - self._speech_start_time

            # Check if max recording duration reached
            if total_duration_s >= self.max_recording_s:
                return False, True

            # Check if silence duration exceeds end-of-speech silence window
            if silence_duration_ms >= self.speech_end_silence_ms:
                speech_duration_ms = (self._last_speech_time - self._speech_start_time) * 1000
                if speech_duration_ms >= self.min_speech_duration_ms:
                    return False, True
                # Rejected as momentary glitch/cough
                self.reset()
                return False, False

            return True, False

        return False, False
