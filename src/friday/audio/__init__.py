"""Audio package root for Friday."""

from friday.audio.config import AudioConfig, DEFAULT_AUDIO_CONFIG
from friday.audio.devices import AudioDevice, get_default_microphone, list_microphones
from friday.audio.processing import calculate_rms_and_peak, pcm16_to_wav_bytes
from friday.audio.recorder import AudioRecorder
from friday.audio.playback import PlaybackManager
from friday.audio.conversation import HandsFreeController
from friday.audio.session import ContinuousListener, ConversationState
from friday.audio.expression import EXPRESSION_PROFILES, ExpressionTuning, SpeechExpression, select_expression_for_context
from friday.audio.speech_segmenter import SpeechSegmenter
from friday.audio.streaming_tts import StreamingTTSCoordinator
from friday.audio.stt import TranscriptionResult, WhisperEngine
from friday.audio.tts import TTSEngine, Voice, prepare_speech_text
from friday.audio.vad import SpeechEndpointDetector, VADDecision, VoiceActivityDetector
from friday.audio.voice_profile import VoiceProfile, VoiceRegistry
from friday.audio.voice_reference import VoiceReferenceValidation, VoiceReferenceValidator
from friday.audio.voice_manager import VoiceManager, VoiceSystemStatus
from friday.audio.engines.neural import NeuralTTSEngine
from friday.audio.engines.native import NativeTTSEngine
from friday.audio.wake_word import ListenerState, WakeWordEngine, WakeWordEvent, WakeWordListener

__all__ = [
    "AudioConfig",
    "AudioDevice",
    "AudioRecorder",
    "ContinuousListener",
    "ConversationState",
    "DEFAULT_AUDIO_CONFIG",
    "EXPRESSION_PROFILES",
    "ExpressionTuning",
    "HandsFreeController",
    "ListenerState",
    "PlaybackManager",
    "SpeechEndpointDetector",
    "SpeechExpression",
    "SpeechSegmenter",
    "StreamingTTSCoordinator",
    "TTSEngine",
    "TranscriptionResult",
    "VADDecision",
    "Voice",
    "VoiceActivityDetector",
    "VoiceProfile",
    "VoiceReferenceValidation",
    "VoiceReferenceValidator",
    "VoiceRegistry",
    "VoiceManager",
    "VoiceSystemStatus",
    "NeuralTTSEngine",
    "NativeTTSEngine",
    "WakeWordEngine",
    "WakeWordEvent",
    "WakeWordListener",
    "WhisperEngine",
    "calculate_rms_and_peak",
    "get_default_microphone",
    "list_microphones",
    "pcm16_to_wav_bytes",
    "prepare_speech_text",
    "select_expression_for_context",
]
