"""Audio input device enumeration and capability detection."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AudioDevice:
    index: int
    name: str
    max_input_channels: int
    default_sample_rate: float
    is_default: bool


def list_microphones() -> list[AudioDevice]:
    """List available audio input devices.

    Returns empty list if sounddevice or PortAudio is not installed or available.
    """
    try:
        import sounddevice as sd  # type: ignore[import-untyped]
    except (ImportError, OSError):
        return []

    try:
        devices: list[dict[str, Any]] = sd.query_devices()
        default_in = sd.default.device[0] if sd.default.device else None
        mics: list[AudioDevice] = []
        for idx, dev in enumerate(devices):
            channels = int(dev.get("max_input_channels", 0))
            if channels > 0:
                mics.append(
                    AudioDevice(
                        index=idx,
                        name=str(dev.get("name", f"Microphone {idx}")),
                        max_input_channels=channels,
                        default_sample_rate=float(dev.get("default_samplerate", 16000.0)),
                        is_default=(idx == default_in),
                    )
                )
        return mics
    except Exception:
        return []


def get_default_microphone() -> AudioDevice | None:
    mics = list_microphones()
    for m in mics:
        if m.is_default:
            return m
    return mics[0] if mics else None
