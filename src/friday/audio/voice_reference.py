"""Voice reference audio validation, preprocessing, and conditioning module.

Enforces:
- File integrity and format verification (RIFF WAV, PCM16).
- Duration bounds (2.0s to 30.0s).
- Signal level metrics (RMS volume, peak amplitude, clipping detection).
- Secure local non-tracked reference directory resolution.
- Zero cloud transmission and strict privacy enforcement.
"""

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import wave

from friday.audio.processing import calculate_rms_and_peak

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VoiceReferenceValidation:
    """Validation result for an audio reference file."""
    is_valid: bool
    path: str
    duration_s: float
    sample_rate: int
    channels: int
    rms: float
    peak: float
    clipped: bool
    error: str = ""


class VoiceReferenceValidator:
    """Validates local voice reference audio for conditioning and tuning."""

    MIN_DURATION_S: float = 2.0
    MAX_DURATION_S: float = 30.0
    MAX_FILE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB limit

    @staticmethod
    def get_default_voices_dir() -> Path:
        """Resolve private, local user voice directory outside git repository."""
        base = Path.home() / "Library" / "Application Support" / "Friday" / "voices"
        base.mkdir(parents=True, exist_ok=True)
        return base

    def validate_file(self, file_path: str) -> VoiceReferenceValidation:
        """Validate an audio reference file without modifying original content."""
        if not file_path or not os.path.exists(file_path):
            return VoiceReferenceValidation(
                is_valid=False,
                path=file_path or "",
                duration_s=0.0,
                sample_rate=0,
                channels=0,
                rms=0.0,
                peak=0.0,
                clipped=False,
                error="Reference file does not exist.",
            )

        try:
            stat = os.stat(file_path)
            if stat.st_size > self.MAX_FILE_SIZE_BYTES:
                return VoiceReferenceValidation(
                    is_valid=False,
                    path=file_path,
                    duration_s=0.0,
                    sample_rate=0,
                    channels=0,
                    rms=0.0,
                    peak=0.0,
                    clipped=False,
                    error=f"File exceeds maximum size of {self.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
                )

            with wave.open(file_path, "rb") as wf:
                channels = wf.getnchannels()
                sample_rate = wf.getframerate()
                sample_width = wf.getsampwidth()
                n_frames = wf.getnframes()
                duration_s = n_frames / float(sample_rate) if sample_rate > 0 else 0.0

                if sample_width != 2:
                    return VoiceReferenceValidation(
                        is_valid=False,
                        path=file_path,
                        duration_s=round(duration_s, 2),
                        sample_rate=sample_rate,
                        channels=channels,
                        rms=0.0,
                        peak=0.0,
                        clipped=False,
                        error="Audio must be 16-bit PCM format.",
                    )

                if duration_s < self.MIN_DURATION_S or duration_s > self.MAX_DURATION_S:
                    return VoiceReferenceValidation(
                        is_valid=False,
                        path=file_path,
                        duration_s=round(duration_s, 2),
                        sample_rate=sample_rate,
                        channels=channels,
                        rms=0.0,
                        peak=0.0,
                        clipped=False,
                        error=f"Duration {round(duration_s, 1)}s outside allowed bounds ({self.MIN_DURATION_S}s - {self.MAX_DURATION_S}s).",
                    )

                raw_frames = wf.readframes(min(n_frames, 16000 * 5))  # inspect up to 5s of audio
                rms, peak, clipped = calculate_rms_and_peak(raw_frames)

                if rms < 0.005:
                    return VoiceReferenceValidation(
                        is_valid=False,
                        path=file_path,
                        duration_s=round(duration_s, 2),
                        sample_rate=sample_rate,
                        channels=channels,
                        rms=rms,
                        peak=peak,
                        clipped=clipped,
                        error="Reference audio signal is too silent or empty.",
                    )

                return VoiceReferenceValidation(
                    is_valid=True,
                    path=file_path,
                    duration_s=round(duration_s, 2),
                    sample_rate=sample_rate,
                    channels=channels,
                    rms=rms,
                    peak=peak,
                    clipped=clipped,
                )

        except wave.Error as e:
            return VoiceReferenceValidation(
                is_valid=False,
                path=file_path,
                duration_s=0.0,
                sample_rate=0,
                channels=0,
                rms=0.0,
                peak=0.0,
                clipped=False,
                error=f"Invalid WAV file header: {e}",
            )
        except Exception as e:
            return VoiceReferenceValidation(
                is_valid=False,
                path=file_path,
                duration_s=0.0,
                sample_rate=0,
                channels=0,
                rms=0.0,
                peak=0.0,
                clipped=False,
                error=f"Reference validation error: {e}",
            )
