import os

from security.privacy_guard import (
    WORKSPACE_ROOT,
    is_path_permanently_protected,
    validate_workspace_path,
)

BASE_DIR = str(WORKSPACE_ROOT)

def get_safe_path(filename: str) -> str:
    # 1. Deny-by-default check for permanently protected folders
    if is_path_permanently_protected(filename):
        raise PermissionError("Access denied: protected privacy location")

    # If BASE_DIR is customized (e.g. in test fixture with monkeypatch), use custom base
    if BASE_DIR != str(WORKSPACE_ROOT):
        clean_name = os.path.basename(filename)
        candidate = os.path.realpath(os.path.join(BASE_DIR, clean_name))
        if not candidate.startswith(os.path.realpath(BASE_DIR)):
            raise PermissionError("Access denied: outside workspace")
        if os.path.islink(candidate):
            raise PermissionError("Access denied: symlink detected")
        if is_path_permanently_protected(candidate):
            raise PermissionError("Access denied: protected privacy location")
        return candidate

    # 2. Standard workspace confinement & traversal check
    safe_path = validate_workspace_path(filename)
    return str(safe_path)
