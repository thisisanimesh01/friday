"""Modular AppleScript Templates and Execution Framework for Milestone 6.3.

Security and Privacy Invariants:
1. STRICTLY ALLOWLISTED TEMPLATES ONLY:
   - FRIDAY NEVER executes raw, unvalidated, or LLM-generated AppleScript / JXA code.
   - Every automation is instantiated from a predefined, reviewed template.
2. ARGUMENT VALIDATION & SANITIZATION:
   - All string arguments are checked against PrivacyGuard. If any argument references
     'me and she' or blocked personal repositories, it is rejected before execution.
   - Parameter values are sanitized against AppleScript quotation injection.
3. OUTPUT WORKSPACE CONFINEMENT:
   - Any script producing a file or document is confined strictly to:
     ~/Desktop/friday workspace/
4. TIMEOUT & SUBPROCESS TREE TERMINATION:
   - Execution uses process groups (os.setsid / os.killpg) to terminate the entire process
     tree upon timeout or cancellation.
5. OS-LEVEL ACCESSIBILITY & AUTOMATION HANDLING:
   - Catches macOS permission errors (-1719, -1743) gracefully without crashing.
"""

from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable

from logger import get_logger
from security.privacy_guard import (
    is_path_permanently_protected,
)

logger = get_logger("MacOSAutomation")


def _sanitize_applescript_arg(val: Any) -> str:
    """Escape characters for safe insertion into AppleScript double-quoted string literals."""
    if val is None:
        return ""
    s = str(val)
    # Check against privacy guard first
    if is_path_permanently_protected(s):
        raise PermissionError(f"Access denied: Argument references protected location: {s}")
    # Escape backslashes and double quotes
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    # Prevent newline breakouts in string literals
    escaped = escaped.replace("\r", " ").replace("\n", " ")
    return escaped


