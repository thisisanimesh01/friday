"""Unit tests for Screen Capture Foundation & Permission Hardening (Milestone 7.1)."""



from friday.macos.media_capture import (
    capture_screen,
    check_screen_recording_permission,
    create_synthetic_test_png,
    discover_displays,
    get_active_capture_authorization,
    issue_single_use_capture_authorization,
    revoke_capture_authorization,
    validate_and_strip_png,
)
from friday.macos.router import route_macos_intent


def test_screen_capture_dry_run_never_touches_disk(tmp_path):
    target = tmp_path / "test_preview.png"
    res = capture_screen(mode="fullscreen", output_filename=target.name, dry_run=True)
    assert res.get("status") == "dry_run"
    assert not target.exists()
    assert "no file written" in res.get("message", "").lower()


def test_permission_detection_structure():
    perm = check_screen_recording_permission()
    assert "granted" in perm
    assert "status" in perm
    assert isinstance(perm["granted"], bool)


def test_discover_displays_structure():
    displays = discover_displays()
    assert len(displays) >= 1
    d0 = displays[0]
    assert d0["index"] == 1
    assert "resolution" in d0
    assert d0["width"] > 0
    assert d0["height"] > 0
    assert "is_main" in d0


def test_single_use_authorization_lifecycle():
    token = issue_single_use_capture_authorization(mode="fullscreen", timeout_s=10.0)
    assert token.nonce is not None
    assert token.mode == "fullscreen"
    assert token.consumed is False

    valid, msg = token.is_valid("fullscreen")
    assert valid is True

    # Mode mismatch check
    mismatch, m_msg = token.is_valid("window")
    assert mismatch is False
    assert "mismatch" in m_msg.lower()

    # Revoke
    revoke_capture_authorization()
    assert get_active_capture_authorization() is None


def test_png_validation_and_metadata_stripping(tmp_path):
    test_png = tmp_path / "test_synth.png"
    create_synthetic_test_png(test_png, width=50, height=50)
    assert test_png.exists()

    valid, msg = validate_and_strip_png(test_png)
    assert valid is True
    assert "stripped" in msg.lower()


def test_region_capture_coordinate_validation():
    # Negative dimensions
    res1 = capture_screen(mode="region", region=(0, 0, -10, 50))
    assert "error" in res1
    assert "Invalid region dimensions" in res1["error"]

    # Incomplete coordinates
    res2 = capture_screen(mode="region", region=(10, 20))  # type: ignore
    assert "error" in res2


def test_privacy_guard_blocks_protected_target():
    res = capture_screen(mode="window", target_window="me and she personal")
    assert "error" in res
    assert "protected privacy location" in res["error"]
    assert res.get("privacy_guard") == "FAIL_CLOSED"


def test_router_milestone_7_1_intents():
    queries = [
        ("Friday, take a screenshot", "capture_screenshot"),
        ("screenshot lo", "capture_screenshot"),
        ("capture the active window", "capture_screen"),
        ("active window capture karo", "capture_screen"),
        ("stop the capture", "cancel_capture"),
        ("screen recording permission", "check_screen_recording_permission"),
        ("discover displays", "discover_displays"),
    ]
    for text, expected_action in queries:
        matched, res = route_macos_intent(text, dry_run=True, confirmed=True)
        assert matched is True, f"Failed to match query: '{text}'"
        assert res.action_name == expected_action
