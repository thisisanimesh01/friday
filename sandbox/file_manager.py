import os
import shutil
from security.path_validator import BASE_DIR, get_safe_path
import subprocess

MAX_DELETE_LIMIT = 10

TRASH_DIR = os.path.join(BASE_DIR, "trash")

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(TRASH_DIR, exist_ok=True)

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

    if not name:
        return "No file specified."

    try:
        path = get_safe_path(name)
    except Exception:
        return "Invalid file path."

    if not os.path.exists(path):
        return f"File '{name}' does not exist."

    try:
        # move to trash instead of deleting
        trash_path = os.path.join(TRASH_DIR, name)

        counter = 1
        base, ext = os.path.splitext(name)
        while os.path.exists(trash_path):
            trash_path = os.path.join(TRASH_DIR, f"{base}_{counter}{ext}")
            counter += 1

        shutil.move(path, trash_path)

        return f"File '{name}' moved to trash."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def restore_file(name: str) -> str:
    if not name:
        return "No file specified."

    try:
        os.makedirs(TRASH_DIR, exist_ok=True)

        trash_path = os.path.join(TRASH_DIR, name)

        if not os.path.exists(trash_path):
            return f"File '{name}' not found in trash."

        restore_path = get_safe_path(name)

        counter = 1
        base, ext = os.path.splitext(name)
        while os.path.exists(restore_path):
            restore_path = get_safe_path(f"{base}_{counter}{ext}")
            counter += 1

        shutil.move(trash_path, restore_path)

        return f"File '{name}' restored successfully."

    except Exception as e:
        return f"Error restoring file: {str(e)}"

def list_trash() -> list:
    try:
        return [f for f in os.listdir(TRASH_DIR) if not f.startswith(".")]
    except:
        return []

def list_files() -> list:
    try:
        files = os.listdir(BASE_DIR)
        return [f for f in files if not f.startswith(".")]
    except Exception:
        return []

def empty_trash() -> str:
    import os
    import shutil

    try:
        os.makedirs(TRASH_DIR, exist_ok=True)

        items = os.listdir(TRASH_DIR)

        for item in items:
            item_path = os.path.join(TRASH_DIR, item)

            if os.path.isfile(item_path):
                os.remove(item_path)

            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

        return "Trash emptied successfully."

    except Exception as e:
        return f"Error clearing trash: {str(e)}"

def open_file(name: str) -> str:
    path = get_safe_path(name)

    if not os.path.exists(path):
        return "File not found."

    try:
        subprocess.run(["code", path])
        return f"Opening '{name}'..."
    except Exception as e:
        return f"Error opening file: {str(e)}"