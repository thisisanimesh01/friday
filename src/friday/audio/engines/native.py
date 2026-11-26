"""Native macOS speech synthesis engine (`say`).

Serves as an explicitly declared emergency fallback when neural models are unavailable.
Zero cloud network calls, CoreAudio daemon-backed.
"""

from dataclasses import dataclass
import logging
import os
import shutil
import subprocess
import threading
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Voice:
    """Represents a speech synthesis voice."""
    name: str
    locale: str
    example: str


class NativeTTSEngine:
    """Explicit macOS native speech synthesis fallback engine."""

    def __init__(
        self,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
    ):
        self.voice = voice or os.getenv("TTS_VOICE", "Samantha")
        self.rate = int(rate if rate is not None else os.getenv("TTS_RATE", "185"))
        self._say_bin = shutil.which("say")
        self._active_proc: Optional[subprocess.Popen[bytes]] = None
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        """Return True if macOS `say` binary is present."""
        return bool(self._say_bin and os.path.exists(self._say_bin))

    def list_voices(self) -> list[Voice]:
        """List available local macOS voices."""
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
            logger.warning(f"Failed to list native voices: {e}")
        return voices

    def select_voice_for_text(self, text: str) -> str:
        """Auto-select Hindi or English voice based on text script."""
        has_devanagari = any("\u0900" <= ch <= "\u097F" for ch in text)
        if has_devanagari:
            installed = {v.name.lower(): v.name for v in self.list_voices()}
            if "lekha" in installed:
                return installed["lekha"]
        return self.voice

    def speak(self, text: str, voice: Optional[str] = None, rate: Optional[int] = None) -> bool:
        """Speak text using macOS `say`."""
        if not self.is_available():
            logger.error("Native TTS engine is unavailable.")
            return False

        target_voice = voice or self.select_voice_for_text(text)
        target_rate = rate or self.rate

        cmd = [self._say_bin, "-v", target_voice, "-r", str(target_rate), text]

        with self._lock:
            try:
                self._active_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                logger.error(f"Failed to execute native TTS speech: {e}")
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
        """Immediately stop native speech playback."""
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
