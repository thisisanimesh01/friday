"""Context-aware emotional expression delivery for FRIDAY.

Maps conversation intent and context to delivery styles:
- gentle: Soft, calm, warm, relaxed cadence (160 wpm, volume 0.9)
- happy: Cheerful, upbeat task completion (180 wpm, volume 1.0)
- focused: Clear, deliberate technical pacing (175 wpm, volume 1.0)
- concerned: Slower, careful cautionary pacing for warnings (150 wpm, volume 1.0)
- supportive: Empathetic, encouraging cadence (165 wpm, volume 0.95)
- neutral: Standard clear assistant delivery (185 wpm, volume 1.0)
- confident: Firm, articulate confirmation (180 wpm, volume 1.0)
"""

from dataclasses import dataclass
import enum
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class SpeechExpression(enum.Enum):
    """Delivery style presets for speech synthesis."""
    GENTLE = "gentle"
    HAPPY = "happy"
    FOCUSED = "focused"
    CONCERNED = "concerned"
    SUPPORTIVE = "supportive"
    NEUTRAL = "neutral"
    CONFIDENT = "confident"


@dataclass(frozen=True)
class ExpressionTuning:
    """Tuning parameters for a specific delivery expression."""
    expression: SpeechExpression
    rate_multiplier: float  # Scales base profile rate
    volume: float
    description: str


EXPRESSION_PROFILES: dict[SpeechExpression, ExpressionTuning] = {
    SpeechExpression.GENTLE: ExpressionTuning(
        expression=SpeechExpression.GENTLE,
        rate_multiplier=0.95,
        volume=0.9,
        description="Soft, calm, and reassuring feminine delivery with natural breathing pauses.",
    ),
    SpeechExpression.HAPPY: ExpressionTuning(
        expression=SpeechExpression.HAPPY,
        rate_multiplier=1.05,
        volume=1.0,
        description="Warm, upbeat, and pleased delivery for successful completions.",
    ),
    SpeechExpression.FOCUSED: ExpressionTuning(
        expression=SpeechExpression.FOCUSED,
        rate_multiplier=1.0,
        volume=1.0,
        description="Clear, steady, articulate delivery for technical explanations.",
    ),
    SpeechExpression.CONCERNED: ExpressionTuning(
        expression=SpeechExpression.CONCERNED,
        rate_multiplier=0.88,
        volume=1.0,
        description="Slower, deliberate pacing for caution and security confirmations.",
    ),
    SpeechExpression.SUPPORTIVE: ExpressionTuning(
        expression=SpeechExpression.SUPPORTIVE,
        rate_multiplier=0.95,
        volume=0.95,
        description="Encouraging, patient delivery when user seeks guidance or help.",
    ),
    SpeechExpression.NEUTRAL: ExpressionTuning(
        expression=SpeechExpression.NEUTRAL,
        rate_multiplier=1.0,
        volume=1.0,
        description="Standard clear assistant delivery.",
    ),
    SpeechExpression.CONFIDENT: ExpressionTuning(
        expression=SpeechExpression.CONFIDENT,
        rate_multiplier=1.02,
        volume=1.0,
        description="Firm, affirmative verification of completed commands.",
    ),
}


def select_expression_for_context(
    text: str,
    intent: Optional[str] = None,
    explicit_style: Optional[str] = None,
) -> ExpressionTuning:
    """Determine the appropriate delivery expression for the given response context."""
    if explicit_style:
        try:
            exp_enum = SpeechExpression(explicit_style.lower())
            return EXPRESSION_PROFILES[exp_enum]
        except ValueError:
            pass

    lower_text = text.lower()

    # 1. Caution / Destructive warning -> CONCERNED
    if any(k in lower_text for k in ["delete", "remove", "confirm", "warning", "caution", "danger", "khatra"]):
        return EXPRESSION_PROFILES[SpeechExpression.CONCERNED]

    # 2. Success / Completion -> HAPPY / CONFIDENT
    if any(k in lower_text for k in ["success", "completed", "done", "ready", "pass", "ho gaya"]):
        return EXPRESSION_PROFILES[SpeechExpression.HAPPY]

    # 3. Technical code or documentation -> FOCUSED
    if any(k in lower_text for k in ["def ", "class ", "return", "function", "variable", "code", "file"]):
        return EXPRESSION_PROFILES[SpeechExpression.FOCUSED]

    # 4. Gentle default for conversational assistance
    return EXPRESSION_PROFILES[SpeechExpression.GENTLE]
