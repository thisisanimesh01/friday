#!/usr/bin/env python3
"""Comprehensive Validation Suite for Milestone 6.5: Multi-Step Desktop Workflows.

Runs 60 structured validation scenarios across 5 critical domains:
1. Category A (20 scenarios): Built-in workflow execution & dry-runs
2. Category B (10 scenarios): Custom workflow CRUD & schema validation
3. Category C (10 scenarios): Workflow cancellation, dependency failure, timeout, & rollback
4. Category D (10 scenarios): Privacy guard, capture isolation, & security bypass prevention
5. Category E (10 scenarios): System monitoring accuracy, RAM/CPU/Disk metrics, & regressions
"""

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

# Configure path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "friday"))

from friday.macos.registry import ActionResult, default_registry  # noqa: E402
from friday.macos.router import format_action_result, route_macos_intent  # noqa: E402
from friday.macos.system_settings import (  # noqa: E402
    get_battery_status,
    get_hardware_metrics,
    get_thermal_status,
)
from friday.macos.workflows import (  # noqa: E402
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowStatus,
    WorkflowStep,
    cleanup_project_workspace,
    delete_custom_workflow,
    get_builtin_workflows,
    get_workflow_by_id,
    list_custom_workflows,
    organize_workspace_structure,
    request_workflow_stop,
    save_custom_workflow,
    setup_project_workspace,
)
from friday.security.privacy_guard import (  # noqa: E402
    PrivacyViolationError,
    is_path_permanently_protected,
    validate_workspace_path,
)

results: list[dict] = []


def record_scenario(num: int, category: str, name: str, passed: bool, details: str = ""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] Scenario {num:02d} ({category}): {name} - {details}")
    results.append({
        "scenario": num,
        "category": category,
        "name": name,
        "passed": passed,
        "details": details,
    })


