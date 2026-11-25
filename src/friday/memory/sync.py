import requests
from logger import get_logger
from memory.local import get_unsynced, mark_synced
from memory.supabase import save_cloud
from runtime_mode import is_offline_mode

logger = get_logger("MemorySync")

def is_online():
    if is_offline_mode():
        return False
    try:
        requests.get("https://www.google.com", timeout=2)
        return True
    except requests.RequestException:
        return False

def sync():
    if not is_online():
        return
    rows = get_unsynced()
    for row in rows:
        try:
            save_cloud(row[1], row[2], row[3])
            mark_synced(row[0])
        except Exception as e:
            logger.warning(f"Failed to sync memory row {row[0]}: {e}")