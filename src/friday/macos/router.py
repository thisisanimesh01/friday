"""macOS Intent Router for Milestone 6.1.

Maps natural-language user queries to strongly typed, allowlisted macOS actions
prior to or without running arbitrary LLM shell commands.
"""

from __future__ import annotations

import re

from friday.macos.registry import ActionResult, default_registry

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
    # ── Milestone 6.2 Application Patterns (English, Hindi, Hinglish) ─────────
    # Active application query
    (
        re.compile(r"(?i)\b(?:active\s+app|frontmost\s+app|which\s+app\s+is\s+active|current\s+app|kaunsa\s+app\s+chal\s+raha\s+hai)\b"),
        "get_active_app",
        lambda m, text: {},
    ),
    # Launch application (e.g., "open calculator", "launch terminal", "calculator kholo", "start brave")
    (
        re.compile(r"(?i)\b(?:open|launch|start|chalu\s+karo|kholo)\s+([a-zA-Z0-9_\s]+?)(?:\s+app|\s+application|\s+kholo|\s+chalu\s+karo)?$"),
        "launch_app",
        lambda m, text: {"app_name": m.group(1).strip()},
    ),
    (
        re.compile(r"(?i)\b([a-zA-Z0-9_]+)\s+(?:kholo|chalu\s+karo|open\s+karo)\b"),
        "launch_app",
        lambda m, text: {"app_name": m.group(1).strip()},
    ),
    # Quit application (e.g., "quit calculator", "close safari", "terminal band karo", "force quit chrome")
    (
        re.compile(r"(?i)\b(?:force\s+quit|kill)\s+([a-zA-Z0-9_\s]+?)(?:\s+app|\s+application)?$"),
        "quit_app",
        lambda m, text: {"app_name": m.group(1).strip(), "force": True},
    ),
    (
        re.compile(r"(?i)\b(?:quit|close|exit|band\s+karo)\s+([a-zA-Z0-9_\s]+?)(?:\s+app|\s+application|\s+band\s+karo)?$"),
        "quit_app",
        lambda m, text: {"app_name": m.group(1).strip(), "force": False},
    ),
    (
        re.compile(r"(?i)\b([a-zA-Z0-9_]+)\s+(?:band\s+karo|close\s+karo)\b"),
        "quit_app",
        lambda m, text: {"app_name": m.group(1).strip(), "force": False},
    ),
    # Switch application (e.g., "switch to terminal", "focus notes", "terminal pe switch karo")
    (
        re.compile(r"(?i)\b(?:switch\s+to|focus|bring\s+up)\s+([a-zA-Z0-9_\s]+?)(?:\s+app|\s+application)?$"),
        "switch_app",
        lambda m, text: {"app_name": m.group(1).strip()},
    ),
    (
        re.compile(r"(?i)\b([a-zA-Z0-9_]+)\s+pe\s+switch\s+karo\b"),
        "switch_app",
        lambda m, text: {"app_name": m.group(1).strip()},
    ),
    # Hide application (e.g., "hide calculator", "hide window", "chupao")
    (
        re.compile(r"(?i)\b(?:hide)\s+([a-zA-Z0-9_\s]+?)(?:\s+app|\s+application)?$"),
        "hide_app",
        lambda m, text: {"app_name": m.group(1).strip()},
    ),
    (
        re.compile(r"(?i)\b(?:hide\s+this|hide\s+window|chupao)\b"),
        "hide_app",
        lambda m, text: {},
    ),
    # ── Milestone 6.2 Window Patterns ─────────────────────────────────────────
    # Minimize window (e.g., "minimize window", "window minimize karo", "minimize calculator")
    (
        re.compile(r"(?i)\b(?:minimize\s+window|minimize)\b(?:\s+([a-zA-Z0-9_\s]+))?"),
        "minimize_window",
        lambda m, text: {"app_name": m.group(1).strip()} if m.group(1) else {},
    ),
    (
        re.compile(r"(?i)\b(?:window\s+chhoti\s+karo|minimize\s+karo)\b"),
        "minimize_window",
        lambda m, text: {},
    ),
    # Restore window (e.g., "restore window", "unminimize", "window wapas lao")
    (
        re.compile(r"(?i)\b(?:restore\s+window|restore|unminimize)\b(?:\s+([a-zA-Z0-9_\s]+))?"),
        "restore_window",
        lambda m, text: {"app_name": m.group(1).strip()} if m.group(1) else {},
    ),
    (
        re.compile(r"(?i)\b(?:window\s+wapas\s+lao|restore\s+karo)\b"),
        "restore_window",
        lambda m, text: {},
    ),
    # Fullscreen window (e.g., "full screen", "fullscreen karo", "toggle fullscreen")
    (
        re.compile(r"(?i)\b(?:fullscreen|full\s+screen|toggle\s+fullscreen|badi\s+screen)\b"),
        "fullscreen_window",
        lambda m, text: {},
    ),
    # Position window (e.g., "snap left", "left half karo", "maximize window", "center window")
    (
        re.compile(r"(?i)\b(?:snap\s+left|left\s+half|left\s+side|left\s+karo)\b"),
        "position_window",
        lambda m, text: {"position": "left_half"},
    ),
    (
        re.compile(r"(?i)\b(?:snap\s+right|right\s+half|right\s+side|right\s+karo)\b"),
        "position_window",
        lambda m, text: {"position": "right_half"},
    ),
    (
        re.compile(r"(?i)\b(?:maximize\s+window|maximize|pura\s+bada\s+karo|maximize\s+karo)\b"),
        "position_window",
        lambda m, text: {"position": "maximize"},
    ),
    (
        re.compile(r"(?i)\b(?:center\s+window|center\s+karo)\b"),
        "position_window",
        lambda m, text: {"position": "center"},
    ),
    # ── Milestone 6.2 Media Capture Patterns ──────────────────────────────────
    # Camera capture (e.g., "take a photo", "capture photo", "camera se photo lo", "photo khicho")
    (
        re.compile(r"(?i)\b(?:take\s+(?:a\s+)?photo|capture\s+photo|camera\s+capture|photo\s+khicho|tasveer\s+lo)\b"),
        "capture_photo",
        lambda m, text: {},
    ),
    # Screenshot capture (e.g., "take a screenshot", "screenshot lo", "capture screen")
    (
        re.compile(r"(?i)\b(?:take\s+(?:a\s+)?screenshot|capture\s+screen|screenshot\s+lo|screen\s+capture)\b"),
        "capture_screenshot",
        lambda m, text: {"mode": "fullscreen"},
    ),
    # ── Milestone 6.3 AppleScript & Shortcuts Patterns ─────────────────────────
    # Notification template (e.g., "show notification Hello", "notification dikhao World")
    (
        re.compile(r"(?i)\b(?:show\s+notification|display\s+notification|notification\s+bhejo|notification\s+dikhao)\s+(.+)$"),
        "run_script_template",
        lambda m, text: {"template_name": "display_notification", "params": {"title": "FRIDAY", "message": m.group(1).strip()}},
    ),
    # Note creation template (e.g., "create note Buy groceries", "note banao Meeting notes")
    (
        re.compile(r"(?i)\b(?:create\s+note|make\s+note|new\s+note|note\s+banao|note\s+likho)\s+(.+)$"),
        "run_script_template",
        lambda m, text: {"template_name": "create_note", "params": {"title": m.group(1).strip(), "body": "Created by FRIDAY"}},
    ),
    # Music play/pause template (e.g., "play music", "pause music", "music chalao", "gaana bajao", "gaana roko")
    (
        re.compile(r"(?i)\b(?:play\s+music|pause\s+music|toggle\s+music|music\s+chalao|music\s+roko|gaana\s+bajao|gaana\s+roko)\b"),
        "run_script_template",
        lambda m, text: {"template_name": "music_play_pause", "params": {}},
    ),
    # Current music track query (e.g., "what is playing", "current track", "kaunsa gaana chal raha hai")
    (
        re.compile(r"(?i)\b(?:what\s+(?:is\s+)?playing|current\s+song|current\s+track|which\s+song|kaunsa\s+gaana\s+chal\s+raha\s+hai)\b"),
        "run_script_template",
        lambda m, text: {"template_name": "get_current_track", "params": {}},
    ),
    # Empty trash template (Destructive, e.g., "empty trash", "kachra saaf karo", "trash khali karo")
    (
        re.compile(r"(?i)\b(?:empty\s+trash|clear\s+trash|trash\s+khali\s+karo|kachra\s+saaf\s+karo)\b"),
        "run_script_template",
        lambda m, text: {"template_name": "empty_trash", "params": {}},
    ),
    # List AppleScript templates (e.g., "list scripts", "list automation templates", "scripts dikhao")
    (
        re.compile(r"(?i)\b(?:list\s+scripts|available\s+scripts|automation\s+templates|scripts\s+dikhao)\b"),
        "list_script_templates",
        lambda m, text: {},
    ),
    # List Shortcuts (e.g., "list shortcuts", "available shortcuts", "shortcuts dikhao")
    (
        re.compile(r"(?i)\b(?:list\s+shortcuts|available\s+shortcuts|my\s+shortcuts|shortcuts\s+dikhao)\b"),
        "list_shortcuts",
        lambda m, text: {},
    ),
    # Run shortcut (e.g., "run shortcut Charger Sound", "execute shortcut Quick Note", "shortcut chalao Charger Sound")
    (
        re.compile(r"(?i)\b(?:run\s+shortcut|execute\s+shortcut|shortcut\s+chalao)\s+([a-zA-Z0-9_\s]+?)$"),
        "run_shortcut",
        lambda m, text: {"shortcut_name": m.group(1).strip()},
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

    if act == "launch_app" and isinstance(data, dict):
        if "error" in data:
            return f"Failed to launch: {data['error']}"
        return f"Application '{data.get('application')}' launched successfully."

    if act == "quit_app" and isinstance(data, dict):
        if "error" in data:
            return f"Failed to quit: {data['error']}"
        status = "Force-quit" if data.get("status") == "force_quit" else "Closed"
        return f"{status} application '{data.get('application')}'."

    if act == "switch_app" and isinstance(data, dict):
        if "error" in data:
            return f"Failed to switch: {data['error']}"
        return f"Switched to '{data.get('application')}'."

    if act == "hide_app" and isinstance(data, dict):
        if "error" in data:
            return f"Failed to hide: {data['error']}"
        return f"Application '{data.get('application')}' hidden."

    if act == "get_active_app" and isinstance(data, dict):
        if "error" in data:
            return f"Active application check: {data['error']}"
        return f"Active application is '{data.get('active_application')}'."

    if act in ("minimize_window", "restore_window", "fullscreen_window") and isinstance(data, dict):
        if "error" in data:
            return f"Window action error: {data['error']}"
        return f"Window operation '{data.get('status')}' applied to {data.get('target', 'active app')}."

    if act == "position_window" and isinstance(data, dict):
        if "error" in data:
            return f"Window position error: {data['error']}"
        return f"Window positioned to '{data.get('position')}'."

    if act == "capture_photo" and isinstance(data, dict):
        if "error" in data:
            return f"Camera capture error: {data['error']}"
        return f"Photo captured successfully: {data.get('file_path')} (Saved in friday workspace/camera/)."

    if act == "capture_screenshot" and isinstance(data, dict):
        if "error" in data:
            return f"Screenshot error: {data['error']}"
        return f"Screenshot captured successfully: {data.get('file_path')} (Saved in friday workspace/screenshots/)."

    if act == "run_script_template" and isinstance(data, dict):
        if "error" in data:
            return f"Script error: {data['error']}"
        if data.get("status") == "dry_run":
            return f"[Dry-Run Preview] Template '{data.get('template')}':\n{data.get('script_preview')}"
        return f"Automation '{data.get('template')}' executed: {data.get('output', 'Success')}"

    if act == "list_script_templates" and isinstance(data, list):
        names = [f"• {t['name']} - {t['description']}" for t in data]
        return "Available AppleScript templates:\n" + "\n".join(names)

    if act == "run_shortcut" and isinstance(data, dict):
        if "error" in data:
            return f"Shortcut error: {data['error']}"
        if data.get("status") == "dry_run":
            return f"[Dry-Run Preview] Shortcut '{data.get('shortcut')}':\nBoundary: {data.get('resource_boundary')}\nSummary: {data.get('actions_summary')}"
        return f"Shortcut '{data.get('shortcut')}' executed successfully in {data.get('duration_s', 0)}s."

    if act == "list_shortcuts" and isinstance(data, list):
        if not data:
            return "No shortcuts found."
        lines = []
        for s in data:
            appr = "✓ Approved" if s.get("approved") else "✗ Unverified"
            lines.append(f"• {s['name']} [{appr}] - {s.get('actions_summary', 'No summary')}")
        return "macOS Shortcuts:\n" + "\n".join(lines)

    return str(data)
