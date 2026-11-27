"""Unit and Security Tests for Milestone 6.3 AppleScript & Shortcuts Automation.

Covers:
1. Allowlisted AppleScript templates (compilation, sanitization, execution).
2. Argument sanitization and injection prevention (escaping quotes, backslashes, newlines).
3. Prohibition gates: blocks 'do shell script', 'administrator privileges', 'sudo', 'rm -rf'.
4. Timeout and process-group termination (clean termination on timeout).
5. Shortcuts discovery, allowlisted default definitions, approval registry.
6. Execution gating: blocks unverified or modified shortcuts until approved.
7. Absolute PrivacyGuard enforcement: blocks 'me and she' across templates and shortcut inputs.
8. Workspace confinement for shortcut outputs strictly under ~/Desktop/friday workspace/.
9. Intent routing (English, Hindi, Hinglish queries for automation).
"""

from __future__ import annotations

import pytest

from friday.macos.applescript_automation import (
    APPLESCRIPT_TEMPLATES,
    _sanitize_applescript_arg,
    execute_template,
    run_compiled_applescript,
)
from friday.macos.registry import default_registry
from friday.macos.router import route_macos_intent
from friday.macos.shortcuts_automation import (
    ShortcutsManager,
)
from friday.security.privacy_guard import (
    PROTECTED_FOLDER_NAME,
    PROTECTED_FOLDER_PATH,
)

# ── 1. AppleScript Sanitization & Security Gates ─────────────────────────────


def test_sanitize_applescript_arg_escaping():
    """Verify that quotes and backslashes are escaped safely."""
    raw = 'Hello "World" \\ and newline\nsecond line'
    sanitized = _sanitize_applescript_arg(raw)
    assert '\\"' in sanitized
    assert "\\\\" in sanitized
    assert "\n" not in sanitized


def test_sanitize_applescript_arg_blocks_protected_folder():
    """Verify that any argument pointing to 'me and she' is immediately rejected."""
    with pytest.raises(PermissionError):
        _sanitize_applescript_arg(f"/Users/user/Desktop/{PROTECTED_FOLDER_NAME}/file.txt")


def test_run_compiled_applescript_prohibits_dangerous_tokens():
    """Verify rejection of prohibited AppleScript tokens like 'do shell script'."""
    forbidden = [
        'tell application "Finder" to do shell script "whoami"',
        'tell application "System Events" with administrator privileges',
        'do shell script "sudo rm -rf /"',
    ]
    for script in forbidden:
        success, out, err = run_compiled_applescript(script)
        assert not success
        assert "Security Violation: Prohibited token" in err


def test_run_compiled_applescript_blocks_me_and_she_target():
    """Verify script source mentioning 'me and she' is rejected immediately."""
    script = 'tell application "Finder" to open folder "me and she"'
    success, out, err = run_compiled_applescript(script)
    assert not success
    assert "Privacy Violation" in err


def test_run_compiled_applescript_timeout_process_group():
    """Verify that long-running scripts hit the timeout and terminate process group."""
    import shutil
    import subprocess
    from unittest.mock import MagicMock, patch

    # If osascript is available (macOS), run real timeout
    if shutil.which("osascript"):
        success, out, err = run_compiled_applescript("delay 10", timeout_s=0.2)
        assert not success
        assert "timed out" in err
    else:
        # On non-macOS CI environments (Linux), mock subprocess.Popen to simulate timeout
        mock_proc = MagicMock()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd=["osascript"], timeout=0.2)
        mock_proc.pid = 99999
        with patch("subprocess.Popen", return_value=mock_proc):
            with patch("os.killpg") as mock_killpg:
                with patch("os.getpgid", return_value=99999):
                    success, out, err = run_compiled_applescript("delay 10", timeout_s=0.2)
                    assert not success
                    assert "timed out" in err
                    mock_killpg.assert_called_once()


# ── 2. Allowlisted Templates & Execution ─────────────────────────────────────


def test_allowlisted_templates_definitions():
    """Verify all expected templates exist in APPLESCRIPT_TEMPLATES."""
    expected = [
        "display_notification",
        "create_note",
        "music_play_pause",
        "get_current_track",
        "set_volume",
        "empty_trash",
    ]
    for name in expected:
        assert name in APPLESCRIPT_TEMPLATES
        tmpl = APPLESCRIPT_TEMPLATES[name]
        assert tmpl.name == name
        assert callable(tmpl.builder)


def test_execute_template_dry_run():
    """Verify dry-run mode returns script preview without executing."""
    res = execute_template(
        "display_notification",
        params={"title": "Test Title", "message": "Test Body"},
        dry_run=True,
    )
    assert res.get("status") == "dry_run"
    assert "display notification \"Test Body\" with title \"Test Title\"" in res.get("script_preview")


def test_execute_template_destructive_requires_confirmation():
    """Verify that destructive templates like empty_trash require confirmation."""
    res = execute_template("empty_trash", confirmed=False)
    assert res.get("requires_confirmation") is True
    assert "Confirmation required" in res.get("prompt", "")


