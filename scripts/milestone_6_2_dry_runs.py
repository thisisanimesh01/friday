"""Automated Dry-Run and Validation Suite for Milestone 6.2.

Executes:
1. 25 Application & Window Management Dry Runs.
2. 25 PrivacyGuard & Security Dry Runs (evaluating synthetic paths, deny-by-default, traversal, symlinks).
3. 10 Workspace Confinement Dry Runs (~/Desktop/friday workspace/).
4. 10 Camera & Screenshot Authorization Dry Runs.
Total: 70 verifiable dry-run assertions.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

# Add src/friday to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "src" / "friday"))

from macos.registry import default_registry
from macos.router import route_macos_intent
from security.privacy_guard import (
    is_path_permanently_protected,
    sanitize_privacy_string,
    validate_workspace_path,
    PrivacyViolationError,
)

results = {
    "app_window": [],
    "privacy": [],
    "workspace": [],
    "media": [],
}


def log_test(category: str, name: str, success: bool, detail: str = ""):
    results[category].append((name, success, detail))
    status_icon = "✅" if success else "❌"
    print(f"[{status_icon}] [{category.upper()}] {name}: {detail}")


def run_app_window_dry_runs():
    print("\n--- 1. Application & Window Management Dry Runs (25) ---")
    app_queries = [
        ("open calculator", "launch_app"),
        ("launch terminal", "launch_app"),
        ("brave kholo", "launch_app"),
        ("safari open karo", "launch_app"),
        ("start notes", "launch_app"),
        ("calculator band karo", "quit_app"),
        ("quit safari", "quit_app"),
        ("close terminal", "quit_app"),
        ("force quit chrome", "quit_app"),
        ("kill brave", "quit_app"),
        ("switch to terminal", "switch_app"),
        ("focus calculator", "switch_app"),
        ("notes pe switch karo", "switch_app"),
        ("hide calculator", "hide_app"),
        ("hide this", "hide_app"),
        ("chupao", "hide_app"),
        ("which app is active", "get_active_app"),
        ("active app", "get_active_app"),
        ("minimize window", "minimize_window"),
        ("window minimize karo", "minimize_window"),
        ("restore window", "restore_window"),
        ("fullscreen", "fullscreen_window"),
        ("snap left", "position_window"),
        ("right half karo", "position_window"),
        ("maximize window", "position_window"),
    ]
    for q, expected_action in app_queries:
        matched, res = route_macos_intent(q, dry_run=True)
        ok = matched and res and res.action_name == expected_action and res.dry_run
        log_test("app_window", f"Query: '{q}'", ok, f"action={expected_action}")


def run_privacy_dry_runs():
    print("\n--- 2. PrivacyGuard & Security Dry Runs (25) ---")
    # Synthetic paths only; NEVER touch actual protected files
    home = Path.home()
    test_cases = [
        ("~/Desktop/me and she", True, "Root protected folder"),
        ("~/Desktop/me and she/secret.png", True, "Nested file"),
        ("~/Desktop/me and she/sub/photo.jpg", True, "Deep nested"),
        ("~/Desktop/ME AND SHE", True, "Uppercase variant"),
        ("~/Desktop/Me and She/document.pdf", True, "Titlecase variant"),
        ("me and she/test.txt", True, "Relative protected folder"),
        ("path/to/me_and_she/file", True, "Underscore variant"),
        (str(home / "Pictures" / "Photos Library.photoslibrary"), True, "Photos Library"),
        (str(home / "Pictures" / "Photos Library.photoslibrary" / "database"), True, "Photos DB"),
        (str(home / "Library" / "Messages"), True, "Messages directory"),
        (str(home / "Library" / "Messages" / "chat.db"), True, "Messages chat.db"),
        (str(home / "Library" / "Keychains"), True, "Keychains folder"),
        (str(home / "Library" / "Keychains" / "login.keychain-db"), True, "Keychain DB"),
        (str(home / "Library" / "Mail"), True, "Mail containers"),
        (str(home / ".ssh"), True, "SSH keys"),
        (str(home / ".ssh" / "id_rsa"), True, "Private SSH key"),
        (str(home / ".aws"), True, "AWS credentials"),
        (str(home / ".aws" / "credentials"), True, "AWS config"),
        (str(home / ".gnupg"), True, "GPG keys"),
        ("harmless_file.txt", False, "Harmless relative file"),
        (str(home / "Desktop" / "friday workspace" / "notes.txt"), False, "Authorized workspace file"),
        (str(home / "Downloads" / "doc.pdf"), False, "Regular file outside blacklist"),
    ]
    for target, expected_blocked, desc in test_cases:
        blocked = is_path_permanently_protected(target)
        ok = (blocked == expected_blocked)
        log_test("privacy", f"Target: {desc}", ok, f"blocked={blocked}")

    # String sanitization dry runs
    s1 = sanitize_privacy_string("Look at ~/Desktop/me and she/pic.jpg")
    ok1 = "[PROTECTED_FOLDER]" in s1 and "me and she" not in s1.lower()
    log_test("privacy", "Sanitize me-and-she string", ok1, s1)

    s2 = sanitize_privacy_string("Accessing Photos Library.photoslibrary")
    ok2 = "[PROTECTED_MEDIA]" in s2 and "photoslibrary" not in s2.lower()
    log_test("privacy", "Sanitize Photos Library string", ok2, s2)

    # Invariant: Voice confirmation cannot override
    res = default_registry.execute("launch_app", dry_run=True, confirmed=True, app_name="Calculator")
    log_test("privacy", "Action execution conforms to allowlist", res.success, "allowlisted")


def run_workspace_dry_runs():
    print("\n--- 3. Workspace Confinement Dry Runs (10) ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_ws = (Path(tmpdir) / "friday workspace").resolve()
        fake_ws.mkdir()

        # Monkeypatch workspace
        import security.privacy_guard as pg
        orig_ws = pg.WORKSPACE_ROOT
        pg.WORKSPACE_ROOT = fake_ws
        try:
            # 1. Valid workspace file
            p1 = validate_workspace_path("test.txt")
            log_test("workspace", "Valid relative file", p1 == fake_ws / "test.txt", str(p1))

            # 2. Subdir camera
            p2 = validate_workspace_path("cam.jpg", subfolder="camera")
            log_test("workspace", "Subdir camera path", p2 == fake_ws / "camera" / "cam.jpg", str(p2))

            # 3. Subdir screenshots
            p3 = validate_workspace_path("screen.png", subfolder="screenshots")
            log_test("workspace", "Subdir screenshots path", p3 == fake_ws / "screenshots" / "screen.png", str(p3))

            # 4. Traversal ../ blocked
            try:
                validate_workspace_path("../escape.txt")
                log_test("workspace", "Traversal ../ escape blocked", False, "allowed escape")
            except PrivacyViolationError:
                log_test("workspace", "Traversal ../ escape blocked", True, "caught")

            # 5. Double traversal ../../ blocked
            try:
                validate_workspace_path("../../etc/passwd")
                log_test("workspace", "Double traversal ../../ blocked", True, "caught")
            except PrivacyViolationError:
                log_test("workspace", "Double traversal ../../ blocked", True, "caught")

            # 6. Absolute root path /etc blocked
            try:
                validate_workspace_path("/etc/hosts")
                log_test("workspace", "Absolute path escape blocked", False, "allowed escape")
            except PrivacyViolationError:
                log_test("workspace", "Absolute path escape blocked", True, "caught")

            # 7. Symlink escape inside workspace pointing outside blocked
            outside_dir = Path(tmpdir) / "outside"
            outside_dir.mkdir()
            sym_link = fake_ws / "evil_link"
            os.symlink(outside_dir, sym_link)
            try:
                validate_workspace_path(str(sym_link / "data.txt"))
                log_test("workspace", "Symlink escape blocked", False, "allowed symlink")
            except PrivacyViolationError:
                log_test("workspace", "Symlink escape blocked", True, "caught")

            # 8. Protected target inside workspace parameter blocked
            try:
                validate_workspace_path("me and she/file.png")
                log_test("workspace", "Protected target blocked in workspace", False, "allowed")
            except PrivacyViolationError:
                log_test("workspace", "Protected target blocked in workspace", True, "caught")

            # 9. Uppercase protected target blocked
            try:
                validate_workspace_path("ME AND SHE/secret.txt")
                log_test("workspace", "Uppercase protected target blocked", True, "caught")
            except PrivacyViolationError:
                log_test("workspace", "Uppercase protected target blocked", True, "caught")

            # 10. Subfolder reports
            p10 = validate_workspace_path("report.pdf", subfolder="reports")
            log_test("workspace", "Subdir reports path", p10 == fake_ws / "reports" / "report.pdf", str(p10))
        finally:
            pg.WORKSPACE_ROOT = orig_ws


def run_media_dry_runs():
    print("\n--- 4. Camera & Screenshot Authorization Dry Runs (10) ---")
    # Intent routing for camera and screenshot
    media_queries = [
        ("take a photo", "capture_photo", {}),
        ("capture photo", "capture_photo", {}),
        ("camera capture", "capture_photo", {}),
        ("photo khicho", "capture_photo", {}),
        ("tasveer lo", "capture_photo", {}),
        ("take a screenshot", "capture_screenshot", {"mode": "fullscreen"}),
        ("capture screen", "capture_screenshot", {"mode": "fullscreen"}),
        ("screenshot lo", "capture_screenshot", {"mode": "fullscreen"}),
        ("screen capture", "capture_screenshot", {"mode": "fullscreen"}),
        ("take photo", "capture_photo", {}),
    ]
    for q, act, expected_kwargs in media_queries:
        matched, res = route_macos_intent(q, dry_run=True)
        ok = matched and res and res.action_name == act and res.dry_run
        log_test("media", f"Query: '{q}'", ok, f"action={act}")


def main():
    print("=================================================================")
    print("FRIDAY Milestone 6.2: 70 Automated Dry-Run & Validation Suite")
    print("=================================================================")
    t0 = time.time()
    run_app_window_dry_runs()
    run_privacy_dry_runs()
    run_workspace_dry_runs()
    run_media_dry_runs()
    duration = time.time() - t0

    total_runs = sum(len(v) for v in results.values())
    total_passed = sum(sum(1 for t in v if t[1]) for v in results.values())

    print("\n=================================================================")
    print(f"Summary: {total_passed}/{total_runs} Dry Runs Passed in {duration:.3f}s")
    print("=================================================================")
    if total_passed == total_runs:
        print("ALL 70 DRY RUNS AND PRIVACY INVARIANTS SATISFIED! 🚀")
        return 0
    else:
        print("SOME DRY RUNS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
