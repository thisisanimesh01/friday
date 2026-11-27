"""Unit tests for Multi-Step Desktop Workflows (Milestone 6.5)."""

from unittest.mock import patch

from friday.macos.router import route_macos_intent
from friday.macos.workflows import (
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowStatus,
    WorkflowStep,
    delete_custom_workflow,
    get_builtin_workflows,
    get_workflow_by_id,
    list_custom_workflows,
    save_custom_workflow,
)


def test_builtin_workflows_catalog():
    builtins = get_builtin_workflows()
    assert len(builtins) >= 8
    expected = [
        "developer_mode",
        "study_mode",
        "system_health_check",
        "python_project_setup",
        "morning_routine",
        "night_mode",
        "focus_mode",
        "workspace_organization",
    ]
    for exp in expected:
        assert exp in builtins
        wf = builtins[exp]
        assert wf.id == exp
        assert wf.is_builtin is True
        assert len(wf.steps) > 0


def test_workflow_engine_dry_run_success():
    engine = WorkflowEngine()
    wf = get_builtin_workflows()["developer_mode"]
    res = engine.execute_workflow(wf, dry_run=True, confirmed=True)
    assert res.status == WorkflowStatus.COMPLETED
    assert res.successful_steps == len(wf.steps)
    assert res.total_steps == len(wf.steps)
    assert res.failed_steps == 0


def test_workflow_dependency_failure_stops_execution():
    engine = WorkflowEngine()
    step1 = WorkflowStep(
        id="s1",
        action="non_existent_fail_action",
        args={},
    )
    step2 = WorkflowStep(
        id="s2",
        action="set_volume",
        args={"level": 30},
        depends_on=["s1"],
    )
    custom_wf = WorkflowDefinition(
        id="test_dep_failure",
        name="Test Dep Failure",
        description="Verifies dependency stoppage",
        steps=[step1, step2],
    )
    res = engine.execute_workflow(custom_wf, dry_run=False, confirmed=True)
    assert res.status == WorkflowStatus.FAILED
    assert "s2" not in res.step_results or res.step_results["s2"].get("skipped")
    assert res.failed_steps > 0


def test_workflow_rollback_on_failure():
    engine = WorkflowEngine()
    step1 = WorkflowStep(
        id="s1",
        action="set_appearance",
        args={"dark_mode": True},
        reversible=True,
        rollback_action="set_appearance",
        rollback_args={"dark_mode": False},
    )
    step2 = WorkflowStep(
        id="s2",
        action="non_existent_failure_action",
        args={},
    )
    custom_wf = WorkflowDefinition(
        id="test_rollback",
        name="Test Rollback",
        description="Verifies rollback invocation",
        steps=[step1, step2],
    )

    with patch.object(engine.registry, "execute", wraps=engine.registry.execute):
        res = engine.execute_workflow(custom_wf, dry_run=True, confirmed=True)
        assert res.status == WorkflowStatus.FAILED
        assert res.rolled_back is True


def test_workflow_cancellation():
    engine = WorkflowEngine()
    step1 = WorkflowStep(
        id="s1",
        action="set_volume",
        args={"level": 25},
    )
    step2 = WorkflowStep(
        id="s2",
        action="set_appearance",
        args={"dark_mode": True},
    )
    custom_wf = WorkflowDefinition(
        id="test_cancel",
        name="Test Cancel",
        description="Verifies cancellation stop",
        steps=[step1, step2],
    )

    from friday.macos import workflows
    workflows._CANCELLATION_REQUESTED = True

    try:
        res = engine.execute_workflow(custom_wf, dry_run=True, confirmed=True)
        assert res.status == WorkflowStatus.STOPPED
        assert "cancelled" in res.error.lower()
    finally:
        workflows._CANCELLATION_REQUESTED = False


def test_custom_workflow_crud(tmp_path):
    with patch("friday.macos.workflows.get_workspace_path", return_value=tmp_path / "workflows"):
        custom = WorkflowDefinition(
            id="user_test_flow",
            name="User Test Flow",
            description="A user flow",
            steps=[
                WorkflowStep(id="step1", action="set_volume", args={"level": 40}),
            ],
        )
        save_res = save_custom_workflow(custom)
        assert save_res.get("status") == "success"

        loaded = get_workflow_by_id("user_test_flow")
        assert loaded is not None
        assert loaded.id == "user_test_flow"
        assert loaded.name == "User Test Flow"

        listing = list_custom_workflows()
        assert len(listing) == 1
        assert listing[0].id == "user_test_flow"

        del_res = delete_custom_workflow("user_test_flow")
        assert del_res.get("status") == "success"

        after_del = get_workflow_by_id("user_test_flow")
        assert after_del is None


def test_media_capture_in_workflow_is_blocked():
    engine = WorkflowEngine()
    step_camera = WorkflowStep(id="c1", action="capture_camera", args={})
    wf = WorkflowDefinition(
        id="illegal_capture",
        name="Illegal Capture",
        description="Tries to secretly capture camera",
        steps=[step_camera],
    )
    # Save should reject automated camera capture
    save_res = save_custom_workflow(wf)
    assert "error" in save_res
    assert "single-use" in save_res["error"]

    # Even direct engine execution should block it
    res = engine.execute_workflow(wf, dry_run=False, confirmed=True)
    assert res.status == WorkflowStatus.FAILED
    assert "single-use" in res.error


def test_router_workflow_intents():
    queries = [
        ("start developer mode", "run_workflow", "developer_mode"),
        ("dev mode chalu karo", "run_workflow", "developer_mode"),
        ("start study mode", "run_workflow", "study_mode"),
        ("start night mode", "run_workflow", "night_mode"),
        ("activate focus mode", "run_workflow", "focus_mode"),
        ("stop the workflow", "stop_workflow", None),
        ("workflow roko", "stop_workflow", None),
        ("list workflows", "list_workflows", None),
        ("run workflow morning_routine", "run_workflow", "morning_routine"),
    ]
    for text, expected_action, expected_wf in queries:
        matched, res = route_macos_intent(text, dry_run=False, confirmed=True)
        assert matched is True, f"Failed to match: {text}"
        assert res.action_name == expected_action
        if expected_wf:
            assert isinstance(res.data, dict)
            assert res.data.get("workflow_id") == expected_wf
