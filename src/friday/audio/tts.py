"""Local Text-to-Speech (TTS) synthesis and voice management.

Provides a safe, local, zero-cloud speech synthesis interface supporting
native macOS speech synthesis (`say`) with parameter sanitization, voice
enumeration, language auto-selection, and text preprocessing.
"""

from dataclasses import dataclass
import logging
import os
import re
import shutil
import subprocess
import tempfile
import threading
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Voice:
    """Represents a speech synthesis voice."""
    name: str
    locale: str
    example: str


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
    """Pluggable local speech synthesis engine."""

    def __init__(
        self,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        engine_type: Optional[str] = None,
    ):
        self.engine_type = engine_type or os.getenv("TTS_ENGINE", "native")
        self.voice = voice or os.getenv("TTS_VOICE", "Samantha")
        # Default rate: 175-190 wpm for calm, clear articulation
        self.rate = int(rate if rate is not None else os.getenv("TTS_RATE", "185"))
        self._say_bin = shutil.which("say")
        self._active_proc: Optional[subprocess.Popen[bytes]] = None
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        """Return True if local speech synthesis backend is available."""
        if self.engine_type == "native":
            return bool(self._say_bin and os.path.exists(self._say_bin))
        return False

    def list_voices(self) -> list[Voice]:
        """List available local voices."""
        if not self._say_bin:
            return []

        voices: list[Voice] = []
        try:
            res = subprocess.run(
                [self._say_bin, "-v", "?"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            for line in res.stdout.splitlines():
                if "#" in line:
                    parts = line.split("#")
                    meta = parts[0].strip().split()
                    example = parts[1].strip()
                    if len(meta) >= 2:
                        locale = meta[-1]
                        name = " ".join(meta[:-1])
                        voices.append(Voice(name=name, locale=locale, example=example))
        except Exception as e:
            logger.warning(f"Failed to list voices: {e}")
        return voices

    def select_voice_for_text(self, text: str) -> str:
        """Auto-select Hindi or English voice based on text script."""
        # Detect Devanagari Unicode range (\u0900-\u097F)
        has_devanagari = any("\u0900" <= ch <= "\u097F" for ch in text)
        if has_devanagari:
            # Check if Lekha is available
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

        target_voice = voice or self.select_voice_for_text(cleaned)
        target_rate = rate or self.rate

        # Subprocess execution using securely passed arguments (no shell=True)
        cmd = [self._say_bin, "-v", target_voice, "-r", str(target_rate), cleaned]

        with self._lock:
            try:
                self._active_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                logger.error(f"Failed to execute TTS speech: {e}")
                return False

        try:
            self._active_proc.wait(timeout=float(os.getenv("TTS_TIMEOUT", "60")))
            return self._active_proc.returncode == 0
        except subprocess.TimeoutExpired:
            self.stop()
            return False
        finally:
            with self._lock:
                self._active_proc = None

    def stop(self) -> None:
        """Immediately cancel active speech synthesis and playback."""
        with self._lock:
            if self._active_proc and self._active_proc.poll() is None:
                try:
                    self._active_proc.terminate()
                    self._active_proc.wait(timeout=1.0)
                except Exception:
                    try:
                        self._active_proc.kill()
                    except Exception:
                        pass
                finally:
                    self._active_proc = None
