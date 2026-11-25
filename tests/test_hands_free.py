from unittest.mock import MagicMock

from friday.audio.conversation import HandsFreeController
from friday.audio.session import ConversationState
from friday.audio.wake_word import WakeWordEvent


def test_hands_free_controller_lifecycle():
    mock_wake = MagicMock()
    mock_stt = MagicMock()
    mock_tts = MagicMock()

    controller = HandsFreeController(
        wake_engine=mock_wake,
        stt_engine=mock_stt,
        tts_engine=mock_tts,
        session_timeout=5.0,
    )

    assert controller.state == ConversationState.DISABLED
    controller.start()
    assert controller.state == ConversationState.STANDBY

    # Test barge in keyword checks
    assert controller.is_barge_in_phrase("stop")
    assert controller.is_barge_in_phrase("ruko")
    assert not controller.is_barge_in_phrase("how are you")

    # Test session end checks
    assert controller.is_session_end("goodbye friday")
    assert controller.is_session_end("alvida friday")

    # Test mic shutdown checks
    assert controller.is_mic_shutdown("stop listening")
    assert controller.is_mic_shutdown("turn off mic")

    controller.stop()
    assert controller.state == ConversationState.STOPPED


def test_hands_free_wake_word_transition():
    mock_wake = MagicMock()
    mock_wake.process_frame.return_value = WakeWordEvent(
        phrase="Hey Friday",
        confidence=0.9,
        timestamp=100.0,
        engine="builtin",
    )

    controller = HandsFreeController(wake_engine=mock_wake)
    controller.start()

    res = controller.handle_audio_frame(b"\x00\x00" * 320)
    assert res is not None
    assert "detected" in res
    assert controller.state == ConversationState.LISTENING


def test_hands_free_barge_in_during_playback():
    mock_tts = MagicMock()
    controller = HandsFreeController(tts_engine=mock_tts, enable_barge_in=True)
    controller.start()
    controller.state = ConversationState.RESPONDING

    # High amplitude speech frame interrupting playback
    loud_speech = b"\x50\x20" * 320
    res = controller.handle_audio_frame(loud_speech)
    assert res is not None
    assert "Interrupted" in res
    assert controller.state == ConversationState.INTERRUPTED
