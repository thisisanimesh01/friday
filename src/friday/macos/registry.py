"""macOS Action Registry and Permission Framework for Milestone 6.1.

Defines:
- Risk tiers (READ_ONLY, LOW, MEDIUM, HIGH, CRITICAL)
- Strongly typed ActionDefinition with argument validation
- Central ActionRegistry for allowlisted macOS actions
- Execution policy enforcement with execution timeouts and dry-run simulation
- Structured, privacy-safe audit logging
"""

from __future__ import annotations

import enum
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from logger import get_logger

logger = get_logger("MacOSControl")


class RiskTier(str, enum.Enum):
    READ_ONLY = "READ_ONLY"      # System info, battery, volume read, app listing
    LOW = "LOW"                  # Non-destructive UI adjustments (volume set, brightness)
    MEDIUM = "MEDIUM"            # Application launch, opening files in apps
    HIGH = "HIGH"                # Closing apps, clipboard write, killing processes
    CRITICAL = "CRITICAL"        # System sleep, lock, restarts, deletions


@dataclass
class ActionResult:
    success: bool
    data: Any = None
    error: str | None = None
    action_name: str = ""
    risk: str = RiskTier.READ_ONLY.value
    duration_s: float = 0.0
    dry_run: bool = False
    requires_confirmation: bool = False
    confirmation_prompt: str | None = None


@dataclass
class ActionDefinition:
    name: str
    description: str
    risk: RiskTier
    handler: Callable[..., Any]
    arg_schema: dict[str, type] = field(default_factory=dict)
    timeout_s: float = 5.0
    requires_confirmation: bool = False

    def validate_args(self, kwargs: dict[str, Any]) -> tuple[bool, str | None]:
        for arg_name, expected_type in self.arg_schema.items():
            if arg_name in kwargs:
                val = kwargs[arg_name]
                if not isinstance(val, expected_type):
                    return False, f"Argument '{arg_name}' must be of type {expected_type.__name__}, got {type(val).__name__}."
        return True, None


class ActionRegistry:
    def __init__(self):
        self._actions: dict[str, ActionDefinition] = {}

    def register(self, action: ActionDefinition):
        self._actions[action.name] = action
        logger.debug(f"Registered macOS action: {action.name} [{action.risk.value}]")

    def get(self, name: str) -> ActionDefinition | None:
        return self._actions.get(name)

    def list_actions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": act.name,
                "description": act.description,
                "risk": act.risk.value,
                "timeout_s": act.timeout_s,
                "requires_confirmation": act.requires_confirmation,
            }
            for act in self._actions.values()
        ]

    def execute(
        self,
        name: str,
        dry_run: bool = False,
        confirmed: bool = False,
        **kwargs: Any,
    ) -> ActionResult:
        act = self.get(name)
        if not act:
            return ActionResult(
                success=False,
                error=f"Unrecognized or disallowed macOS action '{name}'.",
                action_name=name,
            )

        # 1. Argument validation
        valid, err = act.validate_args(kwargs)
        if not valid:
            return ActionResult(
                success=False,
                error=f"Argument validation failed: {err}",
                action_name=name,
                risk=act.risk.value,
            )

        # 2. Risk & confirmation checks
        needs_confirm = act.requires_confirmation or act.risk in (RiskTier.HIGH, RiskTier.CRITICAL)
        if needs_confirm and not confirmed and not dry_run:
            prompt = f"Confirmation required to execute {act.risk.value} action '{name}' on macOS."
            return ActionResult(
                success=False,
                requires_confirmation=True,
                confirmation_prompt=prompt,
                action_name=name,
                risk=act.risk.value,
            )

        # 3. Dry-run simulation
        if dry_run:
            return ActionResult(
                success=True,
                data=f"[DRY-RUN] Simulated execution of '{name}' with args {kwargs}",
                action_name=name,
                risk=act.risk.value,
                dry_run=True,
            )

        # 4. Timed execution with timeout guard
        t0 = time.time()
        try:
            res = act.handler(**kwargs)
            duration = time.time() - t0
            record_audit_log(name, act.risk.value, kwargs, success=True, duration_s=duration)
            return ActionResult(
                success=True,
                data=res,
                action_name=name,
                risk=act.risk.value,
                duration_s=duration,
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - t0
            record_audit_log(name, act.risk.value, kwargs, success=False, error="TimeoutExpired", duration_s=duration)
            return ActionResult(
                success=False,
                error=f"Execution of action '{name}' timed out after {act.timeout_s}s.",
                action_name=name,
                risk=act.risk.value,
                duration_s=duration,
            )
        except Exception as e:
            duration = time.time() - t0
            record_audit_log(name, act.risk.value, kwargs, success=False, error=str(e), duration_s=duration)
            return ActionResult(
                success=False,
                error=f"Action execution error: {e}",
                action_name=name,
                risk=act.risk.value,
                duration_s=duration,
            )


# ── Audit Logging ─────────────────────────────────────────────────────────────
AUDIT_LOG_FILE = Path.home() / "Library" / "Application Support" / "Friday" / "logs" / "macos_actions.jsonl"


def record_audit_log(
    action_name: str,
    risk: str,
    params: dict[str, Any],
    success: bool,
    error: str | None = None,
    duration_s: float = 0.0,
):
    """Write a privacy-sanitized structured audit record to disk."""
    try:
        # Sanitize parameters against sensitive info
        sanitized_params = {}
        for k, v in params.items():
            if any(s in k.lower() for s in ("key", "pass", "token", "auth", "secret")):
                sanitized_params[k] = "[REDACTED]"
            else:
                sanitized_params[k] = str(v)[:100]

        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "action": action_name,
            "risk": risk,
            "params": sanitized_params,
            "success": success,
            "error": error,
            "duration_s": round(duration_s, 4),
        }
        AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.debug(f"Failed to record audit log: {e}")


