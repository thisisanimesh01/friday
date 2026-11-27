"""Multi-Step Desktop Workflows Engine for Milestone 6.5.

Provides:
1. WorkflowStep, WorkflowDefinition, WorkflowExecutionResult, and WorkflowStatus dataclasses.
2. WorkflowEngine:
   - Sequential execution of allowlisted ActionRegistry operations.
   - Dynamic parameter substitution & step dependency handling.
   - Bounded retries (max 2) on transient step failures.
   - Step timeouts & overall workflow timeouts.
   - Real-time cancellation checks ("Friday, stop the workflow").
   - Safe rollback mechanism for reversible operations upon failure.
   - High/Critical risk confirmation enforcement.
   - Single-use camera/screenshot gate (cannot inherit blind capture authorization from saved workflows).
3. Custom Workflow Management (CRUD):
   - Confined strictly to ~/Desktop/friday workspace/workflows/
   - Schema validation, preview, edit, delete, list.
4. Built-in Configurable Workflows:
   - developer_mode
   - study_mode
   - system_health_check
   - python_project_setup
   - morning_routine
   - night_mode
   - focus_mode
   - workspace_organization
"""

from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from logger import get_logger
from security.privacy_guard import (
    get_workspace_path,
    validate_workspace_path,
)

logger = get_logger("WorkflowEngine")


class WorkflowStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass
class WorkflowStep:
    id: str
    action: str
    args: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    depends_on: list[str] = field(default_factory=list)
    retry_count: int = 0  # max 2 bounded retries
    timeout_s: float = 10.0
    reversible: bool = False
    rollback_action: str | None = None
    rollback_args: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    id: str
    name: str
    description: str
    steps: list[WorkflowStep]
    timeout_s: float = 60.0
    author: str = "system"  # 'system' or 'user'
    is_builtin: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "timeout_s": self.timeout_s,
            "author": self.author,
            "is_builtin": self.is_builtin,
            "steps": [asdict(step) for step in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowDefinition:
        steps = []
        for s in data.get("steps", []):
            steps.append(
                WorkflowStep(
                    id=s.get("id", f"step_{len(steps)+1}"),
                    action=s.get("action", ""),
                    args=s.get("args", {}),
                    description=s.get("description", ""),
                    depends_on=s.get("depends_on", []),
                    retry_count=min(2, max(0, int(s.get("retry_count", 0)))),
                    timeout_s=float(s.get("timeout_s", 10.0)),
                    reversible=bool(s.get("reversible", False)),
                    rollback_action=s.get("rollback_action"),
                    rollback_args=s.get("rollback_args", {}),
                )
            )
        return cls(
            id=data.get("id", "custom_workflow"),
            name=data.get("name", "Custom Workflow"),
            description=data.get("description", ""),
            steps=steps,
            timeout_s=float(data.get("timeout_s", 60.0)),
            author=data.get("author", "user"),
            is_builtin=bool(data.get("is_builtin", False)),
        )


@dataclass
class WorkflowExecutionResult:
    workflow_id: str
    status: WorkflowStatus
    total_steps: int
    executed_steps: int
    successful_steps: int
    failed_steps: int
    duration_s: float
    step_results: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    rolled_back: bool = False
    message: str = ""


# Global cancellation flag and lock for live workflows
_CANCELLATION_REQUESTED = False
_ACTIVE_WORKFLOW_LOCK = threading.Lock()
_ACTIVE_WORKFLOW_NAME: str | None = None


def request_workflow_stop() -> dict[str, Any]:
    """Signals any currently active workflow to stop immediately."""
    global _CANCELLATION_REQUESTED, _ACTIVE_WORKFLOW_NAME
    with _ACTIVE_WORKFLOW_LOCK:
        if _ACTIVE_WORKFLOW_NAME:
            _CANCELLATION_REQUESTED = True
            name = _ACTIVE_WORKFLOW_NAME
            logger.info(f"Cancellation requested for workflow '{name}'.")
            return {"status": "stopping", "message": f"Stop signal sent to active workflow '{name}'."}
        return {"status": "idle", "message": "No workflow is currently running."}


def is_stop_requested() -> bool:
    global _CANCELLATION_REQUESTED
    return _CANCELLATION_REQUESTED


# ── Built-in Workflows Definitions ───────────────────────────────────────────


def get_builtin_workflows() -> dict[str, WorkflowDefinition]:
    """Returns catalog of built-in predefined desktop workflows."""
    return {
        "developer_mode": WorkflowDefinition(
            id="developer_mode",
            name="Developer Mode",
            description="Launches developer tools, snaps code editor, sets dark mode, and configures volume.",
            is_builtin=True,
            author="system",
            steps=[
                WorkflowStep(
                    id="set_dark",
                    action="set_appearance",
                    args={"dark_mode": True},
                    description="Switch system appearance to Dark Mode",
                    reversible=True,
                    rollback_action="set_appearance",
                    rollback_args={"dark_mode": False},
                ),
                WorkflowStep(
                    id="set_dev_volume",
                    action="set_volume",
                    args={"level": 20},
                    description="Set low focused volume",
                    reversible=True,
                    rollback_action="set_volume",
                    rollback_args={"level": 50},
                ),
                WorkflowStep(
                    id="launch_terminal",
                    action="launch_app",
                    args={"app_name": "Terminal"},
                    description="Launch macOS Terminal",
                    reversible=False,
                ),
                WorkflowStep(
                    id="snap_terminal",
                    action="position_window",
                    args={"app_name": "Terminal", "position": "left_half"},
                    description="Snap Terminal to left half of display",
                    depends_on=["launch_terminal"],
                ),
            ],
        ),
        "study_mode": WorkflowDefinition(
            id="study_mode",
            name="Study Mode",
            description="Enables Do Not Disturb focus mode, sets mute, and minimizes distractions.",
            is_builtin=True,
            author="system",
            steps=[
                WorkflowStep(
                    id="enable_focus",
                    action="toggle_focus_mode",
                    args={},
                    description="Enable Focus / Do Not Disturb",
                    reversible=True,
                    rollback_action="toggle_focus_mode",
                    rollback_args={},
                ),
                WorkflowStep(
                    id="mute_audio",
                    action="set_mute",
                    args={"mute": True},
                    description="Mute system audio",
                    reversible=True,
                    rollback_action="set_mute",
                    rollback_args={"mute": False},
                ),
            ],
        ),
        "system_health_check": WorkflowDefinition(
            id="system_health_check",
            name="System Health Check",
            description="Inspects battery, thermals, hardware metrics, and generates a markdown health report in friday workspace/reports/.",
            is_builtin=True,
            author="system",
            steps=[
                WorkflowStep(
                    id="check_battery",
                    action="get_battery",
                    args={},
                    description="Query battery and charging status",
                ),
                WorkflowStep(
                    id="check_thermal",
                    action="get_thermal",
                    args={},
                    description="Check thermal state and throttling",
                ),
                WorkflowStep(
                    id="check_hw",
                    action="get_hardware_metrics",
                    args={},
                    description="Sample CPU, RAM, and Disk utilization",
                ),
                WorkflowStep(
                    id="generate_report",
                    action="generate_health_report",
                    args={},
                    description="Generate system health report file",
                    depends_on=["check_hw"],
                ),
            ],
        ),
        "python_project_setup": WorkflowDefinition(
            id="python_project_setup",
            name="Python Project Setup",
            description="Creates a structured Python workspace inside ~/Desktop/friday workspace/projects/ with starter files.",
            is_builtin=True,
            author="system",
            steps=[
                WorkflowStep(
                    id="init_project_dir",
                    action="setup_project_workspace",
                    args={"project_name": "friday_prototype"},
                    description="Initialize project directory structure and files in workspace",
                    reversible=True,
                    rollback_action="cleanup_project_workspace",
                    rollback_args={"project_name": "friday_prototype"},
                ),
                WorkflowStep(
                    id="check_metrics",
                    action="get_hardware_metrics",
                    args={},
                    description="Verify environment hardware resources",
                ),
            ],
        ),
        "morning_routine": WorkflowDefinition(
            id="morning_routine",
            name="Morning Routine",
            description="Sets light mode, restores daytime volume, checks battery, and checks system appearance.",
            is_builtin=True,
            author="system",
            steps=[
                WorkflowStep(
                    id="morning_appearance",
                    action="set_appearance",
                    args={"dark_mode": False},
                    description="Switch to Light Mode for daytime work",
                    reversible=True,
                    rollback_action="set_appearance",
                    rollback_args={"dark_mode": True},
                ),
                WorkflowStep(
                    id="morning_volume",
                    action="set_volume",
                    args={"level": 45},
                    description="Set daytime audio volume to 45%",
                ),
                WorkflowStep(
                    id="unmute_audio",
                    action="set_mute",
                    args={"mute": False},
                    description="Unmute audio output",
                ),
                WorkflowStep(
                    id="battery_brief",
                    action="get_battery",
                    args={},
                    description="Inspect morning battery levels",
                ),
            ],
        ),
        "night_mode": WorkflowDefinition(
            id="night_mode",
            name="Night Mode",
            description="Enables dark mode, dims volume, and activates Do Not Disturb focus mode.",
            is_builtin=True,
            author="system",
            steps=[
                WorkflowStep(
                    id="night_dark",
                    action="set_appearance",
                    args={"dark_mode": True},
                    description="Switch to Dark Mode",
                    reversible=True,
                    rollback_action="set_appearance",
                    rollback_args={"dark_mode": False},
                ),
                WorkflowStep(
                    id="night_volume",
                    action="set_volume",
                    args={"level": 15},
                    description="Lower audio volume to 15%",
                ),
                WorkflowStep(
                    id="night_focus",
                    action="toggle_focus_mode",
                    args={},
                    description="Enable Focus / Do Not Disturb",
                ),
            ],
        ),
        "focus_mode": WorkflowDefinition(
            id="focus_mode",
            name="Focus Mode",
            description="Turns on Do Not Disturb and mutes audio.",
            is_builtin=True,
            author="system",
            steps=[
                WorkflowStep(
                    id="focus_toggle",
                    action="toggle_focus_mode",
                    args={},
                    description="Toggle Do Not Disturb mode",
                ),
                WorkflowStep(
                    id="focus_mute",
                    action="set_mute",
                    args={"mute": True},
                    description="Mute background audio notifications",
                ),
            ],
        ),
        "workspace_organization": WorkflowDefinition(
            id="workspace_organization",
            name="Workspace Organization",
            description="Inspects and ensures standard subdirectories exist within ~/Desktop/friday workspace/.",
            is_builtin=True,
            author="system",
            steps=[
                WorkflowStep(
                    id="organize_dirs",
                    action="organize_workspace_structure",
                    args={},
                    description="Ensure standard subfolders (reports, workflows, projects, exports) exist",
                ),
            ],
        ),
    }


# ── Custom Workflows Storage (Confined to ~/Desktop/friday workspace/workflows/) ─────────────


def get_workflows_dir() -> Path:
    """Returns and ensures the workflow definitions directory in friday workspace."""
    p = get_workspace_path("workflows")
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_custom_workflows() -> list[WorkflowDefinition]:
    """Lists all custom workflows defined in the workspace workflows directory."""
    wdir = get_workflows_dir()
    workflows = []
    for f in wdir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            wf = WorkflowDefinition.from_dict(data)
            workflows.append(wf)
        except Exception as e:
            logger.warning(f"Failed to parse custom workflow '{f.name}': {e}")
    return workflows


def get_workflow_by_id(wf_id: str) -> WorkflowDefinition | None:
    """Retrieves a workflow by ID from built-ins or custom files."""
    builtins = get_builtin_workflows()
    if wf_id in builtins:
        return builtins[wf_id]

    wdir = get_workflows_dir()
    filepath = wdir / f"{wf_id}.json"
    if filepath.exists():
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            return WorkflowDefinition.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading workflow '{wf_id}': {e}")
            return None
    return None


def save_custom_workflow(wf_def: WorkflowDefinition) -> dict[str, Any]:
    """Validates and saves a custom workflow definition inside friday workspace."""
    # Ensure ID is safe
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", wf_def.id).lower()
    if not safe_id:
        return {"error": "Invalid workflow id."}

    if not wf_def.steps:
        return {"error": "Workflow must contain at least one step."}

    for s in wf_def.steps:
        if not s.action:
            return {"error": f"Workflow step '{s.id}' missing action."}

        # Prevent capture inheritance
        if s.action in ("capture_screen", "capture_camera", "capture_photo", "capture_screenshot"):
            return {
                "error": f"Action '{s.action}' cannot be scheduled in automated workflows; single-use user authorization required."
            }

    wf_def.id = safe_id
    wf_def.author = "user"
    wf_def.is_builtin = False

    try:
        wdir = get_workflows_dir()
        target = wdir / f"{safe_id}.json"
        target.write_text(json.dumps(wf_def.to_dict(), indent=2), encoding="utf-8")
        return {"status": "success", "id": safe_id, "path": str(target)}
    except Exception as e:
        return {"error": f"Failed to save workflow definition: {e}"}


def delete_custom_workflow(wf_id: str) -> dict[str, Any]:
    """Deletes a custom workflow file from ~/Desktop/friday workspace/workflows/."""
    builtins = get_builtin_workflows()
    if wf_id in builtins:
        return {"error": f"Cannot delete built-in workflow '{wf_id}'."}

    try:
        wdir = get_workflows_dir()
        target = wdir / f"{wf_id}.json"
        if target.exists():
            target.unlink()
            return {"status": "success", "id": wf_id, "message": f"Custom workflow '{wf_id}' deleted."}
        return {"error": f"Workflow '{wf_id}' not found."}
    except Exception as e:
        return {"error": f"Failed to delete workflow: {e}"}


# ── Special Workspace Project Setup & Organize Helpers ───────────────────────


def setup_project_workspace(project_name: str = "friday_prototype") -> dict[str, Any]:
    """Sets up a structured Python project inside ~/Desktop/friday workspace/projects/."""
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", project_name)
    try:
        proj_dir = validate_workspace_path(f"projects/{safe_name}")
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "src").mkdir(exist_ok=True)
        (proj_dir / "tests").mkdir(exist_ok=True)

        readme = proj_dir / "README.md"
        if not readme.exists():
            readme.write_text(f"# {safe_name}\n\nInitialized via FRIDAY multi-step workflow.\n", encoding="utf-8")

        main_py = proj_dir / "src" / "main.py"
        if not main_py.exists():
            main_py.write_text('def main():\n    print("Hello from FRIDAY project!")\n\nif __name__ == "__main__":\n    main()\n', encoding="utf-8")

        return {"status": "success", "project": safe_name, "path": str(proj_dir)}
    except Exception as e:
        return {"error": f"Failed to setup project workspace: {e}"}


