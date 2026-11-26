"""Unit and regression tests for Milestone 6.1 macOS Control Foundation & Permission Framework."""

import subprocess
from unittest.mock import patch

from friday.macos.registry import (
    ActionDefinition,
    ActionRegistry,
    ActionResult,
    RiskTier,
    get_macos_appearance,
    get_running_applications,
    get_system_battery,
    get_system_storage,
    get_system_volume,
    set_system_volume,
)
from friday.macos.router import format_action_result, route_macos_intent


def test_action_registry_registration_and_listing():
    """Verify registry tracks allowlisted actions and their risk tiers."""
    reg = ActionRegistry()
    act = ActionDefinition(
        name="test_action",
        description="Harmless test action",
        risk=RiskTier.READ_ONLY,
        handler=lambda: {"status": "ok"},
    )
    reg.register(act)
    assert reg.get("test_action") == act

    listed = reg.list_actions()
    assert len(listed) == 1
    assert listed[0]["name"] == "test_action"
    assert listed[0]["risk"] == "READ_ONLY"


def test_argument_validation():
    """Verify arguments are type-checked against action schema."""
    reg = ActionRegistry()
    act = ActionDefinition(
        name="set_test",
        description="Set something",
        risk=RiskTier.LOW,
        handler=lambda count: count * 2,
        arg_schema={"count": int},
    )
    reg.register(act)

    # Valid int
    res_valid = reg.execute("set_test", count=5)
    assert res_valid.success is True
    assert res_valid.data == 10

    # Invalid str instead of int
    res_invalid = reg.execute("set_test", count="not_an_int")
    assert res_invalid.success is False
    assert "Argument 'count' must be of type int" in res_invalid.error


def test_risk_confirmation_policy():
    """Verify high risk actions require confirmation flag."""
    reg = ActionRegistry()
    act_high = ActionDefinition(
        name="kill_proc",
        description="Close a process",
        risk=RiskTier.HIGH,
        handler=lambda: "killed",
    )
    reg.register(act_high)

    # Execution without confirmation
    res_unconfirmed = reg.execute("kill_proc", confirmed=False)
    assert res_unconfirmed.success is False
    assert res_unconfirmed.requires_confirmation is True
    assert "Confirmation required" in res_unconfirmed.confirmation_prompt

    # Execution with confirmed=True
    res_confirmed = reg.execute("kill_proc", confirmed=True)
    assert res_confirmed.success is True
    assert res_confirmed.data == "killed"


def test_dry_run_simulation():
    """Verify dry-run mode returns simulation response without calling handler."""
    called = []
    reg = ActionRegistry()
    act = ActionDefinition(
        name="sample_act",
        description="Sample",
        risk=RiskTier.LOW,
        handler=lambda: called.append(True),
    )
    reg.register(act)

    res = reg.execute("sample_act", dry_run=True)
    assert res.success is True
    assert res.dry_run is True
    assert "[DRY-RUN]" in res.data
    assert len(called) == 0


def test_execution_timeout_protection():
    """Verify execution timeouts trigger and report gracefully."""
    import time

    def slow_handler():
        time.sleep(0.5)
        return "done"

    reg = ActionRegistry()
    act = ActionDefinition(
        name="slow_action",
        description="Action that hangs",
        risk=RiskTier.READ_ONLY,
        handler=slow_handler,
        timeout_s=0.1,
    )
    reg.register(act)

    # Mock timeout exception from subprocess
    with patch.object(act, "handler", side_effect=subprocess.TimeoutExpired(cmd="osascript", timeout=0.1)):
        res = reg.execute("slow_action")
        assert res.success is False
        assert "timed out" in res.error


def test_built_in_harmless_handlers_mocked():
    """Verify handlers execute and return structured dictionaries."""
    with patch("subprocess.check_output", return_value="Now drawing from 'Battery Power'\n -InternalBattery-0 (id=123) 85%; discharging;\n"):
        batt = get_system_battery()
        assert batt["percentage"] == 85
        assert batt["is_charging"] is False

    with patch("subprocess.check_output", return_value="65\n"):
        vol = get_system_volume()
        assert vol["volume"] == 65

    with patch("subprocess.check_call", return_value=0):
        set_vol = set_system_volume(50)
        assert set_vol["volume"] == 50

    with patch("subprocess.check_output", return_value="Finder, Terminal, Safari\n"):
        apps = get_running_applications()
        assert "Finder" in apps
        assert "Terminal" in apps

    with patch("subprocess.check_output", return_value="true\n"):
        appr = get_macos_appearance()
        assert appr["dark_mode"] is True
        assert appr["appearance"] == "Dark"

    storage = get_system_storage()
    assert "free_gb" in storage
    assert "total_gb" in storage


def test_macos_intent_routing():
    """Verify natural-language queries map to registered macOS actions."""
    matched, res = route_macos_intent("what is the current battery level?")
    assert matched is True
    assert res.action_name == "get_battery"

    matched, res = route_macos_intent("what is the current volume?")
    assert matched is True
    assert res.action_name == "get_volume"

    matched, res = route_macos_intent("set volume to 45", dry_run=True)
    assert matched is True
    assert res.action_name == "set_volume"
    assert res.dry_run is True

    matched, res = route_macos_intent("what apps are running right now?")
    assert matched is True
    assert res.action_name == "list_apps"

    matched, res = route_macos_intent("is macOS in dark mode?")
    assert matched is True
    assert res.action_name == "get_appearance"

    matched, res = route_macos_intent("check my free disk space")
    assert matched is True
    assert res.action_name == "get_storage"

    # Unmatched ordinary prompt
    matched, res = route_macos_intent("how do I write a web server?")
    assert matched is False
    assert res is None


def test_format_action_result():
    """Verify result formatter produces clean conversational text."""
    res_batt = ActionResult(success=True, action_name="get_battery", data={"percentage": 88, "is_charging": True})
    formatted = format_action_result(res_batt)
    assert "Battery status: 88% (Charging)." in formatted

    res_vol = ActionResult(success=True, action_name="get_volume", data={"volume": 50})
    assert "Current output volume is 50%." in format_action_result(res_vol)

    res_apps = ActionResult(success=True, action_name="list_apps", data=["Terminal", "Finder"])
    assert "Running visible applications: Terminal, Finder." in format_action_result(res_apps)


def test_cli_macos_action_commands():
    """Verify CLI flags --list-actions and --mac-action."""
    from friday.cli import main

    ret_list = main(["--list-actions"])
    assert ret_list == 0

    ret_act = main(["--mac-action", "get_storage", "--dry-run"])
    assert ret_act == 0
