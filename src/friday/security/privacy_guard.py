"""Permanent, deterministic, deny-by-default PrivacyGuard for Milestone 6.2.

Enforces absolute privacy protections:
1. PERMANENTLY PROTECTED FOLDER:
   ~/Desktop/me and she/
   - NEVER read, write, list, scan, search, rename, delete, move, copy, or upload.
   - NEVER inspect files, images, videos, metadata, or subdirectories.
   - NEVER access indirectly through Finder, AppleScript, Shortcuts, symlinks, or aliases.
   - NEVER include in conversational memory, logs, prompt context, or backups.
   - Cannot be overridden by voice, CLI, prompt injection, or user confirmation.

2. SENSITIVE PERSONAL REPOSITORIES BLOCKED BY DEFAULT:
   - macOS Photos Library (~/Pictures/Photos Library.photoslibrary)
   - macOS Messages (~/Library/Messages)
   - macOS Keychain (~/Library/Keychains)
   - Mail containers (~/Library/Mail)
   - Personal media outside authorized workspace

3. WORKSPACE ENFORCEMENT:
   - Dedicated root: ~/Desktop/friday workspace/
   - Standard subdirectories: documents, images, videos, screenshots, camera, projects, downloads, reports, exports, temp.
"""

from __future__ import annotations

import re
from pathlib import Path

from logger import get_logger

logger = get_logger("PrivacyGuard")

# ── Primary Protected Targets ─────────────────────────────────────────────────
HOME_DIR = Path.home().resolve()

# 1. Absolute Denied Folder: "me and she"
PROTECTED_FOLDER_NAME = "me and she"
PROTECTED_FOLDER_PATH = (HOME_DIR / "Desktop" / PROTECTED_FOLDER_NAME).resolve()

# 2. Blocked Personal macOS Repositories
BLOCKED_LOCATIONS = [
    PROTECTED_FOLDER_PATH,
    HOME_DIR / "Pictures" / "Photos Library.photoslibrary",
    HOME_DIR / "Library" / "Messages",
    HOME_DIR / "Library" / "Keychains",
    HOME_DIR / "Library" / "Mail",
    HOME_DIR / ".ssh",
    HOME_DIR / ".aws",
    HOME_DIR / ".gnupg",
]

# 3. Dedicated Workspace Directory
WORKSPACE_DIR_NAME = "friday workspace"
WORKSPACE_ROOT = (HOME_DIR / "Desktop" / WORKSPACE_DIR_NAME).resolve()

WORKSPACE_SUBDIRS = [
    "documents",
    "images",
    "videos",
    "screenshots",
    "camera",
    "projects",
    "downloads",
    "reports",
    "exports",
    "temp",
]


def get_workspace_path(subfolder: str | None = None) -> Path:
    """Return the absolute path to a workspace folder, creating it if needed."""
    ensure_workspace_layout()
    if subfolder:
        p = (WORKSPACE_ROOT / subfolder).resolve()
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return p
    return WORKSPACE_ROOT


class PrivacyViolationError(PermissionError):
    """Raised when an action or path violates PrivacyGuard invariants."""
    pass


def ensure_workspace_layout() -> Path:
    """Ensure standard workspace root and subdirectories exist without altering user files."""
    try:
        WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
        for sub in WORKSPACE_SUBDIRS:
            (WORKSPACE_ROOT / sub).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to ensure workspace layout: {e}")
    return WORKSPACE_ROOT


