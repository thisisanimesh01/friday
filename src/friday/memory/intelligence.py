"""Intelligent memory filter and preference classifier for Milestone 5.3.

Provides logic to:
1. Filter out sensitive information (passwords, API keys, tokens, PII, credit cards).
2. Filter out temporary conversational noise, acknowledgments, and transient queries.
3. Classify user preferences (coding, language, name, tool, style, UI, database).
4. Detect fact updates / corrections and conflicting memories.
5. Score memory relevance based on semantic similarity, recency, and category match.
"""

from __future__ import annotations

import re
from typing import Any

# ── 1. Sensitive Data Patterns ───────────────────────────────────────────────
SENSITIVE_PATTERNS = [
    # API Keys & Secrets
    r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|bearer|private[_-]?key)\b\s*[:=]\s*['\"]?[a-zA-Z0-9_\-\.]{8,}['\"]?",
    r"(?i)\b(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|github_pat_[a-zA-Z0-9]{22,})\b",
    # Passwords
    r"(?i)\b(?:my\s+)?password\s+(?:is|was|set\s+to)\s+['\"]?\S+['\"]?",
    r"(?i)\b(?:pwd|passwd)\s*[:=]\s*['\"]?\S+['\"]?",
    # Credit Cards (standard 13-19 digit groupings)
    r"\b(?:\d{4}[ -]?){3}\d{4}\b",
    # Social Security / National ID numbers
    r"\b\d{3}-\d{2}-\d{4}\b",
]

SENSITIVE_KEYWORDS = [
    "password is",
    "my password",
    "api key is",
    "api_key",
    "secret token",
    "auth token",
    "private key",
    "credit card",
    "cvv",
]


def contains_sensitive_info(text: str) -> bool:
    """Return True if text contains sensitive credentials, tokens, or PII."""
    if not text or not isinstance(text, str):
        return False
    lower = text.lower()
    for kw in SENSITIVE_KEYWORDS:
        if kw in lower:
            return True
    for pat in SENSITIVE_PATTERNS:
        if re.search(pat, text):
            return True
    return False


# ── 2. Temporary / Ephemeral Conversational Noise ─────────────────────────────
EPHEMERAL_EXACT = {
    "ok",
    "okay",
    "k",
    "yes",
    "no",
    "yep",
    "nope",
    "sure",
    "thanks",
    "thank you",
    "thx",
    "cool",
    "got it",
    "understood",
    "bye",
    "goodbye",
    "see ya",
    "hello",
    "hi",
    "hey",
    "hey friday",
    "friday",
    "what did i say",
    "remember",
    "recall",
}

EPHEMERAL_PATTERNS = [
    r"^what\s+(?:is\s+)?(?:the\s+)?time(?:\s+is\s+it)?\??$",
    r"^what\s+(?:is\s+)?(?:the\s+)?weather(?:\s+like|\s+today|\s+now)?\??$",
    r"^(?:cpu|ram|disk|system)\s+status\??$",
    r"^how\s+are\s+you(?:\s+doing)?\??$",
    r"^can\s+you\s+hear\s+me\??$",
    r"^test(?:ing)?\s*(?:1\s*2\s*3)?$",
]


def is_ephemeral_or_transient(text: str) -> bool:
    """Return True if text is a temporary utterance, greeting, or transient diagnostic."""
    if not text or not isinstance(text, str):
        return True
    cleaned = text.strip().lower().rstrip("?.! ")
    if cleaned in EPHEMERAL_EXACT:
        return True
    for pat in EPHEMERAL_PATTERNS:
        if re.search(pat, cleaned):
            return True
    # Pure short acknowledgments < 3 chars
    if len(cleaned) <= 2:
        return True
    return False


