from friday.audio.session import ContinuousListener, ConversationState
from friday.audio.vad import SpeechEndpointDetector, VoiceActivityDetector
from friday.audio.wake_word import WakeWordEngine


def test_vad_silence_and_speech():
    vad = VoiceActivityDetector(sensitivity=0.5)

    # 1. Complete silence
    silent_chunk = b"\x00\x00" * 320
    decision_silent = vad.is_speech(silent_chunk)
    assert not decision_silent.is_speech
    assert decision_silent.energy == 0.0

    # 2. Simulated high amplitude speech PCM
    loud_sample = b"\x50\x20" * 320
    decision_loud = vad.is_speech(loud_sample)
    assert decision_loud.is_speech
    assert decision_loud.energy > 0.01


def test_speech_endpoint_detection():
    detector = SpeechEndpointDetector(min_speech_duration_ms=100, speech_end_silence_ms=200)

    # Inactive initially
    in_prog, completed = detector.process_chunk(b"\x00\x00" * 320)
    assert not in_prog
    assert not completed

    # Speech starts
    loud_sample = b"\x50\x20" * 320
    in_prog, completed = detector.process_chunk(loud_sample)
    assert in_prog
    assert not completed
    assert detector.speech_started


def test_continuous_listener_lifecycle():
    engine = WakeWordEngine()
    listener = ContinuousListener(wake_engine=engine, session_timeout=5.0)

    assert listener.state == ConversationState.DISABLED
    listener.start()
    assert listener.state == ConversationState.STANDBY

    # Test interruption keywords
    assert listener.is_interruption_command("stop")
    assert listener.is_interruption_command("cancel")
    assert listener.is_interruption_command("wait")
    assert listener.is_interruption_command("ruk jao")
    assert not listener.is_interruption_command("what is the weather")

    # Test session end keywords
    assert listener.is_session_end_command("goodbye friday")
    assert listener.is_session_end_command("alvida")
    assert not listener.is_session_end_command("hello")

    # Test mic shutdown keywords
    assert listener.is_mic_shutdown_command("stop listening")
    assert listener.is_mic_shutdown_command("turn off mic")

    listener.stop()
    assert listener.state == ConversationState.STOPPED
