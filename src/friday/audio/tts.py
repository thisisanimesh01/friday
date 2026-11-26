"""Local Text-to-Speech (TTS) synthesis and voice management.

Provides a safe, local, zero-cloud speech synthesis interface supporting:
- Neural TTS (Kokoro-82M ONNX with conditioned Hinata voice) as primary default.
- Native macOS speech synthesis (`say`) as explicit fallback.
- Sanitization, parameter normalization, and text preprocessing.
"""

from dataclasses import dataclass
import logging
import os
import re
import shutil
import subprocess
import threading
from typing import Optional

from friday.audio.engines.native import NativeTTSEngine, Voice
from friday.audio.engines.neural import NeuralTTSEngine
from friday.audio.voice_manager import VoiceManager

logger = logging.getLogger(__name__)


def prepare_speech_text(text: str) -> str:
    """Clean markdown, code blocks, URLs, and excess whitespace for natural speech synthesis."""
    if not text:
        return ""

    # 1. Remove markdown code blocks ``` ... ```
    cleaned = re.sub(r"```[\s\S]*?```", " [code block omitted] ", text)

    # 2. Remove inline code `...`
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)

    # 3. Replace URLs with readable placeholder
    cleaned = re.sub(r"https?://\S+", "link", cleaned)

    # 4. Remove markdown headers, bold, italics, bullets
    cleaned = re.sub(r"^#{1,6}\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"[*_~]{1,3}", "", cleaned)
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)

    # 5. Collapse excessive whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class TTSEngine:
    """Pluggable local speech synthesis engine prioritizing Neural Hinata voice."""

    def __init__(
        self,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        engine_type: Optional[str] = None,
    ):
        self.engine_type = engine_type or os.getenv("TTS_ENGINE", "neural")
        # Default voice is now hinata
        self.voice = voice or os.getenv("TTS_VOICE", "hinata")
        self.rate = int(rate if rate is not None else os.getenv("TTS_RATE", "165"))

        self.native_engine = NativeTTSEngine(voice="Samantha", rate=self.rate)
        self.neural_engine = NeuralTTSEngine()
        self.voice_manager = VoiceManager(
            neural_engine=self.neural_engine,
            native_engine=self.native_engine,
        )

        self._say_bin = shutil.which("say")
        self._active_proc: Optional[subprocess.Popen[bytes]] = None
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        """Return True if local speech synthesis backend is available."""
        if self.engine_type == "neural":
            return self.neural_engine.is_available() or self.native_engine.is_available()
        return self.native_engine.is_available()

    def list_voices(self) -> list[Voice]:
        """List available local voices across neural and native engines."""
        return self.voice_manager.list_voices()

    def select_voice_for_text(self, text: str) -> str:
        """Auto-select Hindi or English voice based on text script."""
        has_devanagari = any("\u0900" <= ch <= "\u097F" for ch in text)
        if has_devanagari:
            installed = {v.name.lower(): v.name for v in self.list_voices()}
            if "lekha" in installed:
                return installed["lekha"]
        return self.voice

    def speak(self, text: str, voice: Optional[str] = None, rate: Optional[int] = None) -> bool:
        """Synthesize and speak text locally without cloud requests."""
        cleaned = prepare_speech_text(text)
        if not cleaned:
            return False

        if not self.is_available():
            logger.error("TTS engine is unavailable.")
            return False

        target_voice = voice or self.voice
        target_rate = rate or self.rate

        # If user explicitly requested Samantha or native say, use native
        if target_voice.lower() in ("samantha", "lekha") or self.engine_type == "native":
            return self.native_engine.speak(cleaned, voice=target_voice, rate=target_rate)

        # Primary neural voice synthesis with automatic fallback
        return self.voice_manager.speak(cleaned, voice=target_voice, rate=target_rate)

    def stop(self) -> None:
        """Immediately cancel active speech synthesis and playback."""
        self.voice_manager.stop()
