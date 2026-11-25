"""Deterministic unit tests for FRIDAY Centralized Personality & Identity System.

Tests:
- Assistant identity consistency and profile attributes
- Compact prompt construction with parameterization (style, language, form of address)
- Prompt isolation from structured command/intent routing
- Response style selection and mapping to speech expressions
- Honest action acknowledgements across all ActionStatus lifecycle states
- Security warnings and confirmation preservation
- Terminal escape sequence sanitization against ANSI/OSC injection
- CLI flags for personality, --no-color, and --quiet
"""



from friday.personality.profile import (
    PersonalityConfig,
    get_personality_config,
    get_personality_profile,
)
from friday.personality.prompts import (
    build_personality_system_prompt,
    build_style_prompt_fragment,
)
from friday.personality.response_style import (
    STYLE_TO_EXPRESSION_MAP,
    ActionStatus,
    ResponseStyle,
    format_action_acknowledgement,
    format_conversational_response,
    format_security_warning,
    sanitize_terminal_text,
)


def test_personality_profile_identity():
    """Verify centralized identity attributes."""
    profile = get_personality_profile()
    assert profile.name == "Friday"
    assert "macOS" in profile.platform
    assert "Terminal and Voice" in profile.interface
    assert "calm" in profile.tone.lower()
    assert "friday-gentle" == profile.voice_profile_id


def test_personality_config_defaults():
    """Verify default runtime personality configuration."""
    cfg = get_personality_config()
    assert cfg.personality_type == "friendly"
    assert cfg.response_style == "adaptive"
    assert cfg.friendliness == "warm"
    assert cfg.humor == "subtle"
    assert cfg.form_of_address is None
    assert cfg.startup_greeting is True


def test_personality_config_env_overrides(monkeypatch):
    """Verify environment variable overrides for personality settings."""
    monkeypatch.setenv("FRIDAY_PERSONALITY", "professional")
    monkeypatch.setenv("FRIDAY_RESPONSE_STYLE", "concise")
    monkeypatch.setenv("FRIDAY_FRIENDLINESS", "neutral")
    monkeypatch.setenv("FRIDAY_HUMOR", "off")
    monkeypatch.setenv("FRIDAY_LANGUAGE", "hi")
    monkeypatch.setenv("FRIDAY_FORM_OF_ADDRESS", "Animesh")
    monkeypatch.setenv("FRIDAY_STARTUP_GREETING", "false")
    monkeypatch.setenv("NO_COLOR", "1")

    cfg = PersonalityConfig.from_env()
    assert cfg.personality_type == "professional"
    assert cfg.response_style == "concise"
    assert cfg.friendliness == "neutral"
    assert cfg.humor == "off"
    assert cfg.language == "hi"
    assert cfg.form_of_address == "Animesh"
    assert cfg.startup_greeting is False
    assert cfg.terminal_color is False


def test_build_personality_system_prompt_compact():
    """Verify prompt length and essential behavioral instructions."""
    prompt = build_personality_system_prompt()
    # Ensure compact token footprint (<150 words/tokens)
    word_count = len(prompt.split())
    assert word_count < 140
    # Must enforce identity
    assert "You are Friday" in prompt
    assert "Never claim to be JARVIS, Hinata, ChatGPT, Qwen, or human" in prompt
    assert "honest about uncertainty" in prompt
    assert "Never claim an action succeeded unless" in prompt
    assert "Respect privacy and security confirmations" in prompt


def test_build_personality_system_prompt_language_variants():
    """Verify prompt adapts to language configuration."""
    hi_cfg = PersonalityConfig(language="hi")
    hi_prompt = build_personality_system_prompt(config=hi_cfg)
    assert "Hindi" in hi_prompt

    hinglish_cfg = PersonalityConfig(language="hinglish")
    hinglish_prompt = build_personality_system_prompt(config=hinglish_cfg)
    assert "Hinglish" in hinglish_prompt


