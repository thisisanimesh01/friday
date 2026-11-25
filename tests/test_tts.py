from unittest.mock import MagicMock, patch

from friday.audio.playback import PlaybackManager
from friday.audio.session import ContinuousListener, ConversationState
from friday.audio.tts import TTSEngine, Voice, prepare_speech_text


def test_prepare_speech_text():
    # 1. Code blocks and inline code
    markdown_text = (
        "# System Status\n"
        "Here is the code:\n"
        "```python\nprint('hello')\n```\n"
        "Use the `ls` command or visit https://example.com for info."
    )
    cleaned = prepare_speech_text(markdown_text)
    assert "[code block omitted]" in cleaned
    assert "print('hello')" not in cleaned
    assert "ls command" in cleaned
    assert "https://example.com" not in cleaned
    assert "link" in cleaned
    assert "#" not in cleaned


def test_tts_engine_defaults_and_availability():
    engine = TTSEngine(voice="Samantha", rate=185)
    assert engine.voice == "Samantha"
    assert engine.rate == 185
    assert engine.engine_type == "native"


def test_tts_engine_hindi_voice_selection():
    engine = TTSEngine(voice="Samantha")
    # Mock list_voices returning Lekha and Samantha
    with patch.object(
        engine,
        "list_voices",
        return_value=[
            Voice(name="Samantha", locale="en_US", example="Hello!"),
            Voice(name="Lekha", locale="hi_IN", example="नमस्ते!"),
        ],
    ):
        # English text keeps default voice
        assert engine.select_voice_for_text("Hello world") == "Samantha"
        # Hindi Devanagari text triggers Lekha
        assert engine.select_voice_for_text("नमस्ते, आप कैसे हैं?") == "Lekha"


def test_tts_mocked_speak_execution():
    engine = TTSEngine()
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.wait.return_value = 0

    with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
        success = engine.speak("Hello Friday")
        assert success is True
        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]
        assert cmd[0].endswith("say")
        assert "Hello Friday" in cmd


def test_playback_manager_microphone_gating():
    tts_engine = TTSEngine()
    manager = PlaybackManager(tts_engine=tts_engine)
    listener = ContinuousListener()
    listener.start()
    assert listener.state == ConversationState.STANDBY

    with patch.object(tts_engine, "speak", return_value=True):
        # speak() should gate microphone listener during speech and restore afterward
        success = manager.speak("Response text", listener=listener)
        assert success is True
        assert listener.state == ConversationState.STANDBY
