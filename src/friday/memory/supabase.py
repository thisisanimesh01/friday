import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None

def save_cloud(user, bot, embedding):
    if not supabase:
        return
    supabase.table("conversations").insert({
        "user": user,
        "bot": bot,
        "embedding": embedding
    }).execute()