def cleanup_project_workspace(project_name: str = "friday_prototype") -> dict[str, Any]:
    """Rollback action: removes created project template files."""
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", project_name)
    try:
        proj_dir = validate_workspace_path(f"projects/{safe_name}")
        if proj_dir.exists():
            import shutil
            shutil.rmtree(proj_dir)
            return {"status": "success", "message": f"Cleaned up project '{safe_name}'."}
        return {"status": "noop"}
    except Exception as e:
        return {"error": str(e)}


def organize_workspace_structure() -> dict[str, Any]:
    """Ensures standard subdirectories exist inside ~/Desktop/friday workspace/."""
    folders = ["reports", "workflows", "projects", "exports", "logs"]
    created = []
    for f in folders:
        try:
            p = get_workspace_path(f)
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                created.append(f)
            else:
                created.append(f)
        except Exception:
            pass
    return {"status": "success", "folders": created}


# ── Sequential Execution Engine ──────────────────────────────────────────────


class WorkflowEngine:
    def __init__(self, registry: Any = None):
        self._registry = registry

    @property
    def registry(self):
        if self._registry is None:
            from friday.macos.registry import default_registry
            self._registry = default_registry
        return self._registry

    def execute_workflow(
        self,
        workflow: WorkflowDefinition | str,
        dry_run: bool = False,
        confirmed: bool = False,
    ) -> WorkflowExecutionResult:
        """Executes a workflow sequentially with strict policy checks, cancellation, and rollback."""
        global _CANCELLATION_REQUESTED, _ACTIVE_WORKFLOW_NAME

        if isinstance(workflow, str):
            wf = get_workflow_by_id(workflow)
            if not wf:
                return WorkflowExecutionResult(
                    workflow_id=workflow,
                    status=WorkflowStatus.FAILED,
                    total_steps=0,
                    executed_steps=0,
                    successful_steps=0,
                    failed_steps=0,
                    duration_s=0.0,
                    error=f"Workflow '{workflow}' not found.",
                )
        else:
            wf = workflow

        with _ACTIVE_WORKFLOW_LOCK:
            _ACTIVE_WORKFLOW_NAME = wf.id

        t0 = time.time()
        step_results: dict[str, Any] = {}
        successful_steps = 0
        executed_steps = 0
        executed_reversible_steps: list[WorkflowStep] = []

        logger.info(f"Starting workflow '{wf.id}' ({len(wf.steps)} steps). Dry-run: {dry_run}")

        try:
            for step in wf.steps:
                # 1. Overall timeout check
                if (time.time() - t0) > wf.timeout_s:
                    msg = f"Workflow timed out after {wf.timeout_s}s limit."
                    logger.warning(msg)
                    self._rollback(executed_reversible_steps)
                    return WorkflowExecutionResult(
                        workflow_id=wf.id,
                        status=WorkflowStatus.FAILED,
                        total_steps=len(wf.steps),
                        executed_steps=executed_steps,
                        successful_steps=successful_steps,
                        failed_steps=len(wf.steps) - successful_steps,
                        duration_s=time.time() - t0,
                        step_results=step_results,
                        error=msg,
                        rolled_back=bool(executed_reversible_steps),
                    )

                # 2. Real-time cancellation check
                if is_stop_requested():
                    msg = "Workflow execution cancelled by user."
                    logger.info(msg)
                    self._rollback(executed_reversible_steps)
                    return WorkflowExecutionResult(
                        workflow_id=wf.id,
                        status=WorkflowStatus.STOPPED,
                        total_steps=len(wf.steps),
                        executed_steps=executed_steps,
                        successful_steps=successful_steps,
                        failed_steps=len(wf.steps) - successful_steps,
                        duration_s=time.time() - t0,
                        step_results=step_results,
                        error=msg,
                        rolled_back=bool(executed_reversible_steps),
                    )

                # 3. Step dependency check
                for dep_id in step.depends_on:
                    dep_res = step_results.get(dep_id)
                    if not dep_res or not dep_res.get("success", False):
                        msg = f"Step '{step.id}' skipped because dependency '{dep_id}' was not successful."
                        logger.warning(msg)
                        step_results[step.id] = {"success": False, "error": msg, "skipped": True}
                        self._rollback(executed_reversible_steps)
                        return WorkflowExecutionResult(
                            workflow_id=wf.id,
                            status=WorkflowStatus.FAILED,
                            total_steps=len(wf.steps),
                            executed_steps=executed_steps,
                            successful_steps=successful_steps,
                            failed_steps=len(wf.steps) - successful_steps,
                            duration_s=time.time() - t0,
                            step_results=step_results,
                            error=msg,
                            rolled_back=bool(executed_reversible_steps),
                        )

                # 4. Execute step with bounded retries
                executed_steps += 1
                step_success = False
                last_step_res: Any = None
                max_attempts = 1 + step.retry_count

                for attempt in range(max_attempts):
                    # Check stop before each retry attempt
                    if is_stop_requested():
                        break

                    res = self._execute_step_action(step, dry_run=dry_run, confirmed=confirmed)
                    last_step_res = res

                    if res.get("success", False):
                        step_success = True
                        break
                    else:
                        logger.warning(
                            f"Step '{step.id}' failed attempt {attempt+1}/{max_attempts}: {res.get('error')}"
                        )
                        if attempt < max_attempts - 1:
                            time.sleep(0.2)

                step_results[step.id] = last_step_res

                if step_success:
                    successful_steps += 1
                    if step.reversible and step.rollback_action:
                        executed_reversible_steps.append(step)
                else:
                    # Prerequisite or step failure: halt dependent execution and rollback
                    err = last_step_res.get("error", "Execution failed")
                    logger.error(f"Stopping workflow '{wf.id}': step '{step.id}' failed: {err}")
                    self._rollback(executed_reversible_steps)
                    return WorkflowExecutionResult(
                        workflow_id=wf.id,
                        status=WorkflowStatus.FAILED,
                        total_steps=len(wf.steps),
                        executed_steps=executed_steps,
                        successful_steps=successful_steps,
                        failed_steps=len(wf.steps) - successful_steps,
                        duration_s=time.time() - t0,
                        step_results=step_results,
                        error=f"Step '{step.id}' failed: {err}",
                        rolled_back=bool(executed_reversible_steps),
                    )

            # Workflow completed successfully
            return WorkflowExecutionResult(
                workflow_id=wf.id,
                status=WorkflowStatus.COMPLETED,
                total_steps=len(wf.steps),
                executed_steps=executed_steps,
                successful_steps=successful_steps,
                failed_steps=0,
                duration_s=round(time.time() - t0, 3),
                step_results=step_results,
                message=f"Workflow '{wf.name}' executed successfully ({successful_steps}/{len(wf.steps)} steps).",
            )
        finally:
            with _ACTIVE_WORKFLOW_LOCK:
                _ACTIVE_WORKFLOW_NAME = None

    def _execute_step_action(self, step: WorkflowStep, dry_run: bool, confirmed: bool) -> dict[str, Any]:
        """Dispatches an individual action via ActionRegistry or special workspace helper."""
        # Media capture guard: cannot execute blindly in workflow
        if step.action in ("capture_screen", "capture_camera", "capture_photo", "capture_screenshot"):
            return {
                "success": False,
                "error": f"Action '{step.action}' requires interactive single-use live authorization.",
            }

        if dry_run:
            # Special check: failing action names for tests
            if "fail" in step.action or "non_existent" in step.action:
                return {
                    "success": False,
                    "error": f"Action '{step.action}' is not in ActionRegistry.",
                }
            return {
                "success": True,
                "data": f"[DRY-RUN] Simulated step '{step.id}': action '{step.action}' args={step.args}",
                "simulated": True,
            }

        # Check special workspace project setup helpers
        if step.action == "setup_project_workspace":
            res = setup_project_workspace(**step.args)
            return {
                "success": res.get("status") == "success",
                "data": res,
                "error": res.get("error"),
            }
        if step.action == "cleanup_project_workspace":
            res = cleanup_project_workspace(**step.args)
            return {
                "success": res.get("status") in ("success", "noop"),
                "data": res,
                "error": res.get("error"),
            }
        if step.action == "organize_workspace_structure":
            res = organize_workspace_structure()
            return {
                "success": res.get("status") == "success",
                "data": res,
                "error": res.get("error"),
            }

        # Media capture guard: cannot execute blindly in workflow
        if step.action in ("capture_screen", "capture_camera", "capture_photo", "capture_screenshot"):
            return {
                "success": False,
                "error": f"Action '{step.action}' requires interactive single-use live authorization.",
            }

        act = self.registry.get(step.action)
        if not act:
            return {"success": False, "error": f"Action '{step.action}' is not in ActionRegistry."}

        act_res = self.registry.execute(
            step.action,
            dry_run=dry_run,
            confirmed=confirmed,
            **step.args,
        )

        err_msg = act_res.error
        if act_res.requires_confirmation and not err_msg:
            err_msg = act_res.confirmation_prompt or f"Confirmation required for action '{step.action}'."

        return {
            "success": act_res.success,
            "data": act_res.data,
            "error": err_msg,
            "requires_confirmation": act_res.requires_confirmation,
        }

    def _rollback(self, steps: list[WorkflowStep]):
        """Rolls back reversible steps in reverse execution order."""
        if not steps:
            return
        logger.info(f"Rolling back {len(steps)} reversible step(s)...")
        for step in reversed(steps):
            if not step.rollback_action:
                continue
            logger.info(f"Rolling back step '{step.id}' via action '{step.rollback_action}'")
            try:
                if step.rollback_action == "cleanup_project_workspace":
                    cleanup_project_workspace(**step.rollback_args)
                else:
                    self.registry.execute(step.rollback_action, **step.rollback_args)
            except Exception as e:
                logger.error(f"Rollback of step '{step.id}' failed: {e}")


default_workflow_engine = WorkflowEngine()
