"""Audio package root for Friday."""

from friday.audio.config import AudioConfig, DEFAULT_AUDIO_CONFIG
from friday.audio.devices import AudioDevice, get_default_microphone, list_microphones
from friday.audio.processing import calculate_rms_and_peak, pcm16_to_wav_bytes
from friday.audio.recorder import AudioRecorder
from friday.audio.playback import PlaybackManager
from friday.audio.session import ContinuousListener, ConversationState
from friday.audio.stt import TranscriptionResult, WhisperEngine
from friday.audio.tts import TTSEngine, Voice, prepare_speech_text
from friday.audio.vad import SpeechEndpointDetector, VADDecision, VoiceActivityDetector
from friday.audio.voice_profile import VoiceProfile, VoiceRegistry
from friday.audio.voice_reference import VoiceReferenceValidation, VoiceReferenceValidator
from friday.audio.wake_word import ListenerState, WakeWordEngine, WakeWordEvent, WakeWordListener

__all__ = [
    "AudioConfig",
    "AudioDevice",
    "AudioRecorder",
    "ContinuousListener",
    "ConversationState",
    "DEFAULT_AUDIO_CONFIG",
    "ListenerState",
    "PlaybackManager",
    "SpeechEndpointDetector",
    "TTSEngine",
    "TranscriptionResult",
    "VADDecision",
    "Voice",
    "VoiceActivityDetector",
    "VoiceProfile",
    "VoiceReferenceValidation",
    "VoiceReferenceValidator",
    "VoiceRegistry",
    "WakeWordEngine",
    "WakeWordEvent",
    "WakeWordListener",
    "WhisperEngine",
    "calculate_rms_and_peak",
    "get_default_microphone",
    "list_microphones",
    "pcm16_to_wav_bytes",
    "prepare_speech_text",
]
