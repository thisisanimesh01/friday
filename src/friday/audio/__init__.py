"""Audio package root for Friday."""

from friday.audio.config import AudioConfig, DEFAULT_AUDIO_CONFIG
from friday.audio.devices import AudioDevice, get_default_microphone, list_microphones
from friday.audio.processing import calculate_rms_and_peak, pcm16_to_wav_bytes
from friday.audio.recorder import AudioRecorder
from friday.audio.stt import TranscriptionResult, WhisperEngine
from friday.audio.wake_word import ListenerState, WakeWordEngine, WakeWordEvent, WakeWordListener

__all__ = [
    "AudioConfig",
    "AudioDevice",
    "AudioRecorder",
    "DEFAULT_AUDIO_CONFIG",
    "ListenerState",
    "TranscriptionResult",
    "WakeWordEngine",
    "WakeWordEvent",
    "WakeWordListener",
    "WhisperEngine",
    "calculate_rms_and_peak",
    "get_default_microphone",
    "list_microphones",
    "pcm16_to_wav_bytes",
]
