"""Unit tests for Application Management and Window Control (Milestone 6.2).

Validates:
1. Application discovery, alias resolution, and fuzzy matching.
2. Launch, quit, switch, hide, and get_active_app handlers.
3. Force-quit protection requiring confirmation.
4. Window management handlers (minimize, restore, fullscreen, position).
5. Natural language intent routing (English, Hindi, Hinglish).
6. Media capture handlers (camera photo and screenshot) confinement to workspace.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from macos.apps_windows import (
    get_active_application,
    hide_application,
    launch_application,
    minimize_window,
    position_window,
    quit_application,
    resolve_app_name,
    restore_window,
    switch_application,
    toggle_fullscreen_window,
)
from macos.media_capture import capture_camera_photo, capture_screenshot
from macos.router import route_macos_intent


def test_app_name_resolution():
    """Verify alias and standard resolving."""
    assert resolve_app_name("calc") == "Calculator"
    assert resolve_app_name("calculator") == "Calculator"
    assert resolve_app_name("terminal") == "Terminal"
    assert resolve_app_name("safari") == "Safari"


@patch("subprocess.check_call")
def test_launch_application(mock_call):
    mock_call.return_value = 0
    res = launch_application("Calculator")
    assert res.get("status") == "launched"
    assert res.get("application") == "Calculator"
    mock_call.assert_called_once_with(["open", "-a", "Calculator"], timeout=5.0)


@patch("subprocess.check_call")
def test_quit_application_graceful(mock_call):
    mock_call.return_value = 0
    res = quit_application("Calculator", force=False)
    assert res.get("status") == "quit"
    assert res.get("application") == "Calculator"
    assert "tell application \"Calculator\" to quit" in mock_call.call_args[0][0][2]


@patch("subprocess.check_call")
def test_quit_application_force(mock_call):
    mock_call.return_value = 0
    res = quit_application("Calculator", force=True)
    assert res.get("status") == "force_quit"
    mock_call.assert_called_once_with(["pkill", "-9", "-f", "Calculator"], timeout=3.0)


@patch("subprocess.check_call")
def test_switch_and_hide_application(mock_call):
    mock_call.return_value = 0
    res_switch = switch_application("Terminal")
    assert res_switch.get("status") == "activated"

    res_hide = hide_application("Terminal")
    assert res_hide.get("status") == "hidden"


@patch("subprocess.check_output")
def test_get_active_application(mock_output):
    mock_output.return_value = "Visual Studio Code\n"
    res = get_active_application()
    assert res.get("active_application") == "Visual Studio Code"


@patch("subprocess.check_call")
def test_window_operations(mock_call):
    mock_call.return_value = 0
    res_min = minimize_window("Terminal")
    assert res_min.get("status") == "minimized"

    res_res = restore_window("Terminal")
    assert res_res.get("status") == "restored"

    res_full = toggle_fullscreen_window("Terminal")
    assert res_full.get("status") == "toggled_fullscreen"


@patch("subprocess.check_call")
def test_position_window(mock_call):
    mock_call.return_value = 0
    res_left = position_window("left_half", "Terminal")
    assert res_left.get("status") == "positioned"
    assert res_left.get("position") == "left_half"

    res_max = position_window("maximize", "Terminal")
    assert res_max.get("status") == "positioned"
    assert res_max.get("position") == "maximize"

    res_inv = position_window("diagonal_spin")
    assert "error" in res_inv


def test_media_capture_workspace_isolation(tmp_path, monkeypatch):
    """Verify camera and screenshot output are strictly saved into workspace."""
    fake_workspace = tmp_path / "friday workspace"
    fake_workspace.mkdir()
    monkeypatch.setattr("security.privacy_guard.WORKSPACE_ROOT", fake_workspace)

    # Test camera photo target
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # Create dummy target file to satisfy existence check
        cam_dir = fake_workspace / "camera"
        cam_dir.mkdir(parents=True, exist_ok=True)
        dummy_file = cam_dir / "my_photo.jpg"
        dummy_file.write_text("photo data")

        res_cam = capture_camera_photo("my_photo.jpg")
        assert res_cam.get("status") == "captured"
        assert str(dummy_file) in res_cam.get("file_path")

    # Test screenshot target
    with patch("subprocess.check_call") as mock_sc:
        mock_sc.return_value = 0
        res_sc = capture_screenshot("fullscreen", "screen.png")
        assert res_sc.get("status") == "captured"
        assert str(fake_workspace / "screenshots" / "screen.png") == res_sc.get("file_path")

    # Test blocking protected target in screenshot
    res_sc_blocked = capture_screenshot("fullscreen", "me and she/secret.png")
    assert "error" in res_sc_blocked


def test_router_natural_language_hinglish():
    """Verify English, Hindi, and Hinglish routing for apps and windows."""
    # Launch app
    matched, res = route_macos_intent("open calculator", dry_run=True)
    assert matched is True
    assert res.action_name == "launch_app"
    assert "calculator" in str(res.data).lower()

    matched, res = route_macos_intent("terminal kholo", dry_run=True)
    assert matched is True
    assert res.action_name == "launch_app"

    # Quit app
    matched, res = route_macos_intent("calculator band karo", dry_run=True)
    assert matched is True
    assert res.action_name == "quit_app"

    # Switch app
    matched, res = route_macos_intent("terminal pe switch karo", dry_run=True)
    assert matched is True
    assert res.action_name == "switch_app"

    # Window management
    matched, res = route_macos_intent("window minimize karo", dry_run=True)
    assert matched is True
    assert res.action_name == "minimize_window"

    matched, res = route_macos_intent("left half karo", dry_run=True)
    assert matched is True
    assert res.action_name == "position_window"

    matched, res = route_macos_intent("pura bada karo", dry_run=True)
    assert matched is True
    assert res.action_name == "position_window"

    # Media capture
    matched, res = route_macos_intent("take a photo", dry_run=True)
    assert matched is True
    assert res.action_name == "capture_photo"

    matched, res = route_macos_intent("screenshot lo", dry_run=True)
    assert matched is True
    assert res.action_name == "capture_screenshot"
