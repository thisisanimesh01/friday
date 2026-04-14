from memory.local import init_db, save_local, get_all
from memory.embedder import embed
from memory.sync import is_online, sync
from memory.supabase import save_cloud
import os
import json
import numpy as np

init_db()

memory_store = []

structured_memory = {}

rows = get_all()
for row in rows:
    try:
        text = row[1]
        emb = np.array(json.loads(row[3])) if row[3] else np.zeros(1)
        memory_store.append((text, emb))
    except:
        continue

MEMORY_FILE = "personality.json"

DEFAULT_PERSONALITY = {
    "tone": "chill",
    "user_name": "Boss",
    "mood": "neutral",
    "history": []
}


def cosine_sim(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def store_memory(user, bot):

    if isinstance(bot, dict):
        bot_text = bot.get("message", str(bot))
    else:
        bot_text = str(bot)

    text = user

    embedding = embed(text)

    try:
        embedding = np.array(embedding)
    except:
        embedding = np.zeros(1)

    memory_store.append((text, embedding))


    save_local(user, bot_text, embedding.tolist())

    if is_online():
        try:
            save_cloud(user, bot_text, embedding.tolist())
        except:
            pass

    sync()


def search_memory(query):
    query_embedding = embed(query)

    try:
        query_embedding = np.array(query_embedding)
    except:
        return []

    scored = []

    for text, emb in memory_store:
        try:
            score = cosine_sim(query_embedding, emb)
        except:
            score = 0

        scored.append((score, text))

    scored.sort(reverse=True, key=lambda x: x[0])

    top = [t for _, t in scored[:5]]

    return top


def retrieve_memory(query):
    rows = get_all()

    if not rows:
        return []

    query_embedding = embed(query)

    try:
        query_embedding = np.array(query_embedding)
    except:
        return rows[-10:]

    scored = []

    for row in rows:
        try:
            emb = np.array(json.loads(row[3])) if row[3] else np.zeros(1)
            score = cosine_sim(query_embedding, emb)
        except:
            score = 0

        scored.append((score, row))

    scored.sort(reverse=True, key=lambda x: x[0])

    top_rows = [r[1] for r in scored[:10]]

    clean_rows = []

    for row in top_rows:
        user_text = row[1]
        bot_text = row[2]
        clean_rows.append((None, user_text, bot_text))

    return clean_rows


def load_personality():
    if not os.path.exists(MEMORY_FILE):
        return DEFAULT_PERSONALITY

    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_PERSONALITY


def save_personality(data):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass


def update_context(user_input):
    data = load_personality()

    if "history" not in data:
        data["history"] = []

    data["history"].append(user_input)

    if len(data["history"]) > 5:
        data["history"].pop(0)

    save_personality(data)

    return data