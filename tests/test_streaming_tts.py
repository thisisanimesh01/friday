from unittest.mock import MagicMock, patch

from friday.audio.expression import (
    SpeechExpression,
    select_expression_for_context,
)
from friday.audio.speech_segmenter import SpeechSegmenter
from friday.audio.streaming_tts import StreamingTTSCoordinator


def test_speech_segmenter_sentence_splitting():
    segmenter = SpeechSegmenter(min_chars=15)

    # Add chunk without sentence boundary
    segs1 = segmenter.add_chunk("Hello there! ")
    assert len(segs1) == 0  # < 15 chars

    # Add next chunk with sentence boundary
    segs2 = segmenter.add_chunk("How can I assist your project today? ")
    assert len(segs2) >= 1
    assert "Hello there!" in segs2[0] or "How can I assist" in segs2[0]

    # Flush remaining buffer
    flushed = segmenter.flush()
    assert isinstance(flushed, list)


def test_speech_segmenter_devanagari_danda():
    segmenter = SpeechSegmenter(min_chars=10)
    segs = segmenter.add_chunk("नमस्ते, मैं फ्राइडे हूँ। ")
    assert len(segs) == 1
    assert "नमस्ते" in segs[0]


def test_expression_selection_rules():
    # Warning / caution -> CONCERNED
    exp_warn = select_expression_for_context("Warning: This operation will delete files.")
    assert exp_warn.expression == SpeechExpression.CONCERNED
    assert exp_warn.rate_multiplier < 1.0  # Slower deliberate pace

    # Success / ready -> HAPPY
    exp_happy = select_expression_for_context("Success! Your deployment is ready.")
    assert exp_happy.expression == SpeechExpression.HAPPY

    # Technical code -> FOCUSED
    exp_code = select_expression_for_context("The def process() function returns a dictionary.")
    assert exp_code.expression == SpeechExpression.FOCUSED

    # Default -> GENTLE
    exp_default = select_expression_for_context("I understand, let's talk about it.")
    assert exp_default.expression == SpeechExpression.GENTLE


def test_streaming_tts_coordinator_flow():
    mock_tts = MagicMock()
    mock_tts.speak.return_value = True

    coordinator = StreamingTTSCoordinator(tts_engine=mock_tts, min_segment_chars=10)
    tokens = ["Hello world. ", "This is a streaming ", "speech test response!"]

    streamed_out = list(coordinator.stream_and_speak(tokens))
    assert "".join(streamed_out) == "".join(tokens)
    assert mock_tts.speak.called
