from memory.local import init_db, save_local, get_all
from memory.embedder import embed
from memory.sync import is_online, sync
from memory.supabase import save_cloud

init_db()

def store_memory(user, bot):
    if isinstance(bot, dict):
        bot_text = bot.get("message", str(bot))
    else:
        bot_text = str(bot)

    text = user + " " + bot_text

    embedding = embed(text)
    save_local(user, bot_text, embedding)
    if is_online():
        try:
            save_cloud(user, bot, embedding)
        except:
            pass
    sync()

def retrieve_memory(query):
    query_embedding = embed(query)
    rows = get_all()
    results = []
    for row in rows:
        text = row[1] + " " + row[2]
        if any(word in text.lower() for word in query.lower().split()):
            results.append(row)
    return results[-5:]