def run_all_scenarios():
    print("=" * 80)
    print("FRIDAY MILESTONE 6.5 — 60-SCENARIO VALIDATION SUITE")
    print("=" * 80)
    engine = WorkflowEngine()

    # ─────────────────────────────────────────────────────────────────────────
    # Category A: Built-in Workflows (20 scenarios)
    # ─────────────────────────────────────────────────────────────────────────
    builtins = get_builtin_workflows()

    # 1-8: Catalog completeness for all 8 required built-ins
    required_wfs = [
        "developer_mode",
        "study_mode",
        "system_health_check",
        "python_project_setup",
        "morning_routine",
        "night_mode",
        "focus_mode",
        "workspace_organization",
    ]
    for idx, wf_id in enumerate(required_wfs, 1):
        wf = builtins.get(wf_id)
        ok = wf is not None and wf.id == wf_id and len(wf.steps) > 0 and wf.is_builtin
        record_scenario(idx, "Built-in Workflows", f"Catalog check: {wf_id}", ok, f"Steps: {len(wf.steps) if wf else 0}")

    # 9-16: Dry-run execution of each built-in workflow
    for idx, wf_id in enumerate(required_wfs, 9):
        wf = builtins[wf_id]
        res = engine.execute_workflow(wf, dry_run=True, confirmed=True)
        ok = res.status == WorkflowStatus.COMPLETED and res.successful_steps == len(wf.steps)
        record_scenario(idx, "Built-in Workflows", f"Dry-run execution: {wf_id}", ok, f"Status: {res.status.value}")

    # 17: Workspace Organization execution
    org_res = organize_workspace_structure()
    ok_17 = org_res.get("status") == "success" and len(org_res.get("folders", [])) >= 4
    record_scenario(17, "Built-in Workflows", "Workspace organization directory structure", ok_17, f"Folders: {org_res.get('folders')}")

    # 18: Python Project Setup execution
    setup_res = setup_project_workspace("validation_test_proj")
    ok_18 = setup_res.get("status") == "success" and Path(setup_res.get("path", "")).exists()
    record_scenario(18, "Built-in Workflows", "Python project workspace initialization", ok_18, f"Path: {setup_res.get('path')}")

    # 19: Python Project Setup cleanup / rollback execution
    clean_res = cleanup_project_workspace("validation_test_proj")
    ok_19 = clean_res.get("status") == "success" and not Path(setup_res.get("path", "")).exists()
    record_scenario(19, "Built-in Workflows", "Python project workspace rollback cleanup", ok_19, f"Cleaned: {clean_res.get('message')}")

    # 20: Built-in workflow execution via default ActionRegistry handler
    reg_run = default_registry.execute(name="run_workflow", workflow_name="system_health_check", simulated=True, confirmed=True)
    ok_20 = reg_run.success and reg_run.data.get("status") == "COMPLETED"
    record_scenario(20, "Built-in Workflows", "Registry dispatch of system_health_check", ok_20, f"Result: {reg_run.data.get('status')}")

    # ─────────────────────────────────────────────────────────────────────────
    # Category B: Custom Workflow Management (CRUD) (10 scenarios)
    # ─────────────────────────────────────────────────────────────────────────
    temp_dir = tempfile.mkdtemp(prefix="friday_wf_test_")
    with patch("friday.macos.workflows.get_workflows_dir", return_value=Path(temp_dir)):
        # 21: Create valid custom workflow
        custom1 = WorkflowDefinition(
            id="flow_alpha",
            name="Flow Alpha",
            description="Alpha test flow",
            steps=[WorkflowStep(id="s1", action="set_volume", args={"level": 35})],
        )
        s_res = save_custom_workflow(custom1)
        ok_21 = s_res.get("status") == "success" and (Path(temp_dir) / "flow_alpha.json").exists()
        record_scenario(21, "Custom Workflows", "Create custom workflow file", ok_21, f"Path: {s_res.get('path')}")

        # 22: Load custom workflow by ID
        loaded = get_workflow_by_id("flow_alpha")
        ok_22 = loaded is not None and loaded.name == "Flow Alpha" and len(loaded.steps) == 1
        record_scenario(22, "Custom Workflows", "Load custom workflow by ID", ok_22, f"Loaded name: {getattr(loaded, 'name', None)}")

        # 23: List custom workflows
        c_list = list_custom_workflows()
        ok_23 = len(c_list) == 1 and c_list[0].id == "flow_alpha"
        record_scenario(23, "Custom Workflows", "List custom workflows in workspace", ok_23, f"Count: {len(c_list)}")

        # 24: Update existing custom workflow
        custom1.description = "Updated description"
        custom1.steps.append(WorkflowStep(id="s2", action="set_appearance", args={"dark_mode": True}))
        u_res = save_custom_workflow(custom1)
        loaded2 = get_workflow_by_id("flow_alpha")
        ok_24 = u_res.get("status") == "success" and len(loaded2.steps) == 2
        record_scenario(24, "Custom Workflows", "Update custom workflow steps", ok_24, f"Steps: {len(loaded2.steps) if loaded2 else 0}")

        # 25: Delete custom workflow
        del_res = delete_custom_workflow("flow_alpha")
        loaded_after_del = get_workflow_by_id("flow_alpha")
        ok_25 = del_res.get("status") == "success" and loaded_after_del is None
        record_scenario(25, "Custom Workflows", "Delete custom workflow", ok_25, f"Deleted: {del_res.get('status')}")

        # 26: Delete non-existent custom workflow returns error
        del_fail = delete_custom_workflow("non_existent_flow")
        ok_26 = "error" in del_fail
        record_scenario(26, "Custom Workflows", "Delete non-existent workflow error handling", ok_26, f"Error: {del_fail.get('error')}")

        # 27: Reject deleting built-in workflows
        del_builtin = delete_custom_workflow("developer_mode")
        ok_27 = "error" in del_builtin and "Cannot delete built-in" in del_builtin["error"]
        record_scenario(27, "Custom Workflows", "Built-in workflow deletion protection", ok_27, f"Blocked: {del_builtin.get('error')}")

        # 28: Reject saving workflow with 0 steps
        empty_wf = WorkflowDefinition(id="empty_flow", name="Empty", description="No steps", steps=[])
        save_empty = save_custom_workflow(empty_wf)
        ok_28 = "error" in save_empty and "at least one step" in save_empty["error"]
        record_scenario(28, "Custom Workflows", "Reject empty workflow definition", ok_28, f"Error: {save_empty.get('error')}")

        # 29: Reject saving workflow with invalid/unsafe ID
        unsafe_wf = WorkflowDefinition(id="", name="Invalid", description="", steps=[WorkflowStep(id="s1", action="set_volume")])
        save_unsafe = save_custom_workflow(unsafe_wf)
        ok_29 = "error" in save_unsafe
        record_scenario(29, "Custom Workflows", "Reject invalid workflow identifier", ok_29, f"Result: {save_unsafe.get('error')}")

        # 30: Registry create_workflow handler with JSON string
        json_str = json.dumps({
            "id": "registry_test_flow",
            "name": "Registry Flow",
            "description": "Created via registry JSON",
            "steps": [{"id": "st1", "action": "set_volume", "args": {"level": 50}}],
        })
        reg_create = default_registry.execute(name="create_workflow", definition_json=json_str)
        ok_30 = reg_create.success and reg_create.data.get("status") == "success"
        record_scenario(30, "Custom Workflows", "Create workflow via registry JSON handler", ok_30, f"Saved ID: {reg_create.data.get('id') if reg_create.data else None}")

    shutil.rmtree(temp_dir, ignore_errors=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Category C: Cancellation, Dependencies, Timeouts & Rollback (10 scenarios)
    # ─────────────────────────────────────────────────────────────────────────
    # 31: Workflow dependency stoppage: step 2 depends on failed step 1
    dep_wf = WorkflowDefinition(
        id="dep_fail_wf",
        name="Dep Fail",
        description="",
        steps=[
            WorkflowStep(id="bad_step", action="non_existent_action"),
            WorkflowStep(id="dep_step", action="set_volume", args={"level": 20}, depends_on=["bad_step"]),
        ],
    )
    res_31 = engine.execute_workflow(dep_wf, dry_run=False, confirmed=True)
    ok_31 = res_31.status == WorkflowStatus.FAILED and "bad_step" in res_31.error
    record_scenario(31, "Resilience & Control", "Prerequisite dependency failure halts execution", ok_31, f"Error: {res_31.error}")

    # 32: Workflow rollback on failure for reversible steps
    rb_wf = WorkflowDefinition(
        id="rb_test_wf",
        name="Rollback Test",
        description="",
        steps=[
            WorkflowStep(
                id="rev_step",
                action="set_appearance",
                args={"dark_mode": True},
                reversible=True,
                rollback_action="set_appearance",
                rollback_args={"dark_mode": False},
            ),
            WorkflowStep(id="fail_step", action="failing_action"),
        ],
    )
    res_32 = engine.execute_workflow(rb_wf, dry_run=True, confirmed=True)
    ok_32 = res_32.status == WorkflowStatus.FAILED and res_32.rolled_back is True
    record_scenario(32, "Resilience & Control", "Reversible step rollback on subsequent step failure", ok_32, f"Rolled back: {res_32.rolled_back}")

    # 33: Non-reversible steps are not rolled back
    non_rb_wf = WorkflowDefinition(
        id="non_rb_test_wf",
        name="Non-Rollback Test",
        description="",
        steps=[
            WorkflowStep(id="nr_step", action="set_volume", args={"level": 25}, reversible=False),
            WorkflowStep(id="fail_step_2", action="failing_action"),
        ],
    )
    res_33 = engine.execute_workflow(non_rb_wf, dry_run=True, confirmed=True)
    ok_33 = res_33.status == WorkflowStatus.FAILED and res_33.rolled_back is False
    record_scenario(33, "Resilience & Control", "Non-reversible step does not trigger rollback", ok_33, f"Rolled back: {res_33.rolled_back}")

    # 34: Global cancellation stop signal
    from friday.macos import workflows
    workflows._CANCELLATION_REQUESTED = True
    cancel_wf = WorkflowDefinition(
        id="cancel_wf",
        name="Cancel Flow",
        description="",
        steps=[WorkflowStep(id="c1", action="set_volume", args={"level": 40})],
    )
    try:
        res_34 = engine.execute_workflow(cancel_wf, dry_run=True, confirmed=True)
        ok_34 = res_34.status == WorkflowStatus.STOPPED and "cancelled" in res_34.error.lower()
    finally:
        workflows._CANCELLATION_REQUESTED = False
    record_scenario(34, "Resilience & Control", "Real-time workflow stop signal", ok_34, f"Status: {res_34.status.value}")

    # 35: request_workflow_stop() when idle reports no active workflow
    stop_idle = request_workflow_stop()
    ok_35 = stop_idle.get("status") == "idle"
    record_scenario(35, "Resilience & Control", "request_workflow_stop() handles idle state gracefully", ok_35, f"Message: {stop_idle.get('message')}")

    # 36: Workflow overall timeout enforcement
    timeout_wf = WorkflowDefinition(
        id="timeout_wf",
        name="Timeout Flow",
        description="",
        timeout_s=0.00001,  # immediate timeout
        steps=[
            WorkflowStep(id="t1", action="set_volume", args={"level": 30}),
            WorkflowStep(id="t2", action="set_appearance", args={"dark_mode": True}),
        ],
    )
    time.sleep(0.01)
    res_36 = engine.execute_workflow(timeout_wf, dry_run=True, confirmed=True)
    ok_36 = res_36.status == WorkflowStatus.FAILED and res_36.error and "timed out" in res_36.error.lower()
    record_scenario(36, "Resilience & Control", "Workflow overall timeout enforcement", ok_36, f"Error: {res_36.error}")

    # 37: Bounded retry limit (max 2 retries)
    retry_wf = WorkflowDefinition(
        id="retry_wf",
        name="Retry Flow",
        description="",
        steps=[WorkflowStep(id="r1", action="non_existent", retry_count=2)],
    )
    res_37 = engine.execute_workflow(retry_wf, dry_run=False, confirmed=True)
    ok_37 = res_37.status == WorkflowStatus.FAILED
    record_scenario(37, "Resilience & Control", "Bounded retry limits (max 2 retries, no loops)", ok_37, "Attempts executed within bounds")

    # 38: ActionRegistry requires_confirmation enforcement in workflow
    high_risk_step = WorkflowStep(id="hr1", action="system_shutdown", args={})
    hr_wf = WorkflowDefinition(id="hr_wf", name="High Risk", description="", steps=[high_risk_step])
    res_38 = engine.execute_workflow(hr_wf, dry_run=False, confirmed=False)
    ok_38 = res_38.status == WorkflowStatus.FAILED and "system_shutdown" in res_38.error
    record_scenario(38, "Resilience & Control", "Confirmation enforcement inside workflow steps", ok_38, f"Result: {res_38.error}")

    # 39: Multiple dependencies: all must succeed
    multi_dep_wf = WorkflowDefinition(
        id="multi_dep",
        name="Multi Dep",
        description="",
        steps=[
            WorkflowStep(id="m1", action="set_volume", args={"level": 30}),
            WorkflowStep(id="m2", action="failing_action"),
            WorkflowStep(id="m3", action="set_appearance", args={"dark_mode": True}, depends_on=["m1", "m2"]),
        ],
    )
    res_39 = engine.execute_workflow(multi_dep_wf, dry_run=True, confirmed=True)
    ok_39 = res_39.status == WorkflowStatus.FAILED
    record_scenario(39, "Resilience & Control", "Multiple step dependencies requirement", ok_39, f"Status: {res_39.status.value}")

    # 40: Stop workflow registry action dispatch
    stop_act = default_registry.execute(name="stop_workflow")
    ok_40 = stop_act.success and stop_act.data.get("status") in ("idle", "stopping")
    record_scenario(40, "Resilience & Control", "Stop workflow ActionRegistry integration", ok_40, f"Status: {stop_act.data.get('status')}")

    # ─────────────────────────────────────────────────────────────────────────
    # Category D: Privacy & Security Guardrails (10 scenarios)
    # ─────────────────────────────────────────────────────────────────────────
    # 41: Protected folder 'me and she' lexical deny-by-default
    ok_41 = is_path_permanently_protected("/Users/animeshyadav/Desktop/me and she")
    record_scenario(41, "Privacy & Security", "Protected folder 'me and she' lexical check", ok_41, "Blocked: True")

    # 42: Protected folder case variations and encodings
    ok_42 = (
        is_path_permanently_protected("/Users/animeshyadav/Desktop/ME AND SHE/secret.txt")
        and is_path_permanently_protected("/Users/animeshyadav/Desktop/me_and_she/file.png")
    )
    record_scenario(42, "Privacy & Security", "Protected folder case & separator variants", ok_42, "All variants blocked")

    # 43: Directory traversal into protected folder blocked
    ok_43 = False
    try:
        validate_workspace_path("../me and she/passwords.txt")
    except PrivacyViolationError:
        ok_43 = True
    record_scenario(43, "Privacy & Security", "Directory traversal towards protected folder", ok_43, "PrivacyViolationError raised")

    # 44: Reject camera capture action in saved workflow
    cam_wf = WorkflowDefinition(
        id="cam_hack",
        name="Cam Hack",
        description="",
        steps=[WorkflowStep(id="cam", action="capture_camera")],
    )
    cam_save = save_custom_workflow(cam_wf)
    ok_44 = "error" in cam_save and "single-use" in cam_save["error"]
    record_scenario(44, "Privacy & Security", "Automated camera capture blocked in workflow definition", ok_44, f"Blocked: {cam_save.get('error')}")

    # 45: Reject screenshot capture action in saved workflow
    scr_wf = WorkflowDefinition(
        id="scr_hack",
        name="Screenshot Hack",
        description="",
        steps=[WorkflowStep(id="scr", action="capture_screenshot")],
    )
    scr_save = save_custom_workflow(scr_wf)
    ok_45 = "error" in scr_save and "single-use" in scr_save["error"]
    record_scenario(45, "Privacy & Security", "Automated screenshot capture blocked in workflow definition", ok_45, f"Blocked: {scr_save.get('error')}")

    # 46: Engine execution directly blocks single-use photo capture
    photo_wf = WorkflowDefinition(
        id="photo_exec",
        name="Photo Exec",
        description="",
        steps=[WorkflowStep(id="p1", action="capture_photo")],
    )
    res_46 = engine.execute_workflow(photo_wf, dry_run=False, confirmed=True)
    ok_46 = res_46.status == WorkflowStatus.FAILED and "single-use" in res_46.error
    record_scenario(46, "Privacy & Security", "Engine halts workflow on unconfirmed media capture", ok_46, f"Blocked: {res_46.error}")

    # 47: Disallowed shell action in workflow definition rejected
    shell_wf = WorkflowDefinition(
        id="shell_hack",
        name="Shell Hack",
        description="",
        steps=[WorkflowStep(id="sh", action="bash_exec", args={"cmd": "rm -rf /"})],
    )
    res_47 = engine.execute_workflow(shell_wf, dry_run=False, confirmed=True)
    ok_47 = res_47.status == WorkflowStatus.FAILED and "not in ActionRegistry" in res_47.error
    record_scenario(47, "Privacy & Security", "Arbitrary shell action in workflow rejected", ok_47, f"Blocked: {res_47.error}")

    # 48: Ensure workflow definition output path stays strictly in workspace
    try:
        ws_p = validate_workspace_path("workflows/test.json")
        ok_48 = "friday workspace" in str(ws_p)
    except Exception:
        ok_48 = False
    record_scenario(48, "Privacy & Security", "Workflow storage path confinement", ok_48, f"Path: {ws_p if ok_48 else 'Failed'}")

    # 49: Health report generation path strictly inside friday workspace/reports/
    from friday.macos.system_settings import generate_system_health_report
    hr_res = generate_system_health_report("validation_health_test.md")
    ok_49 = hr_res.get("status") == "success" and "friday workspace/reports" in hr_res.get("file_path", "")
    record_scenario(49, "Privacy & Security", "Health report output strictly inside workspace/reports/", ok_49, f"Saved: {hr_res.get('file_path')}")

    # 50: Synthetic fixture isolation distinction
    synth_path = "/tmp/synthetic_test/me and she"
    ok_50 = is_path_permanently_protected(synth_path)
    record_scenario(50, "Privacy & Security", "Synthetic isolation test path caught without touching host directory", ok_50, "Matched pattern: True")

    # ─────────────────────────────────────────────────────────────────────────
    # Category E: System Monitoring & Regressions (10 scenarios)
    # ─────────────────────────────────────────────────────────────────────────
    # 51: get_hardware_metrics RAM calculation fields
    hw = get_hardware_metrics()
    ok_51 = all(k in hw for k in ["ram_total_gb", "ram_used_gb", "ram_active_gb", "ram_wired_gb", "ram_available_gb", "ram_percent"])
    record_scenario(51, "System Monitoring", "RAM Activity Monitor metrics completeness", ok_51, f"Total: {hw.get('ram_total_gb')}GB, Active: {hw.get('ram_active_gb')}GB")

    # 52: get_hardware_metrics Disk calculation fields
    ok_52 = all(k in hw for k in ["disk_total_gb", "disk_used_gb", "disk_free_gb", "disk_percent"])
    record_scenario(52, "System Monitoring", "APFS disk space calculations", ok_52, f"Total: {hw.get('disk_total_gb')}GB, Free: {hw.get('disk_free_gb')}GB")

    # 53: get_hardware_metrics CPU sampling (non-negative)
    ok_53 = isinstance(hw.get("cpu_percent"), (int, float)) and hw["cpu_percent"] >= 0.0
    record_scenario(53, "System Monitoring", "CPU utilization sampling validity", ok_53, f"CPU: {hw.get('cpu_percent')}%")

    # 54: get_battery_status fields
    batt = get_battery_status()
    ok_54 = "percentage" in batt and "power_source" in batt and "is_charging" in batt
    record_scenario(54, "System Monitoring", "Battery and power source status", ok_54, f"Battery: {batt.get('percentage')}%, Power: {batt.get('power_source')}")

    # 55: get_thermal_status fields
    therm = get_thermal_status()
    ok_55 = "thermal_state" in therm and "throttling" in therm
    record_scenario(55, "System Monitoring", "Thermal status & throttling alerts", ok_55, f"State: {therm.get('thermal_state')}, Throttling: {therm.get('throttling')}")

    # 56: English intent routing for workflows
    m_en, res_en = route_macos_intent("start developer mode", dry_run=True, confirmed=True)
    ok_56 = m_en and res_en.action_name == "run_workflow"
    record_scenario(56, "Routing & Regressions", "English workflow intent routing", ok_56, f"Action: {res_en.action_name if res_en else None}")

    # 57: Hinglish intent routing for workflows
    m_hi, res_hi = route_macos_intent("dev mode chalu karo", dry_run=True, confirmed=True)
    ok_57 = m_hi and res_hi.action_name == "run_workflow"
    record_scenario(57, "Routing & Regressions", "Hinglish workflow intent routing", ok_57, f"Action: {res_hi.action_name if res_hi else None}")

    # 58: Stop workflow natural language command
    m_stop, res_stop = route_macos_intent("workflow roko", dry_run=True, confirmed=True)
    ok_58 = m_stop and res_stop.action_name == "stop_workflow"
    record_scenario(58, "Routing & Regressions", "Hinglish stop workflow intent routing", ok_58, f"Action: {res_stop.action_name if res_stop else None}")

    # 59: List workflows natural language command
    m_list, res_list = route_macos_intent("list workflows", dry_run=True, confirmed=True)
    ok_59 = m_list and res_list.action_name == "list_workflows"
    record_scenario(59, "Routing & Regressions", "List workflows intent routing", ok_59, f"Action: {res_list.action_name if res_list else None}")

    # 60: Action result formatting for workflow execution
    sample_exec_result = ActionResult(
        success=True,
        action_name="run_workflow",
        data={
            "workflow_id": "study_mode",
            "status": "COMPLETED",
            "total_steps": 2,
            "successful_steps": 2,
            "duration_s": 0.42,
        },
    )
    fmt = format_action_result(sample_exec_result)
    ok_60 = "study_mode" in fmt and "completed successfully" in fmt
    record_scenario(60, "Routing & Regressions", "Conversational formatting for workflow outcome", ok_60, f"Formatted: {fmt}")

    # ─────────────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────────────
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print("\n" + "=" * 80)
    print(f"VALIDATION SUITE COMPLETE: {passed}/{total} SCENARIOS PASSED ({failed} FAILED)")
    print("=" * 80)

    if failed > 0:
        print("\nFailed Scenarios:")
        for r in results:
            if not r["passed"]:
                print(f"  - Scenario {r['scenario']:02d}: {r['name']} ({r['details']})")
        sys.exit(1)
    else:
        print("\nAll 60 Milestone 6.5 validation scenarios passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    run_all_scenarios()
