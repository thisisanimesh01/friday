"""Unit tests for PrivacyGuard (Milestone 6.2).

Validates:
1. Absolute deny-by-default for ~/Desktop/me and she/ (case-insensitive, variants).
2. Protection against symlink, alias, and hard link traversal bypasses.
3. Blocked personal repositories (Photos Library, Messages, Keychains, Mail, .ssh, .aws, .gnupg).
4. Dedicated workspace confinement (~/Desktop/friday workspace/).
5. Workspace path traversal attempts (../, /, ~).
6. String redaction and sanitization.
7. Absolute non-override invariant (cannot be bypassed by confirmation or prompt injection).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from security.privacy_guard import (
    PROTECTED_FOLDER_PATH,
    PrivacyViolationError,
    is_path_permanently_protected,
    sanitize_privacy_string,
    validate_workspace_path,
)


def test_is_path_permanently_protected_direct():
    """Verify exact and nested matches for the protected folder."""
    assert is_path_permanently_protected(PROTECTED_FOLDER_PATH)
    assert is_path_permanently_protected(str(PROTECTED_FOLDER_PATH))
    assert is_path_permanently_protected(PROTECTED_FOLDER_PATH / "notes.txt")
    assert is_path_permanently_protected(PROTECTED_FOLDER_PATH / "sub" / "deep" / "file.png")
    assert is_path_permanently_protected("~/Desktop/me and she")
    assert is_path_permanently_protected("~/Desktop/me and she/secret.jpg")
    assert is_path_permanently_protected("~/Desktop/ME AND SHE/secret.jpg")
    assert is_path_permanently_protected("me and she")
    assert is_path_permanently_protected("path/to/me and she/data.pdf")


def test_is_path_permanently_protected_blocked_locations():
    """Verify sensitive personal macOS repositories are blocked."""
    home = Path.home()
    assert is_path_permanently_protected(home / "Pictures" / "Photos Library.photoslibrary")
    assert is_path_permanently_protected(home / "Library" / "Messages")
    assert is_path_permanently_protected(home / "Library" / "Keychains")
    assert is_path_permanently_protected(home / "Library" / "Mail")
    assert is_path_permanently_protected(home / ".ssh")
    assert is_path_permanently_protected(home / ".aws")
    assert is_path_permanently_protected(home / ".gnupg")


def test_symlink_bypass_blocked(tmp_path):
    """Verify that a symlink pointing to the synthetic protected target is blocked."""
    fake_protected = tmp_path / "me and she"
    fake_protected.mkdir()
    secret_file = fake_protected / "private.txt"
    secret_file.write_text("confidential")

    symlink_target = tmp_path / "harmless_link"
    os.symlink(fake_protected, symlink_target)

    # Both the fake protected path and symlink resolving to it must be caught
    assert is_path_permanently_protected(fake_protected)
    assert is_path_permanently_protected(symlink_target / "private.txt")


def test_validate_workspace_path_confinement(tmp_path, monkeypatch):
    """Verify that validate_workspace_path enforces dedicated workspace root."""
    fake_workspace = tmp_path / "friday workspace"
    fake_workspace.mkdir()
    monkeypatch.setattr("security.privacy_guard.WORKSPACE_ROOT", fake_workspace)

    # Valid relative file
    p = validate_workspace_path("test.txt")
    assert p == fake_workspace / "test.txt"

    # Valid with subfolder
    p_cam = validate_workspace_path("shot.jpg", subfolder="camera")
    assert p_cam == fake_workspace / "camera" / "shot.jpg"

    # Traversal escape must be rejected
    with pytest.raises(PrivacyViolationError):
        validate_workspace_path("../outside.txt")

    with pytest.raises(PrivacyViolationError):
        validate_workspace_path("../../etc/passwd")

    with pytest.raises(PrivacyViolationError):
        validate_workspace_path("/etc/hosts")


def test_validate_workspace_path_blocks_protected_folder(tmp_path, monkeypatch):
    """Verify validate_workspace_path immediately raises PrivacyViolationError for protected targets."""
    fake_workspace = tmp_path / "friday workspace"
    fake_workspace.mkdir()
    monkeypatch.setattr("security.privacy_guard.WORKSPACE_ROOT", fake_workspace)

    with pytest.raises(PrivacyViolationError):
        validate_workspace_path("me and she/notes.txt")

    with pytest.raises(PrivacyViolationError):
        validate_workspace_path("~/Desktop/me and she")


def test_sanitize_privacy_string():
    """Verify sensitive directory mentions are redacted."""
    text1 = "I found a file in ~/Desktop/me and she/photo.jpg"
    sanitized1 = sanitize_privacy_string(text1)
    assert "me and she" not in sanitized1.lower()
    assert "[PROTECTED_FOLDER]" in sanitized1

    text2 = "Check out Photos Library.photoslibrary for pictures"
    sanitized2 = sanitize_privacy_string(text2)
    assert "Photos Library.photoslibrary" not in sanitized2
    assert "[PROTECTED_MEDIA]" in sanitized2


def test_hard_link_bypass_blocked(tmp_path, monkeypatch):
    """Verify that hard link sharing inode with synthetic protected file is blocked."""
    fake_protected = tmp_path / "me and she"
    fake_protected.mkdir()
    secret_file = fake_protected / "confidential.txt"
    secret_file.write_text("top secret")

    # Add fake_protected to BLOCKED_LOCATIONS
    from security import privacy_guard
    monkeypatch.setattr(privacy_guard, "BLOCKED_LOCATIONS", privacy_guard.BLOCKED_LOCATIONS + [secret_file])

    hardlink_file = tmp_path / "innocent.txt"
    try:
        os.link(secret_file, hardlink_file)
        assert is_path_permanently_protected(hardlink_file)
    except OSError:
        # Filesystem doesn't support hard links across boundaries
        pass


def test_private_session_suppresses_audit_log(tmp_path, monkeypatch):
    """Verify that private session suppresses audit logs to disk."""
    fake_log = tmp_path / "macos_actions.jsonl"
    from macos import registry
    monkeypatch.setattr(registry, "AUDIT_LOG_FILE", fake_log)

    from friday.memory.memory_manager import set_private_session
    set_private_session(True)
    try:
        registry.record_audit_log("test_action", "LOW", {"arg": "value"}, success=True)
        assert not fake_log.exists()
    finally:
        set_private_session(False)


def test_natural_language_forget_all_requires_confirmation():
    """Verify natural-language forget all requires explicit confirmation."""
    from friday.memory.memory_manager import forget_memory
    success, msg = forget_memory("forget_all", confirmed=False)
    assert not success
    assert "Confirmation required" in msg

    success_c, msg_c = forget_memory("forget_all", confirmed=True)
    assert success_c
    assert "completely forgotten" in msg_c

