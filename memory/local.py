import sqlite3

DB = "memory.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        bot TEXT,
        embedding TEXT,
        synced INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

def save_local(user, bot, embedding):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO conversations (user, bot, embedding, synced) VALUES (?, ?, ?, 0)",
        (user, bot, str(embedding))
    )
    conn.commit()
    conn.close()

def get_all():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM conversations")
    rows = c.fetchall()
    conn.close()
    return rows

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