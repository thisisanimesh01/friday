"""FRIDAY Personality, Identity, and Response Style System.

Provides centralized single source of truth for:
- Friday assistant identity and core traits
- Compact personality prompt construction for local & cloud models
- Response styles (conversational, technical, task status, security warnings)
- Multilingual personality support (English, Hindi, Hinglish)
- Safe, honest action acknowledgements (request received, pending, confirmed, succeeded, failed, cancelled)
- Strict separation from structured intent parsing and tool invocation
"""

from friday.personality.profile import (
    PersonalityConfig,
    PersonalityProfile,
    get_personality_config,
    get_personality_profile,
)
from friday.personality.prompts import (
    build_personality_system_prompt,
    build_style_prompt_fragment,
)
from friday.personality.response_style import (
    ActionStatus,
    ResponseStyle,
    format_action_acknowledgement,
    format_conversational_response,
    format_security_warning,
    sanitize_terminal_text,
)

__all__ = [
    "PersonalityConfig",
    "PersonalityProfile",
    "get_personality_config",
    "get_personality_profile",
    "build_personality_system_prompt",
    "build_style_prompt_fragment",
    "ActionStatus",
    "ResponseStyle",
    "format_action_acknowledgement",
    "format_conversational_response",
    "format_security_warning",
    "sanitize_terminal_text",
]
