import json

CONTACT_FILE = "contacts.json"
def get_chat_id(name):
    try:
        with open(CONTACT_FILE, "r") as f:
            data = json.load(f)
            return data.get(name.lower())
    except:
        return None