# ── 3. Preference Recognition & Classification ───────────────────────────────
PREFERENCE_CATEGORIES: dict[str, list[re.Pattern]] = {
    "name": [
        re.compile(r"(?i)\b(?:my\s+name\s+is|call\s+me|i\s+am)\s+([A-Z][a-zA-Z0-9_\-]+)\b"),
    ],
    "role": [
        re.compile(r"(?i)\bi\s+(?:work\s+as|am)\s+(?:a|an)\s+([a-zA-Z\s]+?)(?:\.|$|,|\band\b)"),
    ],
    "programming_language": [
        re.compile(
            r"(?i)\b(?:switched|changed|moved)(?:\s+from\s+[a-zA-Z0-9#+]+)?\s+to\s+([a-zA-Z0-9#+]+)(?:\s+as\s+(?:my\s+)?(?:primary|favorite|main)\s+language)?\b"
        ),
        re.compile(
            r"(?i)\b(?:prefer|favorite|primary|main|love|like|work\s+in)\s+(?:programming\s+)?language\s+(?:is\s+)?([a-zA-Z0-9#+]+)\b"
        ),
        re.compile(
            r"(?i)\bi\s+(?:primarily\s+)?(?:code|program|develop|write)\s+in\s+([a-zA-Z0-9#+]+)\b"
        ),
        re.compile(
            r"(?i)\bi\s+(?:prefer|like|love)\s+([a-zA-Z0-9#+]+)\s+(?:for\s+[a-zA-Z0-9\s]+)?(?:over\s+[a-zA-Z0-9#+]+)?"
        ),
    ],
    "database": [
        re.compile(
            r"(?i)\b(?:prefer|favorite|primary|main)\s+database\s+(?:is\s+)?([a-zA-Z0-9_\-]+)\b"
        ),
        re.compile(
            r"(?i)\b(?:using|use)\s+([a-zA-Z0-9_\-]+)\s+(?:as\s+(?:our|the|my)\s+database|for\s+storage)\b"
        ),
    ],
    "project": [
        re.compile(
            r"(?i)\b(?:building|working\s+on|project\s+is|developing)\s+(?:project\s+)?([A-Za-z0-9_\-]+(?:\s+[A-Za-z0-9_\-]+)?)\b"
        ),
    ],
    "editor": [
        re.compile(
            r"(?i)\b(?:prefer|favorite|use)\s+(?:editor|ide)\s+(?:is\s+)?([a-zA-Z0-9_\-]+)\b"
        ),
    ],
    "theme": [
        re.compile(
            r"(?i)\b(?:prefer|use|like)\s+([a-zA-Z0-9_\-]+)\s+theme\b"
        ),
        re.compile(
            r"(?i)\b(?:prefer|like)\s+(dark\s+mode|light\s+mode)\b"
        ),
    ],
}


def extract_preference_category(text: str) -> tuple[str | None, str | None]:
    """Detect if the statement asserts a user preference or fact.

    Returns:
        (category, extracted_value) or (None, None)
    """
    if not text:
        return None, None

    # Do not treat inquiries, questions or interrogatives as preference assertions
    text_clean = text.strip()
    if text_clean.endswith("?") or re.match(
        r"(?i)^(?:what|which|who|where|when|why|how|can\s+you|do\s+you|tell\s+me)\b",
        text_clean,
    ):
        return None, None

    for category, patterns in PREFERENCE_CATEGORIES.items():
        for pat in patterns:
            match = pat.search(text)
            if match and match.group(1):
                val = match.group(1).strip()
                # Exclude vague common verbs or stopwords
                if val.lower() not in {
                    "a", "an", "the", "that", "this", "it", "to", "working", "building", "now", "here"
                }:
                    return category, val
    return None, None


# ── 4. Fact Correction & Contradiction Detection ──────────────────────────────
CORRECTION_TRIGGERS = [
    r"(?i)\bactually\b",
    r"(?i)\bi\s+meant\b",
    r"(?i)\bnot\s+[a-zA-Z0-9#+]+\s*,?\s*but\s+[a-zA-Z0-9#+]+",
    r"(?i)\bi\s+(?:switched|changed|moved)\s+(?:from\s+[a-zA-Z0-9#+]+\s+)?to\s+([a-zA-Z0-9#+]+)",
    r"(?i)\bmy\s+new\s+(?:favorite|primary|main|preference)\b",
    r"(?i)\bcorrection\s*:",
    r"(?i)\bupdate\s+my\b",
]


def is_fact_correction(text: str) -> bool:
    """Return True if user input indicates updating or correcting a past preference."""
    if not text or not isinstance(text, str):
        return False
    for pat in CORRECTION_TRIGGERS:
        if re.search(pat, text):
            return True
    return False


def find_conflicting_memories(new_text: str, stored_memories: list[tuple]) -> list[tuple]:
    """Identify existing stored memories that are superseded or contradicted by new_text.

    Parameters:
        new_text: The incoming statement.
        stored_memories: List of (id, user_text, bot_text, ...) tuples.

    Returns:
        List of memory tuples that directly conflict with the new preference.
    """
    category, new_val = extract_preference_category(new_text)
    is_corr = is_fact_correction(new_text)

    if not category and not is_corr:
        return []

    conflicts = []
    for row in stored_memories:
        prev_user = row[1]
        prev_cat, prev_val = extract_preference_category(prev_user)

        # Direct category clash with different value
        if category and prev_cat == category:
            if new_val and prev_val and new_val.lower() != prev_val.lower():
                conflicts.append(row)
        # If user explicitly said "switched to X" or "actually Y" and previous mentions category
        elif is_corr and category and category in prev_user.lower():
            conflicts.append(row)

    return conflicts


