import time
import requests
import threading
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=data, timeout=8)
    except Exception:
        pass

def set_reminder(reminder_time, message):
    def reminder_thread():
        while True:
            now = datetime.now().strftime("%H:%M")
            if now == reminder_time:
                send_telegram(f"Reminder: {message}")
                break
            time.sleep(30)

    threading.Thread(target=reminder_thread, daemon=True).start()

def send_telegram_to(chat_id, message):
    if not BOT_TOKEN:
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message
        }
        requests.post(url, data=data, timeout=8)
    except Exception:
        pass