# ── Built-in Harmless macOS Handlers ───────────────────────────────────────────
def get_system_battery() -> dict[str, Any]:
    """Read macOS battery percentage and charging status via pmset."""
    try:
        out = subprocess.check_output(["pmset", "-g", "batt"], text=True, timeout=3.0)
        percent_match = re.search(r"(\d+)%", out)
        lower_out = out.lower()
        is_discharging = "discharging" in lower_out
        is_charging = ("charging" in lower_out or "ac power" in lower_out) and not is_discharging
        percent = int(percent_match.group(1)) if percent_match else None
        return {"percentage": percent, "is_charging": is_charging, "raw": out.strip()}
    except Exception as e:
        return {"error": str(e)}


def get_system_volume() -> dict[str, Any]:
    """Read macOS audio output volume via AppleScript."""
    try:
        script = "output volume of (get volume settings)"
        out = subprocess.check_output(["osascript", "-e", script], text=True, timeout=3.0).strip()
        return {"volume": int(out)}
    except Exception as e:
        return {"error": str(e)}


def set_system_volume(level: int) -> dict[str, Any]:
    """Set macOS audio output volume (0 - 100)."""
    level = max(0, min(100, int(level)))
    script = f"set volume output volume {level}"
    subprocess.check_call(["osascript", "-e", script], timeout=3.0)
    return {"volume": level, "status": "updated"}


def get_running_applications() -> list[str]:
    """List names of currently running front-facing GUI applications via AppleScript."""
    try:
        script = 'tell application "System Events" to get name of every process whose visible is true'
        out = subprocess.check_output(["osascript", "-e", script], text=True, timeout=3.0).strip()
        apps = [app.strip() for app in out.split(",") if app.strip()]
        return apps
    except Exception as e:
        return [f"Error listing applications: {e}"]


def get_macos_appearance() -> dict[str, Any]:
    """Check if macOS is currently in Dark Mode or Light Mode."""
    try:
        script = 'tell application "System Events" to tell appearance preferences to get dark mode'
        out = subprocess.check_output(["osascript", "-e", script], text=True, timeout=3.0).strip()
        is_dark = out.lower() == "true"
        return {"dark_mode": is_dark, "appearance": "Dark" if is_dark else "Light"}
    except Exception as e:
        return {"error": str(e)}


def get_system_storage() -> dict[str, Any]:
    """Read filesystem disk capacity and usage."""
    try:
        stat = os.statvfs("/")
        total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        used_gb = total_gb - free_gb
        return {
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "used_percent": round((used_gb / total_gb) * 100, 1),
        }
    except Exception as e:
        return {"error": str(e)}


