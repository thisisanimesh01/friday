"""macOS Intent Router for Milestone 6.1.

Maps natural-language user queries to strongly typed, allowlisted macOS actions
prior to or without running arbitrary LLM shell commands.
"""

from __future__ import annotations

import re
from typing import Any

from macos.registry import ActionResult, default_registry


ROUTING_PATTERNS = [
    # Battery checks
    (
        re.compile(r"(?i)\b(?:battery|power|charging)\b"),
        "get_battery",
        lambda m, text: {},
    ),
    # Volume read
    (
        re.compile(r"(?i)\b(?:what\s+is\s+the\s+volume|current\s+volume|get\s+volume|volume\s+level)\b"),
        "get_volume",
        lambda m, text: {},
    ),
    # Volume set (e.g. "set volume to 50", "volume 75")
    (
        re.compile(r"(?i)\b(?:set\s+volume\s+(?:to\s+)?|volume\s+)(\d{1,3})\b"),
        "set_volume",
        lambda m, text: {"level": int(m.group(1))},
    ),
    # Running applications
    (
        re.compile(r"(?i)\b(?:list\s+apps|running\s+apps|open\s+applications|what\s+apps\s+are\s+running)\b"),
        "list_apps",
        lambda m, text: {},
    ),
    # System appearance
    (
        re.compile(r"(?i)\b(?:dark\s+mode|light\s+mode|system\s+appearance|is\s+it\s+dark\s+mode)\b"),
        "get_appearance",
        lambda m, text: {},
    ),
    # Storage check
    (
        re.compile(r"(?i)\b(?:disk\s+space|storage\s+space|free\s+disk|storage\s+status|how\s+much\s+storage)\b"),
        "get_storage",
        lambda m, text: {},
    ),
]


def route_macos_intent(
    user_input: str,
    dry_run: bool = False,
    confirmed: bool = False,
) -> tuple[bool, ActionResult | None]:
    """Detect if user_input maps to an allowlisted macOS action.

    Returns:
        (matched: bool, result: ActionResult or None)
    """
    if not user_input or not isinstance(user_input, str):
        return False, None

    cleaned = user_input.strip()

    for pat, action_name, arg_extractor in ROUTING_PATTERNS:
        match = pat.search(cleaned)
        if match:
            kwargs = arg_extractor(match, cleaned)
            result = default_registry.execute(
                name=action_name,
                dry_run=dry_run,
                confirmed=confirmed,
                **kwargs,
            )
            return True, result

    return False, None


def format_action_result(action_result: ActionResult) -> str:
    """Format an ActionResult for conversational display."""
    if not action_result.success:
        if action_result.requires_confirmation:
            return f"⚠️ {action_result.confirmation_prompt} Re-run or confirm with 'yes'."
        return f"Error executing macOS action '{action_result.action_name}': {action_result.error}"

    if action_result.dry_run:
        return f"{action_result.data}"

    act = action_result.action_name
    data = action_result.data

    if act == "get_battery" and isinstance(data, dict):
        pct = data.get("percentage")
        chg = "Charging" if data.get("is_charging") else "Discharging"
        return f"Battery status: {pct}% ({chg})."

    if act == "get_volume" and isinstance(data, dict):
        vol = data.get("volume")
        return f"Current output volume is {vol}%."

    if act == "set_volume" and isinstance(data, dict):
        vol = data.get("volume")
        return f"Volume set to {vol}%."

    if act == "list_apps" and isinstance(data, list):
        return f"Running visible applications: {', '.join(data)}."

    if act == "get_appearance" and isinstance(data, dict):
        app = data.get("appearance", "Unknown")
        return f"macOS system appearance is currently in {app} Mode."

    if act == "get_storage" and isinstance(data, dict):
        free = data.get("free_gb")
        total = data.get("total_gb")
        pct = data.get("used_percent")
        return f"Disk storage: {free} GB free of {total} GB ({pct}% used)."

    return str(data)
