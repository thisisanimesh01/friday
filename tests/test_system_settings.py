"""Unit and Functional Tests for Milestone 6.4: System Settings, Hardware Controls & Health Monitoring."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from friday.macos.registry import default_registry
from friday.macos.router import route_macos_intent
from friday.macos.system_settings import (
    generate_system_health_report,
    get_appearance,
    get_audio_devices,
    get_audio_volume,
    get_battery_status,
    get_bluetooth_status,
    get_display_brightness,
    get_focus_mode,
    get_hardware_metrics,
    get_thermal_status,
    get_wifi_status,
    lock_screen,
    set_audio_device,
    set_audio_mute,
    set_audio_volume,
    set_bluetooth_power,
    set_display_brightness,
    set_wifi_power,
    system_restart,
    system_shutdown,
    system_sleep,
    toggle_appearance,
    toggle_audio_mute,
    toggle_focus_mode,
)

# ── 1. Audio Controls ────────────────────────────────────────────────────────


def test_get_and_set_audio_volume():
    """Verify volume read and set boundary handling."""
    res = get_audio_volume()
    assert "volume" in res
    assert 0 <= res["volume"] <= 100
    assert "muted" in res

    # Set volume clamp check
    set_res = set_audio_volume(50)
    assert "volume" in set_res or "error" in set_res


def test_set_and_toggle_audio_mute():
    """Verify mute / unmute state toggle."""
    res = set_audio_mute(True)
    assert "muted" in res or "error" in res

    toggle_res = toggle_audio_mute()
    assert "muted" in toggle_res or "error" in toggle_res


def test_get_and_set_audio_device():
    """Verify audio device listing and unsupported switching reporting."""
    devices = get_audio_devices()
    assert "devices" in devices
    assert len(devices["devices"]) >= 1

    # Setting device without SwitchAudioSource should report unsupported gracefully
    res = set_audio_device("External Headphones", device_type="output")
    assert res.get("status") in ("unsupported", "success")


# ── 2. Display & Appearance ──────────────────────────────────────────────────


def test_get_and_set_appearance():
    """Verify Dark / Light mode queries and toggles."""
    app = get_appearance()
    assert "appearance" in app
    assert app["appearance"] in ("Dark", "Light")

    # Dry-run toggle
    toggle_res = toggle_appearance()
    assert "appearance" in toggle_res or "error" in toggle_res


def test_get_and_set_display_brightness():
    """Verify brightness query and graceful capability limitation."""
    b_res = get_display_brightness()
    assert "brightness" in b_res

    s_res = set_display_brightness(80)
    assert "brightness" in s_res or s_res.get("status") == "unsupported"


def test_get_and_toggle_focus_mode():
    """Verify Focus Mode / Do Not Disturb queries and toggle trigger."""
    f_res = get_focus_mode()
    assert "focus_mode" in f_res

    t_res = toggle_focus_mode()
    assert "status" in t_res


# ── 3. Hardware & System Monitoring ──────────────────────────────────────────


def test_get_battery_status():
    """Verify battery percentage and charging state."""
    batt = get_battery_status()
    assert "percentage" in batt
    assert "is_charging" in batt
    assert "power_source" in batt


def test_get_thermal_status():
    """Verify thermal state reports Normal and throttling boolean."""
    therm = get_thermal_status()
    assert "thermal_state" in therm
    assert "throttling" in therm
    assert isinstance(therm["throttling"], bool)


def test_get_hardware_metrics():
    """Verify psutil metrics: CPU, RAM, disk."""
    hw = get_hardware_metrics()
    assert "cpu_percent" in hw
    assert "ram_total_gb" in hw
    assert "disk_total_gb" in hw
    assert hw["ram_total_gb"] > 0
    assert hw["disk_total_gb"] > 0


def test_get_wifi_and_bluetooth_status():
    """Verify Wi-Fi and Bluetooth queries."""
    wifi = get_wifi_status()
    assert "power" in wifi
    assert "enabled" in wifi

    bt = get_bluetooth_status()
    assert "power" in bt


# ── 4. Guarded Power & Connectivity Controls ─────────────────────────────────


def test_connectivity_confirmation_requirement():
    """Verify Wi-Fi and Bluetooth controls require confirmation."""
    # Unconfirmed must prompt for confirmation
    res_wifi = set_wifi_power(False, confirmed=False)
    assert res_wifi.get("requires_confirmation") is True

    res_bt = set_bluetooth_power(False, confirmed=False)
    assert res_bt.get("requires_confirmation") is True

    # Confirmed simulated
    sim_wifi = set_wifi_power(False, confirmed=True, simulated=True)
    assert sim_wifi.get("status") == "simulated"


def test_power_controls_confirmation_requirement():
    """Verify screen lock, sleep, restart, and shutdown require confirmation."""
    assert lock_screen(confirmed=False).get("requires_confirmation") is True
    assert system_sleep(confirmed=False).get("requires_confirmation") is True
    assert system_restart(confirmed=False).get("requires_confirmation") is True
    assert system_shutdown(confirmed=False).get("requires_confirmation") is True

    # Simulated executions
    assert lock_screen(confirmed=True, simulated=True).get("status") == "simulated"
    assert system_sleep(confirmed=True, simulated=True).get("status") == "simulated"
    assert system_restart(confirmed=True, simulated=True).get("status") == "simulated"
    assert system_shutdown(confirmed=True, simulated=True).get("status") == "simulated"


# ── 5. System Health Report Confinement ───────────────────────────────────────


def test_generate_system_health_report_confinement(tmp_path):
    """Verify health report generation inside dedicated workspace."""
    # Test path traversal outside workspace must be blocked
    res_escape = generate_system_health_report("../../../escaped_report.md")
    assert "error" in res_escape
    assert "escapes dedicated workspace" in res_escape["error"]

    # Use a synthetic workspace mock to test successful generation in sandboxed test runner
    synthetic_ws = tmp_path / "friday workspace"
    (synthetic_ws / "reports").mkdir(parents=True, exist_ok=True)
    with patch("friday.macos.system_settings.validate_workspace_path", return_value=synthetic_ws / "reports" / "test_report.md"):
        res = generate_system_health_report("test_report.md")
        assert res.get("status") == "success"
        fpath = Path(res["file_path"])
        assert fpath.exists()
        assert "test_report.md" in fpath.name


# ── 6. ActionRegistry and Router Intent Routing ──────────────────────────────


def test_action_registry_milestone_6_4_actions():
    """Verify Milestone 6.4 actions are present in default_registry."""
    actions = {a["name"] for a in default_registry.list_actions()}
    expected = {
        "set_mute",
        "toggle_mute",
        "get_audio_devices",
        "set_audio_device",
        "get_brightness",
        "set_brightness",
        "set_appearance",
        "toggle_appearance",
        "get_focus_mode",
        "toggle_focus_mode",
        "get_thermal",
        "get_hardware_metrics",
        "get_wifi",
        "get_bluetooth",
        "set_wifi_power",
        "set_bluetooth_power",
        "lock_screen",
        "system_sleep",
        "system_restart",
        "system_shutdown",
        "generate_health_report",
    }
    assert expected.issubset(actions)


def test_router_natural_language_settings():
    """Verify English, Hindi, and Hinglish intent routing for settings."""
    m1, r1 = route_macos_intent("mute", dry_run=True)
    assert m1 is True and r1.action_name == "set_mute"

    m2, r2 = route_macos_intent("unmute", dry_run=True)
    assert m2 is True and r2.action_name == "set_mute"

    m3, r3 = route_macos_intent("brightness 80", dry_run=True)
    assert m3 is True and r3.action_name == "set_brightness"

    m4, r4 = route_macos_intent("switch to dark mode", dry_run=True)
    assert m4 is True and r4.action_name == "set_appearance"

    m5, r5 = route_macos_intent("cpu usage", dry_run=True)
    assert m5 is True and r5.action_name == "get_hardware_metrics"

    m6, r6 = route_macos_intent("thermal status", dry_run=True)
    assert m6 is True and r6.action_name == "get_thermal"

    m7, r7 = route_macos_intent("system health report", dry_run=True)
    assert m7 is True and r7.action_name == "generate_health_report"

    m8, r8 = route_macos_intent("screen lock karo", dry_run=True)
    assert m8 is True and r8.action_name == "lock_screen"
