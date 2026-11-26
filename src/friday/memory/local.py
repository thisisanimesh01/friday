import sqlite3
import threading
import os

db_lock = threading.Lock()      # ensure thread safety when accessing the database

# DB path anchored to project root (parent of memory/) — works regardless of CWD
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(_PROJECT_ROOT, "memory.db")

def init_db():
    try:
        conn = sqlite3.connect(DB, check_same_thread=False)
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            bot TEXT,
            embedding TEXT,
            synced INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Add created_at column if legacy database lacks it
        c.execute("PRAGMA table_info(conversations)")
        cols = [row[1] for row in c.fetchall()]
        if "created_at" not in cols:
            c.execute("ALTER TABLE conversations ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

        conn.commit()
        conn.close()

    except sqlite3.DatabaseError:
        os.remove(DB)
        init_db()


def save_local(user, bot, embedding):
    import json
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
        new_id = c.lastrowid
        conn.commit()
        conn.close()
        return new_id


def delete_memory_by_id(memory_id: int) -> bool:
    """Delete a memory record by its integer primary key ID."""
    conn = sqlite3.connect(DB, check_same_thread=False)
    c = conn.cursor()
    c.execute("DELETE FROM conversations WHERE id = ?", (memory_id,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def delete_memory_by_text(query: str) -> int:
    """Delete memories matching a specific substring in user or bot text."""
    conn = sqlite3.connect(DB, check_same_thread=False)
    c = conn.cursor()
    pattern = f"%{query}%"
    c.execute("DELETE FROM conversations WHERE user LIKE ? OR bot LIKE ?", (pattern, pattern))
    deleted_count = c.rowcount
    conn.commit()
    conn.close()
    return deleted_count


def clear_all_memory() -> int:
    """Clear all records from local memory database."""
    conn = sqlite3.connect(DB, check_same_thread=False)
    c = conn.cursor()
    c.execute("DELETE FROM conversations")
    deleted_count = c.rowcount
    conn.commit()
    conn.close()
    return deleted_count

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
        except (json.JSONDecodeError, TypeError):
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