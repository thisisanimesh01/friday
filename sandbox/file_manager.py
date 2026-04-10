import os
from security.path_validator import BASE_DIR, get_safe_path
import subprocess

MAX_DELETE_LIMIT = 10

os.makedirs(BASE_DIR, exist_ok=True)

def create_file(name: str, content: str) -> str:
    path = get_safe_path(name)

    with open(path, "w") as f:
        f.write(content)

    return f"File '{name}' created successfully."


def read_file(name: str) -> str:
    if not name:
        return "No file specified."

    try:
        path = get_safe_path(name)
    except Exception:
        return "Invalid file path."

    if not os.path.exists(path):
        return f"File '{name}' does not exist."

    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def delete_file(name: str, confirm: bool = False) -> str:
    if not confirm:
        return "Confirmation required before deleting file."

    path = get_safe_path(name)

    if not os.path.exists(path):
        return "File not found."

    os.remove(path)
    return f"File '{name}' deleted successfully."


def list_files() -> list:
    try:
        files = os.listdir(BASE_DIR)
        return [f for f in files if not f.startswith(".")]
    except Exception:
        return []

def open_file(name: str) -> str:
    path = get_safe_path(name)

    if not os.path.exists(path):
        return "File not found."

    try:
        subprocess.run(["code", path])
        return f"Opening '{name}'..."
    except Exception as e:
        return f"Error opening file: {str(e)}"