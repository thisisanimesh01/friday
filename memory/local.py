import sqlite3
import threading

db_lock = threading.Lock()      #to ensure thread safety when accessing the database

DB = "memory.db"   # DB to store conversations locally before syncing with cloud

def init_db():
    import sqlite3
    import os

    try:
        conn = sqlite3.connect(DB, check_same_thread=False)
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            bot TEXT,
            embedding TEXT,
            synced INTEGER
        )
        """)

        conn.commit()
        conn.close()

    except sqlite3.DatabaseError:
        os.remove(DB)
        init_db()

def save_local(user, bot, embedding):
    import json
    import sqlite3
    import threading

    if not hasattr(save_local, "lock"):
        save_local.lock = threading.Lock()

    with save_local.lock:
        conn = sqlite3.connect(DB, check_same_thread=False)
        c = conn.cursor()

        if isinstance(bot, dict):
            bot = json.dumps(bot)

        c.execute(
            "INSERT INTO conversations (user, bot, embedding, synced) VALUES (?, ?, ?, 0)",
            (user, str(bot), str(embedding))
        )

        conn.commit()
        conn.close()

def get_all():
    import json

    conn = sqlite3.connect(DB, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM conversations")
    rows = c.fetchall()
    conn.close()

    parsed_rows = []
    for row in rows:
        try:
            bot = json.loads(row[2])
        except:
            bot = row[2]

        parsed_rows.append((row[0], row[1], bot, row[3], row[4]))

    return parsed_rows

def get_unsynced():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM conversations WHERE synced = 0")
    rows = c.fetchall()
    conn.close()
    return rows

def mark_synced(row_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE conversations SET synced = 1 WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()