def test_build_style_prompt_fragment():
    """Verify context prompt fragments for various response situations."""
    assert "greeting" in build_style_prompt_fragment("greeting").lower()
    assert "technical" in build_style_prompt_fragment("technical").lower()
    assert "security warning" in build_style_prompt_fragment("security_warning").lower()
    assert build_style_prompt_fragment("nonexistent") == ""


def test_sanitize_terminal_text_strips_ansi_and_osc():
    """Verify terminal sanitization strips ANSI and OSC injection payloads."""
    malicious_input = "\x1b[31;1mDanger\x1b[0m \x1b]0;TitleSpoof\x07Hello"
    sanitized = sanitize_terminal_text(malicious_input)
    assert "\x1b" not in sanitized
    assert "Danger Hello" in sanitized


def test_honest_action_acknowledgements_english():
    """Verify action status formatting never falsely confirms pending actions in English."""
    received = format_action_acknowledgement("create_file", ActionStatus.RECEIVED, target="notes.txt")
    assert "Request received: create_file 'notes.txt'" in received
    assert "successfully" not in received

    confirm = format_action_acknowledgement("delete_file", ActionStatus.CONFIRMATION_REQUIRED, target="secrets.env")
    assert "Confirmation required:" in confirm
    assert "secrets.env" in confirm

    executing = format_action_acknowledgement("open_file", ActionStatus.EXECUTING, target="data.csv")
    assert "Executing open_file 'data.csv'..." in executing

    succeeded = format_action_acknowledgement("create_file", ActionStatus.SUCCEEDED, target="notes.txt")
    assert "Completed: create_file 'notes.txt' executed successfully." in succeeded

    failed = format_action_acknowledgement("read_file", ActionStatus.FAILED, target="missing.txt", detail="File not found")
    assert "Action failed: Unable to complete read_file 'missing.txt': File not found" in failed

    cancelled = format_action_acknowledgement("empty_trash", ActionStatus.CANCELLED)
    assert "Action cancelled: empty_trash was not executed." in cancelled


def test_honest_action_acknowledgements_hindi():
    """Verify action status formatting in Hindi/Hinglish."""
    received = format_action_acknowledgement("create_file", ActionStatus.RECEIVED, target="notes.txt", language="hi")
    assert "Action request mili" in received

    succeeded = format_action_acknowledgement("create_file", ActionStatus.SUCCEEDED, target="notes.txt", language="hi")
    assert "successfully execute ho gaya" in succeeded

    failed = format_action_acknowledgement("delete_file", ActionStatus.FAILED, target="notes.txt", detail="Permission denied", language="hinglish")
    assert "execute nahi ho paya" in failed


def test_format_security_warning():
    """Verify security alert formatting."""
    warning = format_security_warning("delete_folder", "important_docs", "Recursive deletion of directory")
    assert "Security Alert" in warning
    assert "important_docs" in warning
    assert "explicit user confirmation" in warning


def test_style_to_speech_expression_mapping():
    """Verify that response styles correctly map to supported speech expressions."""
    from friday.audio.expression import SpeechExpression

    assert STYLE_TO_EXPRESSION_MAP[ResponseStyle.GREETING] == SpeechExpression.GENTLE
    assert STYLE_TO_EXPRESSION_MAP[ResponseStyle.TASK_SUCCESS] == SpeechExpression.HAPPY
    assert STYLE_TO_EXPRESSION_MAP[ResponseStyle.SECURITY_WARNING] == SpeechExpression.CONCERNED
    assert STYLE_TO_EXPRESSION_MAP[ResponseStyle.TECHNICAL] == SpeechExpression.FOCUSED


def test_format_conversational_response():
    """Verify terminal formatting pairs with correct speech expression."""
    from friday.audio.expression import SpeechExpression

    text, expr = format_conversational_response("Hello, how can I assist you?", ResponseStyle.GREETING)
    assert text == "Hello, how can I assist you?"
    assert expr == SpeechExpression.GENTLE


def test_cli_personality_flags(monkeypatch):
    """Verify CLI flags set personality, no-color and quiet options."""
    from friday.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["--personality", "professional", "--no-color", "--quiet"])
    assert args.personality == "professional"
    assert args.no_color is True
    assert args.quiet is True