# ── 5. Intelligent Memory Storage Eligibility ────────────────────────────────
def should_store_memory(user_text: str, bot_text: Any = None) -> tuple[bool, str]:
    """Determine whether a turn should be permanently stored in long-term memory.

    Returns:
        (should_store: bool, reason: str)
    """
    if not user_text or not user_text.strip():
        return False, "empty_text"

    if contains_sensitive_info(user_text):
        return False, "sensitive_information"

    if is_ephemeral_or_transient(user_text):
        return False, "ephemeral_conversational_noise"

    # Command executions (file operations, time, weather) shouldn't pollute semantic memory
    user_lower = user_text.strip().lower()
    first_word = user_lower.split()[0] if user_lower.split() else ""
    if first_word in ["create", "make", "open", "read", "delete", "remove", "restore", "empty", "list"]:
        return False, "system_file_command"

    return True, "eligible"


# ── 6. Memory-Based Prompt Injection Sanitization ─────────────────────────
INJECTION_PATTERNS = [
    # System instruction override markers
    r"(?i)<\s*(?:system|instruction|im_start|im_end|tool_call|developer)\b.*?>",
    r"(?i)<\/\s*(?:system|instruction|im_start|im_end|tool_call|developer)\s*>",
    # Role spoofing & prompt prefix hijacking
    r"(?i)^(?:system|assistant|friday|developer|bot)\s*:\s*",
    r"(?i)\n(?:system|assistant|friday|developer|bot)\s*:\s*",
    # Jailbreak / instruction disregard phrases
    r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions|prompts|rules)\b",
    r"(?i)\byou\s+are\s+now\s+(?:unrestricted|in\s+dan\s+mode|jailbroken)\b",
    r"(?i)\bdisregard\s+(?:security|safety|guidelines)\b",
]


def sanitize_memory_text(text: str) -> str:
    """Sanitize retrieved memory text to prevent memory-based prompt injection."""
    if not text or not isinstance(text, str):
        return ""
    sanitized = text
    for pat in INJECTION_PATTERNS:
        sanitized = re.sub(pat, "[SANITIZED]", sanitized)
    return sanitized.strip()


# ── 7. Natural-Language Memory Command Parsing ──────────────────────────────
REMEMBER_PATTERNS = [
    re.compile(r"(?i)^(?:friday\s*,?\s*)?remember\s+(?:that\s+)?(.+)$"),
    re.compile(r"(?i)^(?:friday\s*,?\s*)?please\s+remember\s+(?:that\s+)?(.+)$"),
    re.compile(r"(?i)^(?:friday\s*,?\s*)?keep\s+in\s+mind\s+(?:that\s+)?(.+)$"),
]


def parse_memory_command(text: str) -> tuple[str | None, str | None]:
    """Parse natural language 'remember' and 'forget' commands.

    Returns:
        (command_type, target_value)
        command_type: 'remember', 'forget_all', 'forget_preferences', 'forget_category', 'forget_query', or None
    """
    if not text or not isinstance(text, str):
        return None, None

    cleaned = text.strip().rstrip(".?!")

    # Check forget commands
    if re.search(
        r"(?i)^(?:friday\s*,?\s*)?forget\s+(?:everything(?:\s+you\s+know(?:\s+about\s+me)?)?|all\s+memories|all\s+my\s+data)$",
        cleaned,
    ):
        return "forget_all", None

    if re.search(r"(?i)^(?:friday\s*,?\s*)?forget\s+(?:my\s+)?(?:preferences|profile)$", cleaned):
        return "forget_preferences", None

    match_cat = re.search(
        r"(?i)^(?:friday\s*,?\s*)?forget\s+(?:my\s+)?(name|role|programming\s+language|language|database|editor|theme)(?:\s+preference)?$",
        cleaned,
    )
    if match_cat:
        cat_raw = match_cat.group(1).lower().replace(" ", "_")
        cat_name = "programming_language" if cat_raw in ("language", "programming_language") else cat_raw
        return "forget_category", cat_name

    match_forget = re.search(r"(?i)^(?:friday\s*,?\s*)?forget\s+(?:about\s+)?['\"]?(.+?)['\"]?$", cleaned)
    if match_forget:
        target = match_forget.group(1).strip()
        if target:
            return "forget_query", target

    # Check explicit remember commands
    for pat in REMEMBER_PATTERNS:
        match_rem = pat.search(cleaned)
        if match_rem:
            fact = match_rem.group(1).strip()
            if fact:
                return "remember", fact

    return None, None
