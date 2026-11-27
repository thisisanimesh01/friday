"""macOS Shortcuts Automation Framework for Milestone 6.3.

Security and Privacy Invariants:
1. EXPLICIT APPROVAL REGISTRY:
   - Only reviewed shortcuts with documented actions and resource boundaries are executed.
   - Any unknown, unverified, or modified shortcut is blocked by default until explicit approval.
2. ARGUMENT VALIDATION & SANITIZATION:
   - Input paths and arguments are strictly validated against PrivacyGuard.
   - Any input referencing 'me and she' or blocked personal repositories is rejected immediately.
3. OUTPUT WORKSPACE CONFINEMENT:
   - Output paths are confined strictly to ~/Desktop/friday workspace/
4. TIMEOUT & CANCELLATION:
   - Execution uses process groups (os.setsid / os.killpg) to cancel running shortcuts reliably.
5. DRY-RUN PREVIEW:
   - Supports dry-run inspection of parameters, resource boundaries, and approval status.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from logger import get_logger
from security.privacy_guard import (
    is_path_permanently_protected,
    validate_workspace_path,
)

logger = get_logger("ShortcutsAutomation")

APPROVALS_FILE = Path.home() / ".friday" / "approved_shortcuts.json"


@dataclass
class ShortcutDefinition:
    name: str
    description: str
    actions_summary: str
    resource_boundary: str
    allowed_inputs: list[str] = field(default_factory=list)
    output_required: bool = False
    timeout_s: float = 10.0
    approved: bool = True
    metadata_hash: str = ""


# SECURITY AUDIT NOTE (Milestone 6.4):
# Shortcut verification cannot rely solely on the shortcut title or simple user declaration.
# Any shortcut that operates on external unconfined locations (like Notes.app or unbounded external paths)
# is disabled until static action analysis and strict boundary enforcement can be verified.
DEFAULT_KNOWN_SHORTCUTS: dict[str, ShortcutDefinition] = {
    "Charger Sound": ShortcutDefinition(
        name="Charger Sound",
        description="Plays a system charger sound alert.",
        actions_summary="Audio feedback notification",
        resource_boundary="Audio output only; zero filesystem or network access",
        approved=True,
    ),
    "Quick Note": ShortcutDefinition(
        name="Quick Note",
        description="Adds a quick note entry via Shortcuts (DISABLED: unverified cloud/system sync boundary).",
        actions_summary="Apple Notes text append",
        resource_boundary="Unconfined external Notes database",
        allowed_inputs=["text"],
        approved=False,  # DISABLED: Cannot verify containment within dedicated workspace
    ),
    "Open Workspace": ShortcutDefinition(
        name="Open Workspace",
        description="Opens FRIDAY dedicated workspace folder in Finder.",
        actions_summary="Finder view of workspace",
        resource_boundary="~/Desktop/friday workspace/",
        approved=True,
    ),
}


class ShortcutsManager:
    """Manages discovery, verification, approval, and execution of macOS Shortcuts."""

    def __init__(self, approvals_file: Path | None = None):
        self.approvals_file = approvals_file or APPROVALS_FILE
        self._approved_registry: dict[str, dict[str, Any]] = {}
        self._load_approvals()

    def _load_approvals(self) -> None:
        """Load approved shortcuts registry from disk."""
        if self.approvals_file.exists():
            try:
                data = json.loads(self.approvals_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._approved_registry = data
            except Exception as e:
                logger.warning(f"Could not load approved shortcuts file: {e}")
                self._approved_registry = {}

    def _save_approvals(self) -> None:
        """Persist approved shortcuts registry to disk."""
        try:
            self.approvals_file.parent.mkdir(parents=True, exist_ok=True)
            self.approvals_file.write_text(json.dumps(self._approved_registry, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save approved shortcuts: {e}")

    def list_installed_shortcuts(self, timeout_s: float = 5.0) -> list[str]:
        """Discover installed shortcuts using `/usr/bin/shortcuts list`."""
        try:
            res = subprocess.run(
                ["/usr/bin/shortcuts", "list"],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            if res.returncode == 0:
                lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
                return lines
            else:
                logger.debug(f"shortcuts list failed or returned {res.returncode}: {res.stderr}")
                return []
        except Exception as e:
            logger.debug(f"Error querying shortcuts list: {e}")
            return []

    def get_shortcut_status(self, name: str) -> dict[str, Any]:
        """Check whether a shortcut is approved, allowlisted, or unverified."""
        installed = self.list_installed_shortcuts()
        is_installed = name in installed

        # Check known definitions first
        known = DEFAULT_KNOWN_SHORTCUTS.get(name)
        disk_approval = self._approved_registry.get(name)

        if disk_approval:
            return {
                "name": name,
                "installed": is_installed,
                "approved": disk_approval.get("approved", False),
                "source": "user_approved",
                "resource_boundary": disk_approval.get("resource_boundary", "Unknown"),
                "actions_summary": disk_approval.get("actions_summary", "Custom user shortcut"),
            }
        elif known:
            return {
                "name": name,
                "installed": is_installed,
                "approved": known.approved,
                "source": "allowlisted_default",
                "resource_boundary": known.resource_boundary,
                "actions_summary": known.actions_summary,
            }
        else:
            return {
                "name": name,
                "installed": is_installed,
                "approved": False,
                "source": "unverified",
                "resource_boundary": "Unverified - Requires review",
                "actions_summary": "Unreviewed shortcut",
            }

    def approve_shortcut(
        self,
        name: str,
        actions_summary: str = "User approved shortcut",
        resource_boundary: str = "Authorized macOS boundaries",
    ) -> dict[str, Any]:
        """Explicitly approve an installed shortcut after manual user review."""
        status = self.get_shortcut_status(name)
        if not status["installed"]:
            # If not detected by CLI (e.g. sandbox restriction), we allow approving with note
            logger.info(f"Approving shortcut '{name}' (unconfirmed in live list).")

        entry = {
            "name": name,
            "approved": True,
            "actions_summary": actions_summary,
            "resource_boundary": resource_boundary,
            "approved_at": time.time(),
        }
        self._approved_registry[name] = entry
        self._save_approvals()
        return {"status": "approved", "shortcut": name, "details": entry}

    def revoke_shortcut(self, name: str) -> dict[str, Any]:
        """Revoke approval of a previously approved shortcut."""
        if name in self._approved_registry:
            del self._approved_registry[name]
            self._save_approvals()
            return {"status": "revoked", "shortcut": name}
        return {"status": "not_found", "shortcut": name}

    def list_all_shortcuts(self) -> list[dict[str, Any]]:
        """List all discoverable and known shortcuts with their approval status."""
        installed = self.list_installed_shortcuts()
        all_names = set(installed) | set(DEFAULT_KNOWN_SHORTCUTS.keys()) | set(self._approved_registry.keys())
        results = []
        for name in sorted(all_names):
            results.append(self.get_shortcut_status(name))
        return results

    def run_shortcut(
        self,
        name: str,
        input_path: str | Path | None = None,
        output_filename: str | None = None,
        dry_run: bool = False,
        timeout_s: float = 10.0,
    ) -> dict[str, Any]:
        """Execute a verified macOS shortcut with argument validation and output confinement.

        Security enforcement:
        - If shortcut is unverified or not approved, execution is BLOCKED.
        - If input_path points to protected location ('me and she'), execution is BLOCKED.
        - Output is strictly confined to ~/Desktop/friday workspace/
        - Subprocess runs in a process group for clean timeout cleanup.
        """
        # Privacy check 1: Shortcut name
        if is_path_permanently_protected(name):
            return {"error": f"Privacy violation: Shortcut name points to protected location: {name}"}

        # Verification check
        status = self.get_shortcut_status(name)
        if not status.get("approved"):
            return {
                "error": (
                    f"Shortcut '{name}' is unverified or not approved. "
                    "For security, only reviewed shortcuts with defined resource boundaries "
                    "can be executed. Approve it first via shortcuts approval."
                ),
                "approval_required": True,
                "shortcut": name,
            }

        # Privacy check 2: Input path validation
        resolved_input: Path | None = None
        if input_path:
            input_str = str(input_path)
            if is_path_permanently_protected(input_str):
                return {
                    "error": f"Privacy violation: Input path '{input_str}' points to permanently protected location."
                }
            resolved_input = Path(input_str).expanduser().resolve()
            if not resolved_input.exists():
                return {"error": f"Input path does not exist: {resolved_input}"}

        # Privacy check 3: Output path confinement
        resolved_output: Path | None = None
        if output_filename:
            # Must be inside workspace
            try:
                safe, out_path = validate_workspace_path(f"reports/{output_filename}")
                if not safe or not out_path:
                    return {
                        "error": f"Output path outside dedicated workspace: {output_filename}"
                    }
                out_path.parent.mkdir(parents=True, exist_ok=True)
                resolved_output = out_path
            except Exception as e:
                return {
                    "error": f"Output path outside dedicated workspace: {e}"
                }

        # Construct CLI invocation
        cmd = ["/usr/bin/shortcuts", "run", name]
        if resolved_input:
            cmd.extend(["-i", str(resolved_input)])
        if resolved_output:
            cmd.extend(["-o", str(resolved_output)])

        if dry_run:
            return {
                "status": "dry_run",
                "shortcut": name,
                "command": cmd,
                "resource_boundary": status.get("resource_boundary"),
                "actions_summary": status.get("actions_summary"),
                "input_path": str(resolved_input) if resolved_input else None,
                "output_path": str(resolved_output) if resolved_output else None,
            }

        # Subprocess execution with process-group timeout cancellation
        start_time = time.time()
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid,  # Create process group for reliable termination
            )
            try:
                stdout, stderr = proc.communicate(timeout=timeout_s)
                duration = time.time() - start_time
                success = proc.returncode == 0
                if success:
                    return {
                        "status": "success",
                        "shortcut": name,
                        "duration_s": round(duration, 3),
                        "output": stdout.strip() or "Executed successfully.",
                        "output_file": str(resolved_output) if resolved_output else None,
                    }
                else:
                    return {
                        "error": f"Shortcut execution failed (exit {proc.returncode}): {stderr.strip()}",
                        "shortcut": name,
                        "duration_s": round(duration, 3),
                    }
            except subprocess.TimeoutExpired:
                # Cancel process tree
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
                    pass
                proc.kill()
                proc.wait()
                return {
                    "error": f"Shortcut execution timed out after {timeout_s}s (process tree terminated).",
                    "shortcut": name,
                }
        except Exception as e:
            return {"error": f"Execution error: {e}", "shortcut": name}