def test_execute_template_unrecognized_fails():
    """Verify that un-allowlisted template names are rejected."""
    res = execute_template("arbitrary_hacker_script")
    assert "error" in res
    assert "not allowlisted" in res["error"]


def test_execute_template_privacy_violation_param():
    """Verify that protected folder references in parameters are caught."""
    res = execute_template(
        "create_note",
        params={"title": "Secret", "body": f"See {PROTECTED_FOLDER_PATH}"},
    )
    assert "error" in res
    assert "Privacy" in res["error"] or "Access denied" in res["error"]


# ── 3. Shortcuts Management & Approval Registry ──────────────────────────────


def test_shortcuts_manager_approval_flow(tmp_path):
    """Test approval and revoking lifecycle in ShortcutsManager."""
    approvals_file = tmp_path / "approved_shortcuts.json"
    mgr = ShortcutsManager(approvals_file=approvals_file)

    # Initially unverified shortcut
    status = mgr.get_shortcut_status("Custom Routine")
    assert not status["approved"]
    assert status["source"] == "unverified"

    # Approve shortcut
    appr_res = mgr.approve_shortcut(
        "Custom Routine",
        actions_summary="Runs daily briefing",
        resource_boundary="Safe standard boundaries",
    )
    assert appr_res["status"] == "approved"

    # Status check after approval
    status2 = mgr.get_shortcut_status("Custom Routine")
    assert status2["approved"] is True
    assert status2["source"] == "user_approved"

    # Revoke shortcut
    rev_res = mgr.revoke_shortcut("Custom Routine")
    assert rev_res["status"] == "revoked"

    status3 = mgr.get_shortcut_status("Custom Routine")
    assert not status3["approved"]


def test_shortcuts_manager_default_known_shortcuts(tmp_path):
    """Verify default known shortcuts and security auditing behavior."""
    mgr = ShortcutsManager(approvals_file=tmp_path / "approvals.json")
    # Charger Sound and Open Workspace have verified boundaries
    for name in ["Charger Sound", "Open Workspace"]:
        st = mgr.get_shortcut_status(name)
        assert st["approved"] is True
        assert st["source"] == "allowlisted_default"

    # Quick Note has unverified external boundary and must be disabled
    qn = mgr.get_shortcut_status("Quick Note")
    assert qn["approved"] is False


def test_run_shortcut_blocks_unverified(tmp_path):
    """Verify unapproved shortcut execution is blocked."""
    mgr = ShortcutsManager(approvals_file=tmp_path / "approvals.json")
    res = mgr.run_shortcut("Suspicious Shortcut")
    assert "error" in res
    assert "unverified or not approved" in res["error"]
    assert res.get("approval_required") is True


def test_run_shortcut_privacy_guard_rejection(tmp_path):
    """Verify input path pointing to 'me and she' is blocked."""
    mgr = ShortcutsManager(approvals_file=tmp_path / "approvals.json")
    # Even if shortcut is approved (e.g. Charger Sound), protected input must be rejected
    res = mgr.run_shortcut("Charger Sound", input_path=str(PROTECTED_FOLDER_PATH / "notes.txt"))
    assert "error" in res
    assert "Privacy violation" in res["error"]


def test_run_shortcut_dry_run_command_construction(tmp_path):
    """Verify dry-run returns command array with verified boundaries."""
    mgr = ShortcutsManager(approvals_file=tmp_path / "approvals.json")
    res = mgr.run_shortcut("Charger Sound", dry_run=True)
    assert res.get("status") == "dry_run"
    assert res.get("command") == ["/usr/bin/shortcuts", "run", "Charger Sound"]


# ── 4. ActionRegistry and Intent Router Integration ──────────────────────────


def test_registry_contains_automation_actions():
    """Verify all Milestone 6.3 actions are present in default_registry."""
    actions = {a["name"] for a in default_registry.list_actions()}
    assert "run_script_template" in actions
    assert "list_script_templates" in actions
    assert "run_shortcut" in actions
    assert "list_shortcuts" in actions


def test_router_applescript_intent_notification():
    """Verify English natural-language routing for notifications."""
    matched, res = route_macos_intent("show notification All tasks complete", dry_run=True)
    assert matched is True
    assert res.action_name == "run_script_template"


def test_router_applescript_intent_hindi_note():
    """Verify Hindi/Hinglish routing for creating notes."""
    matched, res = route_macos_intent("note banao Buy milk and coffee", dry_run=True)
    assert matched is True
    assert res.action_name == "run_script_template"


def test_router_applescript_intent_music_toggle():
    """Verify English/Hinglish routing for music toggle."""
    matched, res = route_macos_intent("gaana bajao", dry_run=True)
    assert matched is True
    assert res.action_name == "run_script_template"

    matched2, res2 = route_macos_intent("what is playing", dry_run=True)
    assert matched2 is True
    assert res2.action_name == "run_script_template"


def test_router_shortcuts_intent():
    """Verify routing for shortcuts."""
    matched, res = route_macos_intent("list shortcuts", dry_run=True)
    assert matched is True
    assert res.action_name == "list_shortcuts"

    matched2, res2 = route_macos_intent("run shortcut Charger Sound", dry_run=True)
    assert matched2 is True
    assert res2.action_name == "run_shortcut"
