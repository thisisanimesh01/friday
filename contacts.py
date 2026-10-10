import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
CONTACT_FILE = os.path.join(_DIR, "contacts.json")
def get_chat_id(name):
    try:
        with open(CONTACT_FILE, "r") as f:
            data = json.load(f)
            return data.get(name.lower())
    except:
        return None



