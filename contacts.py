import json
import os
from logger import get_logger

logger = get_logger("Contacts")
_DIR = os.path.dirname(os.path.abspath(__file__))
CONTACT_FILE = os.path.join(_DIR, "contacts.json")
def get_chat_id(name):
    try:
        with open(CONTACT_FILE, "r") as f:
            data = json.load(f)
            return data.get(name.lower())
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to read contacts for '{name}': {e}")
        return None



