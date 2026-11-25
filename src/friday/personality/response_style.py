"""Response style formatting, honest action acknowledgements, and terminal sanitization.

Ensures:
- Honest state separation (received, pending, confirming, executing, succeeded, failed, cancelled)
- Mapping to speech synthesis expressions (SpeechExpression from friday.audio.expression)
- Terminal presentation (plain text fallback, NO_COLOR compliance, sanitized escape sequences)
"""

import enum
import os
import re
from typing import Optional

try:
    from friday.audio.expression import SpeechExpression
except ImportError:
    # Audio optional dependency fallback
    class SpeechExpression(enum.Enum):  # type: ignore[no-redef]
        GENTLE = "gentle"
        HAPPY = "happy"
        FOCUSED = "focused"
        CONCERNED = "concerned"
        SUPPORTIVE = "supportive"
        NEUTRAL = "neutral"
        CONFIDENT = "confident"


class ResponseStyle(enum.Enum):
    """Contextual conversational response styles."""
    GREETING = "greeting"
    TECHNICAL = "technical"
    TASK_ACK = "task_ack"
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    SECURITY_WARNING = "security_warning"
    SUPPORTIVE = "supportive"
    CASUAL = "casual"
    CONCISE_FACTUAL = "concise_factual"


class ActionStatus(enum.Enum):
    """Explicit lifecycle status for executable actions to prevent dishonest acknowledgements."""
    RECEIVED = "received"
    CONFIRMATION_REQUIRED = "confirmation_required"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Map response styles to compatible speech expressions
STYLE_TO_EXPRESSION_MAP: dict[ResponseStyle, SpeechExpression] = {
    ResponseStyle.GREETING: SpeechExpression.GENTLE,
    ResponseStyle.TECHNICAL: SpeechExpression.FOCUSED,
    ResponseStyle.TASK_ACK: SpeechExpression.CONFIDENT,
    ResponseStyle.TASK_SUCCESS: SpeechExpression.HAPPY,
    ResponseStyle.TASK_FAILURE: SpeechExpression.SUPPORTIVE,
    ResponseStyle.SECURITY_WARNING: SpeechExpression.CONCERNED,
    ResponseStyle.SUPPORTIVE: SpeechExpression.SUPPORTIVE,
    ResponseStyle.CASUAL: SpeechExpression.GENTLE,
    ResponseStyle.CONCISE_FACTUAL: SpeechExpression.NEUTRAL,
}


def sanitize_terminal_text(text: str) -> str:
    """Sanitize model or untrusted text to prevent terminal ANSI/OSC escape sequence injection.

    Strips terminal escape codes (e.g. \x1b[..., \x1b]..., CSI, OSC sequences)
    that could corrupt the terminal or spoof user input.
    """
    if not text:
        return ""
    # Strip OSC sequences: \x1b] ... (\x07 | \x1b\\)
    text = re.sub(r"\x1b\].*?(?:\x07|\x1b\\)", "", text)
    # Strip CSI and standard ANSI escape sequences: \x1b[...m, etc.
    text = re.sub(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", text)
    # Remove raw control chars except newline, carriage return, tab
    sanitized = "".join(ch for ch in text if ch in ("\n", "\r", "\t") or ord(ch) >= 32)
    return sanitized


def format_action_acknowledgement(
    action_type: str,
    status: ActionStatus,
    target: Optional[str] = None,
    detail: Optional[str] = None,
    language: str = "en",
) -> str:
    """Generate an honest, accurate status message reflecting real action state.

    Never claims an action completed while it is still pending or executing.
    """
    target_str = f" '{target}'" if target else ""

    if language in ("hi", "hinglish"):
        if status == ActionStatus.RECEIVED:
            return f"Action request mili: {action_type}{target_str}."
        if status == ActionStatus.CONFIRMATION_REQUIRED:
            msg = detail or f"Kya aap sure hain ki {action_type}{target_str} karna chahte hain?"
            return f"Confirmation chahiye: {msg}"
        if status == ActionStatus.EXECUTING:
            return f"Processing: {action_type}{target_str} ho raha hai..."
        if status == ActionStatus.SUCCEEDED:
            detail_str = f" ({detail})" if detail else ""
            return f"Completed: {action_type}{target_str} successfully execute ho gaya{detail_str}."
        if status == ActionStatus.FAILED:
            err = f": {detail}" if detail else "."
            return f"Failed: {action_type}{target_str} execute nahi ho paya{err}"
        if status == ActionStatus.CANCELLED:
            return f"Cancelled: {action_type}{target_str} cancel kar diya gaya."

    # English default
    if status == ActionStatus.RECEIVED:
        return f"Request received: {action_type}{target_str}."
    if status == ActionStatus.CONFIRMATION_REQUIRED:
        msg = detail or f"Are you sure you want to proceed with {action_type}{target_str}?"
        return f"Confirmation required: {msg}"
    if status == ActionStatus.EXECUTING:
        return f"Executing {action_type}{target_str}..."
    if status == ActionStatus.SUCCEEDED:
        detail_str = f" ({detail})" if detail else ""
        return f"Completed: {action_type}{target_str} executed successfully{detail_str}."
    if status == ActionStatus.FAILED:
        err = f": {detail}" if detail else "."
        return f"Action failed: Unable to complete {action_type}{target_str}{err}"
    if status == ActionStatus.CANCELLED:
        return f"Action cancelled: {action_type}{target_str} was not executed."

    return f"{action_type}{target_str}: {status.value}"


def format_security_warning(action_name: str, resource: str, reason: str) -> str:
    """Format a clear, unmistakable security warning for high-risk operations."""
    return (
        f"⚠️  Security Alert: {action_name} requested for '{resource}'.\n"
        f"Reason: {reason}\n"
        f"This action requires explicit user confirmation before proceeding."
    )


def format_conversational_response(
    text: str,
    style: ResponseStyle = ResponseStyle.CASUAL,
    use_color: bool = True,
) -> tuple[str, SpeechExpression]:
    """Format assistant response for terminal display and pair with speech expression."""
    clean_text = sanitize_terminal_text(text).strip()
    speech_expr = STYLE_TO_EXPRESSION_MAP.get(style, SpeechExpression.NEUTRAL)
    return clean_text, speech_expr
