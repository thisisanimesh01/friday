import os

BASE_DIR = "/Users/animeshyadav/Desktop/friday_workspace"

def get_safe_path(filename: str) -> str:
    # Remove any path traversal attempts
    filename = os.path.basename(filename)

    full_path = os.path.join(BASE_DIR, filename)
    real_path = os.path.realpath(full_path)

    # Ensure path stays inside workspace
    if not real_path.startswith(BASE_DIR):
        raise PermissionError("Access denied: outside workspace")

    # Block symbolic links
    if os.path.islink(real_path):
        raise PermissionError("Access denied: symlink detected")

    return real_path