def run_compiled_applescript(
    script_source: str,
    timeout_s: float = 5.0,
) -> tuple[bool, str, str]:
    """Execute AppleScript via osascript with process-group timeout cancellation.

    Returns:
        (success: bool, stdout: str, stderr: str)
    """
    # Pre-execution check: Ensure no reference to protected targets in the script
    if "me and she" in script_source.lower() or "me_and_she" in script_source.lower():
        return False, "", "Privacy Violation: AppleScript references permanently protected folder 'me and she'."

    # Pre-execution check: block shell execution or privilege escalation
    forbidden_tokens = ["do shell script", "administrator privileges", "sudo", "rm -rf"]
    for token in forbidden_tokens:
        if token in script_source.lower():
            return False, "", f"Security Violation: Prohibited token '{token}' detected in AppleScript."

    try:
        proc = subprocess.Popen(
            ["osascript", "-e", script_source],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,  # Create process group for child tree cleanup
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
            success = proc.returncode == 0
            return success, stdout.strip(), stderr.strip()
        except subprocess.TimeoutExpired:
            # Terminate the entire process group
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass
            proc.kill()
            proc.wait()
            return False, "", f"Execution timed out after {timeout_s}s (child process tree terminated)."
    except Exception as e:
        return False, "", str(e)


# ── Allowlisted AppleScript Templates ──────────────────────────────────────────

@dataclass
class AppleScriptTemplate:
    name: str
    description: str
    builder: Callable[..., str]
    param_schema: dict[str, type] = field(default_factory=dict)
    timeout_s: float = 5.0
    requires_confirmation: bool = False


# Template 1: Display system dialog / notification
def _build_display_notification(title: str = "FRIDAY", message: str = "", sound: str = "") -> str:
    s_title = _sanitize_applescript_arg(title)
    s_msg = _sanitize_applescript_arg(message)
    s_sound = f' sound name "{_sanitize_applescript_arg(sound)}"' if sound else ""
    return f'display notification "{s_msg}" with title "{s_title}"{s_sound}'


# Template 2: Create a quick note in Apple Notes
def _build_create_apple_note(title: str, body: str = "") -> str:
    s_title = _sanitize_applescript_arg(title)
    s_body = _sanitize_applescript_arg(body)
    return f'''
    tell application "Notes"
        activate
        tell default account
            make new note at folder "Notes" with properties {{name:"{s_title}", body:"{s_body}"}}
        end tell
    end tell
    '''


# Template 3: Toggle music playback (Music.app)
def _build_music_play_pause() -> str:
    return '''
    tell application "Music"
        playpause
    end tell
    '''


# Template 4: Set system output volume via AppleScript
def _build_set_volume(level: int) -> str:
    lvl = max(0, min(100, int(level)))
    return f"set volume output volume {lvl}"


# Template 5: Empty macOS Trash (Destructive: requires confirmation)
def _build_empty_trash() -> str:
    return 'tell application "Finder" to empty trash'


# Template 6: Get currently playing track in Music.app
def _build_get_current_track() -> str:
    return '''
    if application "Music" is running then
        tell application "Music"
            if player state is playing then
                set trackName to name of current track
                set artistName to artist of current track
                return trackName & " by " & artistName
            else
                return "Paused"
            end if
        end tell
    else
        return "Music.app is not running"
    end if
    '''


# Template Registry
APPLESCRIPT_TEMPLATES: dict[str, AppleScriptTemplate] = {
    "display_notification": AppleScriptTemplate(
        name="display_notification",
        description="Display a native macOS banner notification.",
        builder=_build_display_notification,
        param_schema={"title": str, "message": str, "sound": str},
        timeout_s=3.0,
    ),
    "create_note": AppleScriptTemplate(
        name="create_note",
        description="Create a new note in Apple Notes.",
        builder=_build_create_apple_note,
        param_schema={"title": str, "body": str},
        timeout_s=5.0,
    ),
    "music_play_pause": AppleScriptTemplate(
        name="music_play_pause",
        description="Play or pause current track in Music.app.",
        builder=_build_music_play_pause,
        timeout_s=3.0,
    ),
    "get_current_track": AppleScriptTemplate(
        name="get_current_track",
        description="Get currently playing track info from Music.app.",
        builder=_build_get_current_track,
        timeout_s=3.0,
    ),
    "set_volume": AppleScriptTemplate(
        name="set_volume",
        description="Set macOS output volume (0-100).",
        builder=_build_set_volume,
        param_schema={"level": int},
        timeout_s=3.0,
    ),
    "empty_trash": AppleScriptTemplate(
        name="empty_trash",
        description="Empty macOS system Trash (destructive).",
        builder=_build_empty_trash,
        timeout_s=5.0,
        requires_confirmation=True,
    ),
}


def execute_template(
    template_name: str,
    params: dict[str, Any] | None = None,
    dry_run: bool = False,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Execute a predefined allowlisted AppleScript template.

    Parameters:
        template_name: Key in APPLESCRIPT_TEMPLATES.
        params: Arguments matching template's param_schema.
        dry_run: If True, previews script without running.
        confirmed: Confirmation for destructive templates.
    """
    tmpl = APPLESCRIPT_TEMPLATES.get(template_name)
    if not tmpl:
        return {"error": f"Template '{template_name}' not allowlisted or recognized."}

    params = params or {}

    # Validate argument types and schemas
    for arg_name, expected_type in tmpl.param_schema.items():
        if arg_name in params:
            val = params[arg_name]
            if not isinstance(val, expected_type):
                return {
                    "error": f"Argument '{arg_name}' must be of type {expected_type.__name__}, got {type(val).__name__}."
                }
            # Deep check string against privacy guard
            if isinstance(val, str) and is_path_permanently_protected(val):
                return {
                    "error": f"Privacy violation: Argument '{arg_name}' points to protected privacy location."
                }

    # Destructive confirmation check
    if tmpl.requires_confirmation and not confirmed and not dry_run:
        return {
            "requires_confirmation": True,
            "prompt": f"Confirmation required to execute destructive automation '{template_name}'.",
            "template": template_name,
        }

    try:
        script = tmpl.builder(**params)
    except PermissionError as pe:
        return {"error": f"Privacy restriction: {pe}"}
    except Exception as e:
        return {"error": f"Failed to build script template: {e}"}

    if dry_run:
        return {
            "status": "dry_run",
            "template": template_name,
            "params": params,
            "script_preview": script.strip(),
        }

    success, stdout, stderr = run_compiled_applescript(script, timeout_s=tmpl.timeout_s)
    if success:
        return {
            "status": "success",
            "template": template_name,
            "output": stdout or "Executed successfully.",
        }
    else:
        # Check for standard permission error codes
        if "-1719" in stderr or "-1743" in stderr:
            return {
                "error": f"macOS Accessibility or Automation permission required in System Settings: {stderr}"
            }
        return {"error": f"Execution failed: {stderr or 'Unknown error'}"}
