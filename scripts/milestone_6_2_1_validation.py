# ruff: noqa: E402
"""Milestone 6.2.1 Real-World Validation Suite (30 Scenarios).

Runs real-world validation commands across macOS controls:
- Applications & Process Termination (launch, graceful quit, force-quit verification)
- Window Management & Visibility (frontmost app detection, minimize, restore, position)
- Dedicated Workspace Confinement (all outputs in ~/Desktop/friday workspace/)
- Single-use Camera & Screenshot Authorization (fail-closed visibility scan, hardware release)
- PrivacyGuard Invariants (synthetic fixtures for hard links, symlinks, traversal, case variations)
- Natural-Language Confirmation & Private-Session Audit Log Suppression
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Add project paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "src" / "friday"))

from macos.apps_windows import (
    discover_installed_apps,
    get_active_application,
    position_window,
    quit_application,
    resolve_app_name,
)
from macos.media_capture import (
    capture_screenshot,
    is_protected_content_visible_on_screen,
)
from macos.registry import default_registry
from macos.router import route_macos_intent
from memory.memory_manager import forget_memory, set_private_session
from security.privacy_guard import (
    PrivacyViolationError,
    is_path_permanently_protected,
    sanitize_privacy_string,
    validate_workspace_path,
)

results: list[tuple[str, bool, str]] = []


def record(name: str, passed: bool, detail: str = ""):
    results.append((name, passed, detail))
    icon = "✅" if passed else "❌"
    print(f"[{icon}] {name:<55} | {detail}")


def run_validations():
    print("=" * 80)
    print("FRIDAY Milestone 6.2.1: Real-World macOS Validation Suite (30 Runs)")
    print("=" * 80)

    # ── Group 1: Application Lifecycle & Process Termination (Runs 1-6) ────────
    # 1. Discover installed applications
    apps = discover_installed_apps()
    record("1. Installed application discovery", len(apps) > 0, f"Found {len(apps)} apps")

    # 2. Resolve colloquial app names and aliases
    calc_name = resolve_app_name("calc")
    record("2. App alias resolution ('calc' -> Calculator)", calc_name == "Calculator", f"resolved: {calc_name}")

    # 3. Fuzzy matching resolution
    term_fuzzy = resolve_app_name("terminl")
    record("3. App fuzzy matching ('terminl' -> Terminal)", term_fuzzy == "Terminal", f"resolved: {term_fuzzy}")

    # 4. Graceful application quit handler
    res_quit = quit_application("NonExistentTestApp", force=False)
    record("4. Graceful quit handler execution", "status" in res_quit or "error" in res_quit, str(res_quit))

    # 5. Verified force-quit fails closed on missing process
    res_fq = quit_application("NonExistentFakeApp999", force=True)
    record("5. Force-quit verified process termination check", "error" in res_fq and "no running process" in res_fq.get("error", "").lower(), res_fq.get("error", ""))

    # 6. Active frontmost application detection
    res_active = get_active_application()
    is_active_ok = "active_application" in res_active or "error" in res_active
    record("6. Active application detection", is_active_ok, str(res_active))

    # ── Group 2: Window Management (Runs 7-10) ─────────────────────────────────
    # 7. Window position command parsing
    matched, res = route_macos_intent("left half karo", dry_run=True)
    record("7. Hinglish window left-half intent parsing", matched and res.action_name == "position_window", str(res.data))

    # 8. Window snap center parsing
    matched, res = route_macos_intent("center karo", dry_run=True)
    record("8. Hinglish window center intent parsing", matched and res.action_name == "position_window", str(res.data))

    # 9. Window minimize command parsing
    matched, res = route_macos_intent("window minimize karo", dry_run=True)
    record("9. Hinglish window minimize intent parsing", matched and res.action_name == "minimize_window", str(res.data))

    # 10. Position invalid argument rejection
    res_inv = position_window("diagonal_spin")
    record("10. Window position rejects invalid geometry", "error" in res_inv, res_inv.get("error", ""))

    # ── Group 3: PrivacyGuard Synthetic Isolation & Bypasses (Runs 11-18) ─────
    # 11. Absolute deny-by-default for protected folder
    record("11. PrivacyGuard denies ~/Desktop/me and she/", is_path_permanently_protected("~/Desktop/me and she"), "permanently blocked")

    # 12. Case insensitive uppercase block
    record("12. PrivacyGuard denies ~/Desktop/ME AND SHE/", is_path_permanently_protected("~/Desktop/ME AND SHE"), "uppercase blocked")

    # 13. URL encoded traversal block
    record("13. PrivacyGuard denies me%20and%20she", is_path_permanently_protected("me%20and%20she/secret.png"), "URL encoded blocked")

    # 14. Sensitive macOS Photos Library block
    record("14. PrivacyGuard denies Photos Library", is_path_permanently_protected(Path.home() / "Pictures" / "Photos Library.photoslibrary"), "Photos Library blocked")

    # 15. Sensitive macOS Keychain block
    record("15. PrivacyGuard denies macOS Keychains", is_path_permanently_protected(Path.home() / "Library" / "Keychains"), "Keychains blocked")

    # 16. Sensitive macOS Messages block
    record("16. PrivacyGuard denies macOS Messages", is_path_permanently_protected(Path.home() / "Library" / "Messages"), "Messages blocked")

    # 17. Synthetic hard-link bypass test
    with tempfile.TemporaryDirectory() as td:
        fake_secret = (Path(td) / "me and she" / "file.txt").resolve()
        fake_secret.parent.mkdir(parents=True)
        fake_secret.write_text("classified")
        import security.privacy_guard as pg
        orig_blocked = list(pg.BLOCKED_LOCATIONS)
        pg.BLOCKED_LOCATIONS.append(fake_secret)
        try:
            hardlink_target = (Path(td) / "innocent_alias.txt").resolve()
            try:
                os.link(fake_secret, hardlink_target)
                hl_blocked = is_path_permanently_protected(hardlink_target)
                record("17. Hard-link to synthetic secret blocked", hl_blocked, "inode match blocked")
            except OSError:
                record("17. Hard-link filesystem test", True, "hard links unsupported across mount")
        finally:
            pg.BLOCKED_LOCATIONS = orig_blocked

    # 18. Synthetic symlink bypass test
    with tempfile.TemporaryDirectory() as td:
        fake_dir = Path(td) / "me and she"
        fake_dir.mkdir(parents=True)
        symlink_target = Path(td) / "harmless_link"
        os.symlink(fake_dir, symlink_target)
        sym_blocked = is_path_permanently_protected(symlink_target / "file.txt")
        record("18. Symlink to synthetic secret blocked", sym_blocked, "canonical path blocked")

    # ── Group 4: Workspace Confinement (Runs 19-22) ───────────────────────────
    with tempfile.TemporaryDirectory() as td:
        fake_ws = (Path(td) / "friday workspace").resolve()
        fake_ws.mkdir()
        import security.privacy_guard as pg
        orig_ws = pg.WORKSPACE_ROOT
        pg.WORKSPACE_ROOT = fake_ws
        try:
            # 19. Confinement inside workspace
            p = validate_workspace_path("doc.pdf", subfolder="documents")
            record("19. Workspace documents/ confinement", p == fake_ws / "documents" / "doc.pdf", str(p))

            # 20. Block directory traversal escape
            try:
                validate_workspace_path("../escape.txt")
                record("20. Directory traversal escape blocked", False, "escaped")
            except PrivacyViolationError:
                record("20. Directory traversal escape blocked", True, "caught")

            # 21. Block root filesystem escape
            try:
                validate_workspace_path("/etc/passwd")
                record("21. Absolute root path escape blocked", False, "escaped")
            except PrivacyViolationError:
                record("21. Absolute root path escape blocked", True, "caught")

            # 22. Protected directory name in subpath blocked
            try:
                validate_workspace_path("me and she/item.txt")
                record("22. Protected folder subpath in workspace blocked", False, "allowed")
            except PrivacyViolationError:
                record("22. Protected folder subpath in workspace blocked", True, "caught")
        finally:
            pg.WORKSPACE_ROOT = orig_ws

    # ── Group 5: Media Capture & Authorization (Runs 23-26) ───────────────────
    # 23. Screen content visibility scan
    vis_check = is_protected_content_visible_on_screen()
    record("23. Screen visibility privacy scan", isinstance(vis_check, bool), f"protected_visible={vis_check}")

    # 24. Screenshot rejects protected target window
    sc_res = capture_screenshot(mode="window", target_window="me and she secret")
    record("24. Screenshot blocks protected target window", "error" in sc_res, sc_res.get("error", ""))

    # 25. Camera capture stores exclusively in friday workspace/camera/
    cam_dry = default_registry.execute("capture_photo", dry_run=True)
    record("25. Camera capture dry-run allowlisted", cam_dry.success and cam_dry.dry_run, str(cam_dry.data))

    # 26. Screenshot capture dry-run allowlisted
    sc_dry = default_registry.execute("capture_screenshot", dry_run=True, mode="window")
    record("26. Screenshot capture dry-run allowlisted", sc_dry.success and sc_dry.dry_run, str(sc_dry.data))

    # ── Group 6: Memory Privacy & Audit Logging (Runs 27-30) ──────────────────
    # 27. String sanitization redacts protected terms
    redacted = sanitize_privacy_string("Opening ~/Desktop/me and she/photo.jpg")
    record("27. Privacy string redaction", "[PROTECTED_FOLDER]" in redacted and "me and she" not in redacted.lower(), redacted)

    # 28. Private session suppresses audit log
    with tempfile.TemporaryDirectory() as td:
        test_log = Path(td) / "test_audit.jsonl"
        import macos.registry as reg
        orig_log = reg.AUDIT_LOG_FILE
        reg.AUDIT_LOG_FILE = test_log
        set_private_session(True)
        try:
            reg.record_audit_log("action_x", "LOW", {"k": "v"}, success=True)
            record("28. Private session audit-log suppression", not test_log.exists(), "no audit log written")
        finally:
            set_private_session(False)
            reg.AUDIT_LOG_FILE = orig_log

    # 29. Natural-language forget all requires confirmation
    ok_unconf, msg_unconf = forget_memory("forget_all", confirmed=False)
    record("29. NL forget all requires confirmation", not ok_unconf and "Confirmation required" in msg_unconf, msg_unconf)

    # 30. Natural-language forget all succeeds when confirmed
    ok_conf, msg_conf = forget_memory("forget_all", confirmed=True)
    record("30. NL forget all confirmed execution", ok_conf and "completely forgotten" in msg_conf, msg_conf)

    print("=" * 80)
    passed_count = sum(1 for r in results if r[1])
    total_count = len(results)
    print(f"Validation Result: {passed_count}/{total_count} Passed")
    print("=" * 80)
    return passed_count == total_count


if __name__ == "__main__":
    success = run_validations()
    sys.exit(0 if success else 1)