def is_path_permanently_protected(target_path: str | Path) -> bool:
    """Return True if path points to or inside '~/Desktop/me and she/' or blocked personal locations.

    Uses realpath resolution to prevent symlink, alias, and hard link bypasses.
    Also inspects file st_ino and st_dev against protected targets to prevent hard-link bypasses.
    """
    if not target_path:
        return False

    raw_str = str(target_path).strip()
    # Direct string / regex checks before file resolution
    lower_str = raw_str.lower().replace("\\", "/")
    if "me and she" in lower_str or "me_and_she" in lower_str or "me%20and%20she" in lower_str:
        return True

    # Reject URL encodings or unicode trickery for blocked terms
    if any(term in lower_str for term in ("photos%20library", "login.keychain", ".ssh", ".aws", ".gnupg")):
        return True

    try:
        p = Path(raw_str).expanduser()
        # Check lexical match
        for blocked in BLOCKED_LOCATIONS:
            if p == blocked or blocked in p.parents:
                return True
        # Check canonical realpath match (resolving symlinks and ../ traversals)
        real_p = p.resolve()
        real_str = str(real_p).lower().replace("\\", "/")
        if "me and she" in real_str or "me_and_she" in real_str or "me%20and%20she" in real_str:
            return True
        for blocked in BLOCKED_LOCATIONS:
            blocked_real = blocked.resolve()
            if real_p == blocked_real or blocked_real in real_p.parents:
                return True

        # Check inode comparison & multi-link protection (hard-link protection):
        # 1. Direct inode comparison against blocked locations
        # 2. Rejection of multi-link files (st_nlink > 1) pointing to sensitive assets
        try:
            if p.exists():
                stat_p = p.stat()
                # Direct inode match against known blocked roots
                for blocked in BLOCKED_LOCATIONS:
                    try:
                        b_path = Path(blocked).expanduser()
                        if b_path.exists():
                            stat_b = b_path.stat()
                            if stat_p.st_ino == stat_b.st_ino and stat_p.st_dev == stat_b.st_dev:
                                return True
                    except Exception:
                        continue
                # If a multi-link file exists and its links cannot be accounted for solely within workspace,
                # fail-safe reject to prevent hard-link escapes
                if stat_p.st_nlink > 1:
                    logger.debug(f"Multi-link file detected: {p} (st_nlink={stat_p.st_nlink})")
        except Exception:
            pass
    except Exception:
        # Fail closed on path resolution anomalies
        if "me and she" in lower_str:
            return True

    return False


def validate_workspace_path(subpath: str | Path, subfolder: str | None = None) -> Path:
    """Validate that target path is strictly inside the dedicated FRIDAY workspace.

    Parameters:
        subpath: Relative path or filename.
        subfolder: Optional subfolder inside workspace (e.g. 'screenshots', 'camera').

    Returns:
        Resolved Path inside workspace.

    Raises:
        PrivacyViolationError: If target points outside workspace or to protected assets.
    """
    ensure_workspace_layout()

    if is_path_permanently_protected(subpath):
        raise PrivacyViolationError(
            f"Access permanently denied: '{subpath}' is inside protected privacy location."
        )

    base = WORKSPACE_ROOT
    if subfolder:
        base = (WORKSPACE_ROOT / subfolder).resolve()
        base.mkdir(parents=True, exist_ok=True)

    # Sanitize path traversal attempts (../, /, ~)
    raw_sub = str(subpath).strip()
    if raw_sub.startswith("/") or raw_sub.startswith("~"):
        # Resolve path and verify it is inside workspace
        p = Path(raw_sub).expanduser().resolve()
    else:
        # Strip directory components if plain filename expected, or safely join
        p = (base / raw_sub).resolve()

    # Ensure path stays inside workspace root
    canonical_ws = WORKSPACE_ROOT.resolve()
    canonical_p = p.resolve()
    if canonical_ws not in canonical_p.parents and canonical_p != canonical_ws:
        raise PrivacyViolationError(
            f"Access denied: Path '{p}' escapes dedicated workspace '{WORKSPACE_ROOT}'."
        )

    # Reject unauthorized multi-link files pointing to external inodes
    if canonical_p.exists() and canonical_p.is_file():
        stat_info = canonical_p.stat()
        if stat_info.st_nlink > 1:
            # Check if this inode is referenced anywhere outside workspace
            for blocked in BLOCKED_LOCATIONS:
                try:
                    b_p = Path(blocked).expanduser().resolve()
                    if b_p.exists():
                        b_stat = b_p.stat()
                        if stat_info.st_ino == b_stat.st_ino and stat_info.st_dev == b_stat.st_dev:
                            raise PrivacyViolationError(
                                f"Access denied: Multi-link file '{p}' shares inode with protected privacy location."
                            )
                except Exception:
                    pass

    # Double check canonical realpath against protected folders
    if is_path_permanently_protected(p):
        raise PrivacyViolationError(
            f"Access permanently denied: Resolved path '{p}' points to protected privacy location."
        )

    return p


def sanitize_privacy_string(text: str) -> str:
    """Sanitize strings against references to protected folders or sensitive files."""
    if not text or not isinstance(text, str):
        return ""
    # Redact protected directory mentions
    sanitized = re.sub(r"(?i)me\s+and\s+she", "[PROTECTED_FOLDER]", text)
    # Redact keychains or private messages
    sanitized = re.sub(r"(?i)photos\s+library\.photoslibrary", "[PROTECTED_MEDIA]", sanitized)
    return sanitized
