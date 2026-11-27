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
    # System appearance read query
    (
        re.compile(r"(?i)\b(?:is\s+(?:macos\s+in\s+)?dark\s+mode|is\s+it\s+dark\s+mode|what\s+is\s+(?:the\s+)?appearance|current\s+appearance|system\s+appearance)\b"),
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
        re.compile(r"(?i)\b(?:open|launch|start|chalu\s+karo|kholo)\s+(?!developer\s+mode|study\s+mode|night\s+mode|focus\s+mode|system\s+health|python\s+project|workspace\s+organization|morning\s+routine|workflow)([a-zA-Z0-9_\s]+?)(?:\s+app|\s+application|\s+kholo|\s+chalu\s+karo)?$"),
        "launch_app",
        lambda m, text: {"app_name": m.group(1).strip()},
    ),
    (
        re.compile(r"(?i)\b(?!developer|study|night|focus|mode|system|health|python|project|workspace|organization|morning|routine)([a-zA-Z0-9_]+)\s+(?:kholo|chalu\s+karo|open\s+karo)\b"),
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
        re.compile(r"(?i)\b(?:switch\s+to|focus|bring\s+up)\s+(?!dark\s+mode|light\s+mode|focus\s+mode|mode)([a-zA-Z0-9_\s]+?)(?:\s+app|\s+application)?$"),
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
    # Milestone 7.1 Active Window Capture
    (
        re.compile(r"(?i)\b(?:capture\s+(?:the\s+)?active\s+window|active\s+window\s+(?:screenshot|capture)|active\s+window\s+capture\s+karo)\b"),
        "capture_screen",
        lambda m, text: {"mode": "window"},
    ),
    # Milestone 7.1 Cancel capture
    (
        re.compile(r"(?i)\b(?:stop\s+(?:the\s+)?capture|cancel\s+capture|capture\s+roko)\b"),
        "cancel_capture",
        lambda m, text: {},
    ),
    # Milestone 7.1 Permission check & display queries
    (
        re.compile(r"(?i)\b(?:screen\s+recording\s+permission|check\s+screen\s+permission)\b"),
        "check_screen_recording_permission",
        lambda m, text: {},
    ),
    (
        re.compile(r"(?i)\b(?:discover\s+displays|list\s+displays|my\s+screens|screen\s+info)\b"),
        "discover_displays",
        lambda m, text: {},
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
    # ── Milestone 6.4 System Settings, Hardware & Monitoring Patterns ──────────
    # Mute / Unmute
    (
        re.compile(r"(?i)\b(?:mute|awaaz\s+band\s+karo|shant\s+ho\s+jao)\b"),
        "set_mute",
        lambda m, text: {"mute": True},
    ),
    (
        re.compile(r"(?i)\b(?:unmute|awaaz\s+chalu\s+karo)\b"),
        "set_mute",
        lambda m, text: {"mute": False},
    ),
    # Brightness get / set (e.g., "brightness 80", "set brightness to 60", "brightness kitni hai")
    (
        re.compile(r"(?i)\b(?:set\s+brightness\s+(?:to\s+)?|brightness\s+)(\d{1,3})\b"),
        "set_brightness",
        lambda m, text: {"level": int(m.group(1))},
    ),
    (
        re.compile(r"(?i)\b(?:get\s+brightness|current\s+brightness|brightness\s+check|brightness\s+kitni\s+hai)\b"),
        "get_brightness",
        lambda m, text: {},
    ),
    # Appearance dark / light / toggle
    (
        re.compile(r"(?i)\b(?:switch\s+to\s+dark\s+mode|enable\s+dark\s+mode|dark\s+mode\s+on|dark\s+mode\s+karo)\b"),
        "set_appearance",
        lambda m, text: {"dark_mode": True},
    ),
    (
        re.compile(r"(?i)\b(?:switch\s+to\s+light\s+mode|enable\s+light\s+mode|light\s+mode\s+on|light\s+mode\s+karo)\b"),
        "set_appearance",
        lambda m, text: {"dark_mode": False},
    ),
    (
        re.compile(r"(?i)\b(?:toggle\s+appearance|toggle\s+dark\s+mode|theme\s+badlo)\b"),
        "toggle_appearance",
        lambda m, text: {},
    ),
    # Audio Devices
    (
        re.compile(r"(?i)\b(?:list\s+audio\s+devices|audio\s+devices|speakers\s+and\s+mics)\b"),
        "get_audio_devices",
        lambda m, text: {},
    ),
    # Focus Mode / Do Not Disturb
    (
        re.compile(r"(?i)\b(?:is\s+focus\s+mode|focus\s+mode\s+status|do\s+not\s+disturb\s+status|dnd\s+status)\b"),
        "get_focus_mode",
        lambda m, text: {},
    ),
    (
        re.compile(r"(?i)\b(?:toggle\s+focus\s+mode|toggle\s+dnd|dnd\s+on|dnd\s+off)\b"),
        "toggle_focus_mode",
        lambda m, text: {},
    ),
    # System Monitoring: CPU, RAM, Hardware metrics
    (
        re.compile(r"(?i)\b(?:cpu\s+usage|ram\s+usage|memory\s+usage|system\s+metrics|hardware\s+metrics)\b"),
        "get_hardware_metrics",
        lambda m, text: {},
    ),
    # Thermal status
    (
        re.compile(r"(?i)\b(?:thermal\s+status|temperature|is\s+mac\s+hot|throttling)\b"),
        "get_thermal",
        lambda m, text: {},
    ),
    # Wi-Fi & Bluetooth status
    (
        re.compile(r"(?i)\b(?:wifi\s+status|check\s+wifi|is\s+wifi\s+on|wifi\s+connected)\b"),
        "get_wifi",
        lambda m, text: {},
    ),
    (
        re.compile(r"(?i)\b(?:bluetooth\s+status|check\s+bluetooth|is\s+bluetooth\s+on)\b"),
        "get_bluetooth",
        lambda m, text: {},
    ),
    # Wi-Fi control (e.g. "turn on wifi", "disable wifi", "wifi band karo")
    (
        re.compile(r"(?i)\b(?:turn\s+on\s+wifi|enable\s+wifi|wifi\s+chalu\s+karo)\b"),
        "set_wifi_power",
        lambda m, text: {"enabled": True},
    ),
    (
        re.compile(r"(?i)\b(?:turn\s+off\s+wifi|disable\s+wifi|wifi\s+band\s+karo)\b"),
        "set_wifi_power",
        lambda m, text: {"enabled": False},
    ),
    # Bluetooth control (e.g. "turn on bluetooth", "turn off bluetooth")
    (
        re.compile(r"(?i)\b(?:turn\s+on\s+bluetooth|enable\s+bluetooth|bluetooth\s+chalu\s+karo)\b"),
        "set_bluetooth_power",
        lambda m, text: {"enabled": True},
    ),
    (
        re.compile(r"(?i)\b(?:turn\s+off\s+bluetooth|disable\s+bluetooth|bluetooth\s+band\s+karo)\b"),
        "set_bluetooth_power",
        lambda m, text: {"enabled": False},
    ),
    # Screen Lock, Sleep, Restart, Shutdown
    (
        re.compile(r"(?i)\b(?:lock\s+screen|lock\s+display|screen\s+lock\s+karo)\b"),
        "lock_screen",
        lambda m, text: {},
    ),
    (
        re.compile(r"(?i)\b(?:sleep\s+system|put\s+to\s+sleep|sleep\s+mac|so\s+jao)\b"),
        "system_sleep",
        lambda m, text: {},
    ),
    (
        re.compile(r"(?i)\b(?:restart\s+system|reboot\s+mac|restart\s+mac|restart\s+karo)\b"),
        "system_restart",
        lambda m, text: {},
    ),
    (
        re.compile(r"(?i)\b(?:shut\s+down|power\s+off|turn\s+off\s+mac|system\s+band\s+karo)\b"),
        "system_shutdown",
        lambda m, text: {},
    ),
    # System Health Report
    (
        re.compile(r"(?i)\b(?:system\s+health\s+report|generate\s+report|health\s+report|system\s+summary\s+report)\b"),
        "generate_health_report",
        lambda m, text: {},
    ),
    # ── Milestone 6.5 Desktop Workflows Patterns (English, Hindi, Hinglish) ───
    # Stop active workflow
    (
        re.compile(r"(?i)\b(?:stop\s+(?:the\s+)?workflow|workflow\s+roko|cancel\s+workflow|stop\s+current\s+workflow)\b"),
        "stop_workflow",
        lambda m, text: {},
    ),
    # List workflows
    (
        re.compile(r"(?i)\b(?:list\s+workflows|what\s+workflows|available\s+workflows|show\s+workflows)\b"),
        "list_workflows",
        lambda m, text: {},
    ),
    # Built-in direct triggers
    (
        re.compile(r"(?i)\b(?:start|run|launch|activate|chalu\s+karo)?\s*(?:developer\s+mode|dev\s+mode)(?:\s+chalu\s+karo|\s+start)?\b"),
        "run_workflow",
        lambda m, text: {"workflow_name": "developer_mode"},
    ),
    (
        re.compile(r"(?i)\b(?:start|run|launch|activate|chalu\s+karo)?\s*(?:study\s+mode)(?:\s+chalu\s+karo|\s+start)?\b"),
        "run_workflow",
        lambda m, text: {"workflow_name": "study_mode"},
    ),
    (
        re.compile(r"(?i)\b(?:start|run|launch|activate|chalu\s+karo)?\s*(?:system\s+health\s+check)(?:\s+chalu\s+karo|\s+start)?\b"),
        "run_workflow",
        lambda m, text: {"workflow_name": "system_health_check"},
    ),
    (
        re.compile(r"(?i)\b(?:start|run|launch|activate|setup|chalu\s+karo)?\s*(?:python\s+project\s+setup|setup\s+python\s+project)(?:\s+chalu\s+karo|\s+start)?\b"),
        "run_workflow",
        lambda m, text: {"workflow_name": "python_project_setup"},
    ),
    (
        re.compile(r"(?i)\b(?:start|run|launch|activate|chalu\s+karo)?\s*(?:morning\s+routine)(?:\s+chalu\s+karo|\s+start)?\b"),
        "run_workflow",
        lambda m, text: {"workflow_name": "morning_routine"},
    ),
    (
        re.compile(r"(?i)\b(?:start|run|launch|activate|chalu\s+karo)?\s*(?:night\s+mode)(?:\s+chalu\s+karo|\s+start)?\b"),
        "run_workflow",
        lambda m, text: {"workflow_name": "night_mode"},
    ),
    (
        re.compile(r"(?i)\b(?:start|run|launch|activate|chalu\s+karo)?\s*(?:focus\s+mode)(?:\s+chalu\s+karo|\s+start)?\b"),
        "run_workflow",
        lambda m, text: {"workflow_name": "focus_mode"},
    ),
    (
        re.compile(r"(?i)\b(?:start|run|launch|activate|organize|chalu\s+karo)?\s*(?:workspace\s+organization|organize\s+workspace)(?:\s+chalu\s+karo|\s+start)?\b"),
        "run_workflow",
        lambda m, text: {"workflow_name": "workspace_organization"},
    ),
    # Generic run workflow: "run workflow <name>" or "execute workflow <name>"
    (
        re.compile(r"(?i)\b(?:run\s+workflow|execute\s+workflow|start\s+workflow)\s+([a-zA-Z0-9_\-]+)\b"),
        "run_workflow",
        lambda m, text: {"workflow_name": m.group(1).strip().lower()},
    ),
    # ── Milestone 7.2: Local OCR & Text Extraction Intents ───────────────────
    (
        re.compile(r"(?i)\b(?:extract\s+text\s+from|read\s+text\s+from|ocr\s+image|ocr\s+file|text\s+extract\s+karo)\s+([^\s]+)\b"),
        "extract_text",
        lambda m, text: {"image_path": m.group(1).strip()},
    ),
    (
        re.compile(r"(?i)\b(?:what\s+does\s+this\s+image\s+say|is\s+image\s+me\s+kya\s+likha\s+hai)\s*(?:in\s+)?([^\s]+)?\b"),
        "extract_text",
        lambda m, text: {"image_path": m.group(1).strip() if m.group(1) else "latest"},
    ),
    (
        re.compile(r"(?i)\b(?:inspect\s+ocr\s+languages|check\s+ocr\s+languages|list\s+ocr\s+languages|ocr\s+languages)\b"),
        "inspect_ocr_languages",
        lambda m, text: {},
    ),
    (
        re.compile(r"(?i)\b(?:check\s+ocr\s+status|ocr\s+status|get\s+ocr\s+status)\b"),
        "get_ocr_engine_status",
        lambda m, text: {},
    ),
    # ── Milestone 7.3: Active Window & Desktop Context Intents ──────────────
    (
        re.compile(r"(?i)\b(?:which\s+app(?:lication)?(?:\s+am\s+i\s+using)?|what\s+app\s+is\s+this|kaunsa\s+app\s+hai)\b"),
        "get_active_window_context",
        lambda m, text: {},
    ),
    (
        re.compile(r"(?i)\b(?:what\s+window\s+is\s+currently\s+active|active\s+window|current\s+window|active\s+window\s+kya\s+hai)\b"),
        "get_active_window_context",
        lambda m, text: {},
    ),
    (
        re.compile(r"(?i)\b(?:which\s+monitor\s+am\s+i\s+using|which\s+monitor|which\s+display|display\s+layout|screen\s+layout)\b"),
        "get_display_layout",
        lambda m, text: {},
    ),
    (
        re.compile(r"(?i)\b(?:how\s+are\s+my\s+windows\s+arranged|window\s+layout|desktop\s+context|what\s+am\s+i\s+working\s+on|screen\s+par\s+kya\s+khula\s+hai)\b"),
        "get_desktop_context",
        lambda m, text: {},
    ),
    (
        re.compile(r"(?i)\b(?:current\s+window\s+ka\s+size|active\s+window\s+size|window\s+size\s+batao)\b"),
        "get_active_window_context",
        lambda m, text: {},
    ),
    # ── Milestone 7.4: Visual Document Understanding Intents ─────────────────
    (
        re.compile(r"(?i)\b(?:summarize\s+document|summarize\s+doc|summarize\s+pdf|document\s+summarize\s+karo)\s+([^\s]+)\b"),
        "summarize_document",
        lambda m, text: {"file_path": m.group(1).strip()},
    ),
    (
        re.compile(r"(?i)\b(?:inspect\s+document|inspect\s+doc|inspect\s+pdf|read\s+document|extract\s+document\s+text)\s+([^\s]+)\b"),
        "inspect_document",
        lambda m, text: {"file_path": m.group(1).strip()},
    ),
    # ── Milestone 7.5: Vision Privacy & Redaction Intents ────────────────────
    (
        re.compile(r"(?i)\b(?:redact\s+text|mask\s+sensitive\s+data|sanitize\s+text)\s+([^\s].*)\b"),
        "redact_text",
        lambda m, text: {"text": m.group(1).strip()},
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

    if act in ("capture_screenshot", "capture_screen") and isinstance(data, dict):
        if "error" in data:
            return f"Screenshot error: {data['error']}"
        if data.get("status") == "dry_run":
            return f"{data.get('message', '[DRY-RUN] Preview completed.')}"
        return f"Screenshot captured successfully ({data.get('mode')}, {data.get('file_size_bytes', 0)} bytes): {data.get('file_path')} (Saved in friday workspace/screenshots/)."

    if act == "check_screen_recording_permission" and isinstance(data, dict):
        if data.get("granted"):
            return f"Screen Recording Permission: Active ({data.get('message')})"
        return f"Screen Recording Permission: Denied. {data.get('guidance')}"

    if act == "discover_displays" and isinstance(data, list):
        lines = [f"• Display {d['index']}: {d['name']} ({d['resolution']}){' [Main]' if d.get('is_main') else ''}" for d in data]
        return f"Connected Displays ({len(data)}):\n" + "\n".join(lines)

    if act == "cancel_capture" and isinstance(data, dict):
        return f"Capture Cancel: {data.get('message')}"

    if act == "get_window_geometry" and isinstance(data, dict):
        return f"Frontmost Window: {data.get('app_name')} - '{data.get('window_title')}' [{data.get('width')}x{data.get('height')} at ({data.get('x')}, {data.get('y')})]"

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

    # ── Milestone 6.4 Formatters ─────────────────────────────────────────────
    if act in ("set_mute", "toggle_mute") and isinstance(data, dict):
        if "error" in data:
            return f"Audio mute error: {data['error']}"
        state = "Muted" if data.get("muted") else "Unmuted"
        return f"Audio output is now {state}."

    if act == "get_audio_devices" and isinstance(data, dict):
        devs = data.get("devices", [])
        lines = [f"• {d['name']} ({d['type']}){' [Default]' if d.get('default_output') or d.get('default_input') else ''}" for d in devs]
        return f"Audio Devices ({len(devs)} found):\n" + "\n".join(lines)

    if act == "set_audio_device" and isinstance(data, dict):
        if "error" in data:
            return f"Audio device error: {data['error']}"
        if data.get("status") == "unsupported":
            return data.get("message", "Switching device unsupported.")
        return f"Switched audio {data.get('type')} to '{data.get('device')}'."

    if act in ("get_brightness", "set_brightness") and isinstance(data, dict):
        if "error" in data:
            return f"Brightness error: {data['error']}"
        if data.get("status") == "unsupported":
            return f"Brightness notice: {data.get('message')}"
        return f"Display brightness is set to {data.get('brightness')}%."

    if act in ("set_appearance", "toggle_appearance") and isinstance(data, dict):
        if "error" in data:
            return f"Appearance error: {data['error']}"
        return f"macOS system appearance set to {data.get('appearance')} Mode."

    if act in ("get_focus_mode", "toggle_focus_mode") and isinstance(data, dict):
        return f"Focus mode: {data.get('message', data.get('focus_mode', 'Normal'))}."

    if act == "get_thermal" and isinstance(data, dict):
        throttled = " (Throttling active)" if data.get("throttling") else ""
        return f"Thermal state: {data.get('thermal_state')}{throttled}. {data.get('details')}"

    if act == "get_hardware_metrics" and isinstance(data, dict):
        return (
            f"Hardware Metrics: CPU: {data.get('cpu_percent')}% | "
            f"RAM: {data.get('ram_used_gb')}/{data.get('ram_total_gb')} GB ({data.get('ram_percent')}%) | "
            f"Disk: {data.get('disk_free_gb')} GB free ({data.get('disk_percent')}% used)."
        )

    if act == "get_wifi" and isinstance(data, dict):
        return f"Wi-Fi is {data.get('power')} (Connected SSID: {data.get('ssid', 'N/A')})."

    if act == "get_bluetooth" and isinstance(data, dict):
        return f"Bluetooth power is {data.get('power')}."

    if act in ("set_wifi_power", "set_bluetooth_power") and isinstance(data, dict):
        if "error" in data:
            return f"Connectivity error: {data['error']}"
        status_prefix = "[Simulated] " if data.get("status") == "simulated" else ""
        pwr = data.get("wifi_power") or data.get("bluetooth_power")
        target = "Wi-Fi" if "wifi_power" in data else "Bluetooth"
        return f"{status_prefix}{target} power set to {pwr}."

    if act in ("lock_screen", "system_sleep", "system_restart", "system_shutdown") and isinstance(data, dict):
        if "error" in data:
            return f"Power control error: {data['error']}"
        status_prefix = "[Simulated] " if data.get("status") == "simulated" else ""
        return f"{status_prefix}{data.get('message', 'Action completed.')}"

    if act == "generate_health_report" and isinstance(data, dict):
        if "error" in data:
            return f"Health report error: {data['error']}"
        return f"System health report generated: {data.get('file_path')} (Saved in friday workspace/reports/)."

    # ── Milestone 6.5 Workflow Formatters ────────────────────────────────────
    if act == "run_workflow" and isinstance(data, dict):
        if data.get("error"):
            rb = " (Changes rolled back)" if data.get("rolled_back") else ""
            return f"Workflow '{data.get('workflow_id')}' {data.get('status').lower()}: {data.get('error')}{rb}"
        return f"Workflow '{data.get('workflow_id')}' completed successfully ({data.get('successful_steps')}/{data.get('total_steps')} steps in {data.get('duration_s')}s)."

    if act == "list_workflows" and isinstance(data, dict):
        lines = []
        lines.append(f"Available Workflows ({data.get('total_count', 0)} total):")
        lines.append("Built-in:")
        for w in data.get("built_in", []):
            lines.append(f"  • {w['name']} ({w['id']}) - {w['description']} [{w['steps_count']} steps]")
        if data.get("custom"):
            lines.append("Custom:")
            for w in data.get("custom", []):
                lines.append(f"  • {w['name']} ({w['id']}) - {w['description']} [{w['steps_count']} steps]")
        return "\n".join(lines)

    if act == "stop_workflow" and isinstance(data, dict):
        return f"Workflow Stop: {data.get('message')}"

    if act == "create_workflow" and isinstance(data, dict):
        if "error" in data:
            return f"Create workflow error: {data['error']}"
        return f"Workflow '{data.get('id')}' saved successfully in workspace workflows."

    if act == "delete_workflow" and isinstance(data, dict):
        if "error" in data:
            return f"Delete workflow error: {data['error']}"
        return f"Workflow '{data.get('id')}' deleted successfully."

    # ── Milestone 7.2 OCR Formatters ─────────────────────────────────────────
    if act in ("extract_text", "ocr_image") and isinstance(data, dict):
        if data.get("error"):
            return f"OCR Extraction error: {data['error']}"
        warn_str = ""
        if data.get("has_prompt_injection"):
            warn_str = f"\n⚠️ Prompt Injection Alert: Neutralized suspicious command in text ({len(data.get('injection_warnings', []))} pattern matches)."
        export_str = f" (Saved to {data.get('export_path')})" if data.get("export_path") else ""
        return (
            f"Extracted Text [{data.get('engine', 'apple_vision')} | {data.get('latency_seconds', 0.0):.2f}s]{export_str}:\n"
            f"\"{data.get('text', '').strip()}\"{warn_str}"
        )

    if act == "inspect_ocr_languages" and isinstance(data, dict):
        v_langs = data.get("apple_vision", {}).get("supported_languages", [])
        v_count = len(v_langs)
        t_langs = data.get("tesseract", {}).get("supported_languages", [])
        sample_v = ", ".join(v_langs[:8]) + "..." if v_count > 8 else ", ".join(v_langs)
        return (
            f"OCR Capabilities:\n"
            f"  • Primary Engine: {data.get('primary_engine')}\n"
            f"  • Apple Vision Languages: {v_count} supported ({sample_v})\n"
            f"  • Tesseract Fallback: {', '.join(t_langs) if t_langs else 'None'}"
        )

    if act == "get_ocr_engine_status" and isinstance(data, dict):
        return (
            f"OCR Engine Status: {data.get('status').upper()}\n"
            f"  • Active Backend: {data.get('primary_engine')}\n"
            f"  • Hindi Supported: {data.get('hindi_supported')}\n"
            f"  • English Supported: {data.get('english_supported')}\n"
            f"  • Offline Confinement: {data.get('offline_only')}"
        )

    # ── Milestone 7.3 Desktop Context Formatters ─────────────────────────────
    if act == "get_active_window_context" and isinstance(data, dict):
        b = data.get("active_window_bounds", {})
        b_str = f"{int(b.get('width', 0))}x{int(b.get('height', 0))} at ({int(b.get('x', 0))}, {int(b.get('y', 0))})"
        fs_str = " [Fullscreen]" if data.get("is_fullscreen") else ""
        return (
            f"Active Application: **{data.get('frontmost_app_name')}** ({data.get('frontmost_bundle_id')})\n"
            f"Active Window: *'{data.get('active_window_title') or 'Untitled'}'*{fs_str}\n"
            f"Window Bounds: {b_str} (Display {data.get('active_window_display', 0)})"
        )

    if act == "get_desktop_context" and isinstance(data, dict):
        wins = data.get("visible_windows", [])
        w_lines = []
        for w in wins[:5]:
            w_lines.append(f"  • {w.get('owner_name')}: '{w.get('title')}' ({int(w.get('width', 0))}x{int(w.get('height', 0))})")
        wins_formatted = "\n".join(w_lines) if w_lines else "  • No visible windows detected"
        sc_cnt = len(data.get("screens", []))
        return (
            f"Desktop Context Summary:\n"
            f"  • Frontmost: {data.get('frontmost_app_name')} (PID {data.get('frontmost_pid')})\n"
            f"  • Active Window: '{data.get('active_window_title')}'\n"
            f"  • Displays: {sc_cnt} active screen(s)\n"
            f"Visible Windows ({len(wins)} total):\n{wins_formatted}"
        )

    if act == "get_display_layout" and isinstance(data, dict):
        sc_list = data.get("screens", [])
        lines = [f"Display Configuration ({data.get('screen_count', 0)} display(s)):"]
        for sc in sc_list:
            pri = " [Primary]" if sc.get("is_primary") else ""
            lines.append(f"  • Display {sc.get('index')}{pri}: {int(sc.get('width', 0))}x{int(sc.get('height', 0))} (Visible: {int(sc.get('visible_width', 0))}x{int(sc.get('visible_height', 0))})")
        return "\n".join(lines)

    # ── Milestone 7.4 Document Intelligence Formatters ───────────────────────
    if act == "inspect_document" and isinstance(data, dict):
        if data.get("error"):
            return f"Document error: {data['error']}"
        tbl_cnt = len(data.get("tables") or [])
        inj_str = "\n⚠️ Prompt Injection Alert: Neutralized suspicious instructions in document text." if data.get("has_prompt_injection") else ""
        return (
            f"Document Analysis: **{data.get('file_name')}** ({data.get('file_type')})\n"
            f"  • Pages: {data.get('page_count')} page(s)\n"
            f"  • Tables Detected: {tbl_cnt}\n"
            f"  • Extracted Text Sample:\n\"{data.get('full_text', '')[:300].strip()}...\"{inj_str}"
        )

    if act == "summarize_document" and isinstance(data, dict):
        return f"Summary for {data.get('file_path')}:\n{data.get('summary')}"

    if act == "ask_document" and isinstance(data, dict):
        return f"Q: {data.get('question')}\nA: {data.get('answer')}"

    return str(data)