# ── Global Registry Setup ─────────────────────────────────────────────────────
def create_default_registry() -> ActionRegistry:
    reg = ActionRegistry()

    # 1. Battery status
    reg.register(
        ActionDefinition(
            name="get_battery",
            description="Get macOS battery level and charging status.",
            risk=RiskTier.READ_ONLY,
            handler=get_system_battery,
        )
    )

    # 2. Volume read
    reg.register(
        ActionDefinition(
            name="get_volume",
            description="Get current macOS output volume level.",
            risk=RiskTier.READ_ONLY,
            handler=get_system_volume,
        )
    )

    # 3. Volume set
    reg.register(
        ActionDefinition(
            name="set_volume",
            description="Set macOS output volume level (0 - 100).",
            risk=RiskTier.LOW,
            handler=set_system_volume,
            arg_schema={"level": int},
        )
    )

    # 4. List running GUI apps
    reg.register(
        ActionDefinition(
            name="list_apps",
            description="List visible running applications on macOS.",
            risk=RiskTier.READ_ONLY,
            handler=get_running_applications,
        )
    )

    # 5. Get Dark/Light mode appearance
    reg.register(
        ActionDefinition(
            name="get_appearance",
            description="Get macOS system appearance (Dark or Light Mode).",
            risk=RiskTier.READ_ONLY,
            handler=get_macos_appearance,
        )
    )

    # 6. Storage info
    reg.register(
        ActionDefinition(
            name="get_storage",
            description="Get macOS root disk total, used, and free space.",
            risk=RiskTier.READ_ONLY,
            handler=get_system_storage,
        )
    )

    # ── Milestone 6.2 Actions ─────────────────────────────────────────────────
    from macos.apps_windows import (
        get_active_application,
        hide_application,
        launch_application,
        minimize_window,
        position_window,
        quit_application,
        restore_window,
        switch_application,
        toggle_fullscreen_window,
    )
    from macos.media_capture import capture_camera_photo, capture_screenshot

    # 7. Launch application
    reg.register(
        ActionDefinition(
            name="launch_app",
            description="Launch an installed macOS application.",
            risk=RiskTier.MEDIUM,
            handler=launch_application,
            arg_schema={"app_name": str},
        )
    )

    # 8. Quit application (graceful or forced)
    reg.register(
        ActionDefinition(
            name="quit_app",
            description="Quit a running macOS application (force-quit requires confirmation).",
            risk=RiskTier.HIGH,
            handler=quit_application,
            arg_schema={"app_name": str, "force": bool},
            requires_confirmation=False,  # Checked dynamically for force=True
        )
    )

    # 9. Switch application
    reg.register(
        ActionDefinition(
            name="switch_app",
            description="Switch to and activate a target macOS application.",
            risk=RiskTier.LOW,
            handler=switch_application,
            arg_schema={"app_name": str},
        )
    )

    # 10. Hide application
    reg.register(
        ActionDefinition(
            name="hide_app",
            description="Hide an application or the active frontmost application.",
            risk=RiskTier.LOW,
            handler=hide_application,
            arg_schema={"app_name": str},
        )
    )

    # 11. Get active application
    reg.register(
        ActionDefinition(
            name="get_active_app",
            description="Get the frontmost active application name on macOS.",
            risk=RiskTier.READ_ONLY,
            handler=get_active_application,
        )
    )

    # 12. Minimize window
    reg.register(
        ActionDefinition(
            name="minimize_window",
            description="Minimize the front window of an application or the active window.",
            risk=RiskTier.LOW,
            handler=minimize_window,
            arg_schema={"app_name": str},
        )
    )

    # 13. Restore window
    reg.register(
        ActionDefinition(
            name="restore_window",
            description="Restore/unminimize the window of an application.",
            risk=RiskTier.LOW,
            handler=restore_window,
            arg_schema={"app_name": str},
        )
    )

    # 14. Fullscreen window
    reg.register(
        ActionDefinition(
            name="fullscreen_window",
            description="Toggle full-screen mode on the frontmost window.",
            risk=RiskTier.LOW,
            handler=toggle_fullscreen_window,
            arg_schema={"app_name": str},
        )
    )

    # 15. Position window (left, right, center, maximize)
    reg.register(
        ActionDefinition(
            name="position_window",
            description="Position and snap window (left_half, right_half, center, maximize).",
            risk=RiskTier.LOW,
            handler=position_window,
            arg_schema={"position": str, "app_name": str},
        )
    )

    # 16. Capture camera photo (explicit on-demand, saved strictly to friday workspace/camera/)
    reg.register(
        ActionDefinition(
            name="capture_photo",
            description="Capture single on-demand camera photo to friday workspace/camera/.",
            risk=RiskTier.MEDIUM,
            handler=capture_camera_photo,
            arg_schema={"filename": str},
        )
    )

    # 17. Capture screenshot (explicit on-demand, saved strictly to friday workspace/screenshots/)
    reg.register(
        ActionDefinition(
            name="capture_screenshot",
            description="Capture single screenshot to friday workspace/screenshots/.",
            risk=RiskTier.MEDIUM,
            handler=capture_screenshot,
            arg_schema={"mode": str, "filename": str, "target_window": str},
        )
    )

    return reg


default_registry = create_default_registry()
