import requests
from memory.local import get_unsynced, mark_synced
from memory.supabase import save_cloud

def is_online():
    try:
        requests.get("https://www.google.com", timeout=2)
        return True
    except:
        return False

def sync():
    if not is_online():
        return
    rows = get_unsynced()
    for row in rows:
        try:
            save_cloud(row[1], row[2], row[3])
            mark_synced(row[0])
        except:
            pass