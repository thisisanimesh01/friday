"""Local Speech-to-Text (STT) interface and Whisper engine integration.

Supports local transcription using whisper.cpp (CLI/dylib) or faster-whisper/whisper,
processing 16kHz mono PCM16 audio without cloud transmission.
"""

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Optional

from friday.audio.processing import pcm16_to_wav_bytes


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    duration_s: float
    confidence: float = 1.0


class WhisperEngine:
    """Lightweight, offline local speech recognition engine."""

    def __init__(
        self,
        model_name: str = "base",
        model_path: Optional[str] = None,
        language: str = "auto",
        binary_path: Optional[str] = None,
    ):
        self.model_name = model_name
        self.model_path = model_path or os.getenv("STT_MODEL_PATH")
        self.language = language or os.getenv("STT_LANGUAGE", "auto")
        self.binary_path = binary_path or os.getenv("STT_BINARY_PATH") or shutil.which("whisper-cli") or shutil.which("whisper")

    def is_available(self) -> bool:
        """Return True if local speech recognition engine and model are available."""
        if self.binary_path and os.path.exists(self.binary_path):
            if self.model_path and os.path.exists(self.model_path):
                return True
        # Check for Python whisper package as fallback
        try:
            import whisper  # type: ignore[import-untyped]
            return True
        except ImportError:
            pass
        return False

    def transcribe_pcm16(self, pcm_bytes: bytes, sample_rate: int = 16000) -> TranscriptionResult:
        """Transcribe raw 16kHz mono PCM16 bytes locally."""
        if not pcm_bytes:
            return TranscriptionResult(text="", language=self.language, duration_s=0.0)

        duration = len(pcm_bytes) / (sample_rate * 2)

        # 1. Try local whisper-cli binary if configured
        if self.binary_path and self.model_path and os.path.exists(self.model_path):
            return self._transcribe_subprocess(pcm_bytes, sample_rate, duration)

        # 2. Try Python whisper package if installed
        try:
            import whisper

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
                wav_data = pcm16_to_wav_bytes(pcm_bytes, sample_rate=sample_rate)
                tmp.write(wav_data)

            try:
                model = whisper.load_model(self.model_name)
                kwargs = {}
                if self.language and self.language != "auto":
                    kwargs["language"] = self.language
                result = model.transcribe(tmp_path, **kwargs)
                return TranscriptionResult(
                    text=result.get("text", "").strip(),
                    language=result.get("language", self.language),
                    duration_s=round(duration, 2),
                )
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except ImportError:
            pass

        # Engine not configured/available
        return TranscriptionResult(
            text="[Local STT engine not configured. Install whisper or configure STT_MODEL_PATH.]",
            language=self.language,
            duration_s=round(duration, 2),
            confidence=0.0,
        )

    def _transcribe_subprocess(self, pcm_bytes: bytes, sample_rate: int, duration: float) -> TranscriptionResult:
        """Execute local whisper-cli securely without shell interpolation."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            wav_data = pcm16_to_wav_bytes(pcm_bytes, sample_rate=sample_rate)
            tmp.write(wav_data)

        try:
            cmd = [
                str(self.binary_path),
                "-m", str(self.model_path),
                "-f", tmp_path,
                "--no-timestamps",
            ]
            if self.language and self.language != "auto":
                cmd.extend(["-l", self.language])

            res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            text = res.stdout.strip()
            return TranscriptionResult(
                text=text,
                language=self.language,
                duration_s=round(duration, 2),
            )
        except Exception:
            return TranscriptionResult(
                text="",
                language=self.language,
                duration_s=round(duration, 2),
                confidence=0.0,
            )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
