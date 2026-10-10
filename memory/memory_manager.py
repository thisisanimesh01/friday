"""
memory_manager.py — Persistent memory, conversation history, and rolling summarization.

Storage layout:
  memory.db          — SQLite: all conversation turns + embeddings
  personality.json   — JSON: rolling summary, tone, user prefs (in PROJECT_ROOT)

Both paths are resolved relative to this file's directory (project root),
so they work correctly regardless of the caller's CWD.
"""

import os
import json
import threading
import requests
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

from memory.local import init_db, save_local, get_all
from memory.embedder import embed
from memory.sync import is_online, sync
from memory.supabase import save_cloud
from logger import get_logger

load_dotenv()
logger = get_logger("MemoryManager")

# ── Paths anchored to project root ────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PERSONALITY_FILE = PROJECT_ROOT / "personality.json"

# ── Init DB ───────────────────────────────────────────────────────────────────
init_db()

# ── In-memory embedding cache ─────────────────────────────────────────────────
memory_store = []

rows = get_all()
for row in rows:
    try:
        text = row[1]
        emb = np.array(json.loads(row[3])) if row[3] else np.zeros(1)
        memory_store.append((text, emb))
    except Exception:
        continue

logger.info(f"Loaded {len(memory_store)} memory entries from DB.")

# ── Default personality ───────────────────────────────────────────────────────
DEFAULT_PERSONALITY = {
    "tone": "chill",
    "user_name": "Boss",
    "mood": "neutral",
    "history": [],          # last N user messages (used to trigger summarization)
    "full_history": [],     # full (user, bot) pairs for rich context
    "summary": "",          # rolling conversation summary
}

# ── Track which rows have been summarized to avoid re-summarizing ─────────────
_last_summarized_count = 0
_summarization_lock = threading.Lock()

GEMINI_API_KEY = os.getenv("GEMINI_API")
GROQ_API_KEY = os.getenv("GROQ_API")
try:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except Exception:
    client = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def cosine_sim(a, b):
    a = np.array(a)
    b = np.array(b)
    if a.shape != b.shape or np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# ── Personality file (project-relative) ───────────────────────────────────────

def load_personality() -> dict:
    if not PERSONALITY_FILE.exists():
        logger.info(f"personality.json not found at {PERSONALITY_FILE}, using defaults.")
        return dict(DEFAULT_PERSONALITY)
    try:
        with open(PERSONALITY_FILE, "r") as f:
            data = json.load(f)
        # Ensure all expected keys exist
        for k, v in DEFAULT_PERSONALITY.items():
            data.setdefault(k, v)
        logger.debug(f"Loaded personality from {PERSONALITY_FILE}")
        return data
    except Exception as e:
        logger.error(f"Failed to load personality.json: {e}")
        return dict(DEFAULT_PERSONALITY)


def save_personality(data: dict):
    try:
        with open(PERSONALITY_FILE, "w") as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved personality to {PERSONALITY_FILE}")
    except Exception as e:
        logger.error(f"Failed to save personality.json: {e}")


# ── Core memory operations ─────────────────────────────────────────────────────

def store_memory(user: str, bot):
    """Persist one conversation turn to SQLite + in-memory cache."""
    if isinstance(bot, dict):
        bot_text = bot.get("message", str(bot))
    else:
        bot_text = str(bot)

    embedding = embed(user)
    try:
        emb_arr = np.array(embedding)
    except Exception:
        emb_arr = np.zeros(1)

    memory_store.append((user, emb_arr))
    save_local(user, bot_text, emb_arr.tolist())

    if is_online():
        try:
            save_cloud(user, bot_text, emb_arr.tolist())
        except Exception:
            pass

    sync()

    # Also update full_history in personality for context building
    try:
        data = load_personality()
        fh = data.get("full_history", [])
        fh.append({"user": user, "bot": bot_text})
        # Keep rolling window of last 30 pairs
        data["full_history"] = fh[-30:]
        # Track simple user-message list for summarization trigger
        h = data.get("history", [])
        h.append(user)
        data["history"] = h[-20:]
        save_personality(data)
    except Exception as e:
        logger.error(f"Failed to update personality history: {e}")


def search_memory(query: str) -> list:
    """Return top-5 most semantically similar stored user messages."""
    query_embedding = embed(query)
    try:
        query_embedding = np.array(query_embedding)
    except Exception:
        return []

    scored = []
    for text, emb in memory_store:
        try:
            score = cosine_sim(query_embedding, emb)
        except Exception:
            score = 0.0
        scored.append((score, text))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [t for _, t in scored[:5]]


def retrieve_memory(query: str) -> list:
    """Return top-10 most relevant (user, bot) pairs from SQLite, ranked by embedding similarity."""
    rows = get_all()
    if not rows:
        return []

    query_embedding = embed(query)
    try:
        query_embedding = np.array(query_embedding)
    except Exception:
        return [(None, r[1], r[2]) for r in rows[-10:]]

    scored = []
    for row in rows:
        try:
            emb = np.array(json.loads(row[3])) if row[3] else np.zeros(1)
            score = cosine_sim(query_embedding, emb)
        except Exception:
            score = 0.0
        scored.append((score, row))

    scored.sort(reverse=True, key=lambda x: x[0])
    top_rows = [r[1] for r in scored[:10]]
    return [(None, row[1], row[2]) for row in top_rows]


def get_rich_context(query: str, n_recent: int = 6, n_semantic: int = 5) -> str:
    """
    Build a rich context string by combining:
      1. Rolling summary
      2. Recent full conversation pairs
      3. Semantically relevant older turns
    """
    data = load_personality()
    parts = []

    summary = data.get("summary", "").strip()
    if summary:
        parts.append(f"[Conversation Summary]\n{summary}")

    full_history = data.get("full_history", [])
    recent = full_history[-n_recent:]
    if recent:
        recent_text = "\n".join(
            f"User: {p['user']}\nFriday: {p['bot']}" for p in recent
        )
        parts.append(f"[Recent Conversation]\n{recent_text}")

    # Semantic search from SQLite for older relevant turns
    rows = get_all()
    if rows and len(rows) > n_recent:
        older_rows = rows[: max(0, len(rows) - n_recent)]
        q_emb = embed(query)
        try:
            q_emb = np.array(q_emb)
        except Exception:
            q_emb = None

        if q_emb is not None:
            scored = []
            for row in older_rows:
                try:
                    emb = np.array(json.loads(row[3])) if row[3] else np.zeros(1)
                    score = cosine_sim(q_emb, emb)
                except Exception:
                    score = 0.0
                scored.append((score, row))
            scored.sort(reverse=True, key=lambda x: x[0])
            top = [r[1] for r in scored[:n_semantic] if r[0] > 0.3]
            if top:
                sem_text = "\n".join(f"User: {r[1]}\nFriday: {r[2]}" for r in top)
                parts.append(f"[Relevant Past Memories]\n{sem_text}")

    return "\n\n".join(parts)


# ── Summarization ──────────────────────────────────────────────────────────────

def summarize_conversation_worker(history_pairs: list):
    """
    Background worker: summarize full_history pairs via Gemini and persist.
    Only summarizes new pairs since the last summary.
    """
    global _last_summarized_count

    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API not set; will attempt providers if available, otherwise use local fallback.")

    if not history_pairs:
        return

    logger.info(f"Summarization triggered for {len(history_pairs)} conversation pairs.")

    history_text = "\n".join(
        f"User: {p['user']}\nFriday: {p['bot']}" for p in history_pairs
    )

    system_prompt = (
        "You are a memory assistant. Summarize the following conversation history "
        "into a compact paragraph (3-5 sentences). Capture: key facts the user shared, "
        "ongoing tasks or projects, preferences, and any important context. "
        "Be concise and factual. Do not invent information."
    )

    # Try Gemini first, then Groq, then skip but log diagnostics.
    providers = []
    if GEMINI_API_KEY:
        providers.append(("Gemini", f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"))
    if GROQ_API_KEY:
        providers.append(("Groq", "groq_client"))

    summary = None
    res_json = None

    for provider, endpoint in providers:
        try:
            logger.info(f"Summarization attempt with provider: {provider}")
            if provider == "Gemini":
                payload = {"contents": [{"parts": [{"text": system_prompt + "\n\n" + history_text}]}]}
                try:
                    resp = requests.post(endpoint, json=payload, timeout=10)
                except Exception as e:
                    logger.error(f"{provider} request failed: {e}")
                    continue

                # Validate HTTP response code if present
                status = getattr(resp, 'status_code', None)
                if status and status != 200:
                    logger.error(f"{provider} summarization HTTP error: status={status}")
                    try:
                        res_json = resp.json()
                        logger.debug(f"{provider} response keys: {list(res_json.keys()) if isinstance(res_json, dict) else 'non-dict'}")
                    except Exception:
                        pass
                    continue

                try:
                    res_json = resp.json()
                except Exception:
                    logger.error(f"{provider} summarization: invalid JSON or empty response")
                    continue

                def _valid_summary_text(text: str) -> bool:
                    if not text or not isinstance(text, str):
                        return False
                    t = text.strip()
                    if len(t) < 20:
                        return False
                    low = t.lower()
                    bad_indicators = [
                        "error", "not found", "no longer available", "404", "429",
                        "deprecated", "unauthorized", "forbidden", "quota", "rate limit",
                        "invalid model", "not allowed", "exception"
                    ]
                    if any(b in low for b in bad_indicators):
                        return False
                    return True

                # Try structured candidate path
                try:
                    candidates = res_json.get("candidates", [])
                    if candidates and isinstance(candidates, list):
                        txt = candidates[0].get("content", {}).get("parts", [])[0].get("text", "").strip()
                        if _valid_summary_text(txt):
                            summary = txt
                            logger.info(f"Summarization succeeded with {provider}")
                            break
                        else:
                            logger.error("Gemini candidate rejected as invalid/diagnostic text")

                    # Fallback: search for any textual payload and validate it
                    def find_text(obj):
                        if isinstance(obj, str):
                            return obj
                        if isinstance(obj, dict):
                            for v in obj.values():
                                t = find_text(v)
                                if t:
                                    return t
                        if isinstance(obj, list):
                            for item in obj:
                                t = find_text(item)
                                if t:
                                    return t
                        return None

                    s = find_text(res_json)
                    if s and _valid_summary_text(s):
                        summary = s.strip()
                        logger.info(f"Summarization (alternate path) succeeded with {provider}")
                        break
                    else:
                        logger.error("Gemini alternate path returned invalid or diagnostic text; rejecting")
                except Exception as e:
                    logger.error(f"Gemini parsing error: {e}")
                    continue

            elif provider == "Groq" and client:
                try:
                    response = client.chat.completions.create(
                        model="qwen/qwen3.8-27b",
                        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": history_text}]
                    )
                    text = response.choices[0].message.content
                    if isinstance(text, str) and len(text.strip()) >= 20:
                        low = text.lower()
                        bad_indicators = [
                            "error", "not found", "no longer available", "404", "429",
                            "deprecated", "unauthorized", "forbidden", "quota", "rate limit",
                            "invalid model", "not allowed", "exception"
                        ]
                        if any(b in low for b in bad_indicators):
                            logger.error("Groq returned diagnostic-looking text; rejecting.")
                        else:
                            summary = text.strip()
                            logger.info("Summarization succeeded with Groq")
                            break
                    else:
                        logger.error("Groq returned short or invalid summary; rejecting.")
                except Exception as e:
                    logger.error(f"Groq summarization failed: {e}")
                    continue
        except Exception as e:
            logger.error(f"Summarization provider {provider} call failed: {e}")
            continue

    if not summary:
        # Log sanitized diagnostics
        try:
            diag = {"provider_attempts": [p for p, _ in providers]}
            if res_json and isinstance(res_json, dict):
                diag["response_keys"] = list(res_json.keys())
        except Exception:
            diag = {"provider_attempts": [p for p, _ in providers]}
        logger.error(f"Summarization failed after providers. Diagnostics: {diag}")
        # Fallback: produce a simple local summary based on recent history_pairs
        try:
            logger.info("Attempting local summarization fallback")
            # Extract distinct recent user messages
            users = [p.get("user", "") for p in history_pairs if p.get("user")]
            # Deduplicate while preserving order
            seen = set()
            uniq = []
            for u in users:
                if u not in seen:
                    uniq.append(u)
                    seen.add(u)
            if not uniq:
                logger.error("Local summarization had no content to summarize")
                return
            # Choose up to first 6 unique user messages to build a compact summary
            candidate = "; ".join(uniq[:6])
            # Truncate to reasonable length
            summary = (candidate[:400] + "...") if len(candidate) > 400 else candidate
            # Prepend a marker to indicate this is a local fallback
            summary = f"(local summary) {summary}"
            logger.info("Local summarization produced a fallback summary")
        except Exception as e:
            logger.error(f"Local summarization failed: {e}")
            return

    # Persist the summary
    with _summarization_lock:
        data = load_personality()
        data["summary"] = summary
        data["full_history"] = data.get("full_history", [])[-6:]
        _last_summarized_count = len(data.get("history", []))
        save_personality(data)

    logger.info(f"Summarization persisted. Summary: {summary[:80]}...")


def trigger_summarization():
    """Trigger background summarization if enough new conversation has accumulated."""
    global _last_summarized_count

    data = load_personality()
    full_history = data.get("full_history", [])
    current_count = len(full_history)

    # Trigger when we have at least 6 pairs AND at least 4 new pairs since last summarization
    if current_count >= 6 and (current_count - _last_summarized_count) >= 4:
        logger.info(
            f"Triggering summarization: {current_count} pairs total, "
            f"{current_count - _last_summarized_count} new since last summary."
        )
        pairs_to_summarize = full_history
        t = threading.Thread(
            target=summarize_conversation_worker,
            args=(pairs_to_summarize,),
            daemon=True,
        )
        t.start()
    else:
        logger.debug(
            f"Summarization not triggered: {current_count} pairs, "
            f"{current_count - _last_summarized_count} new."
        )


def get_current_summary() -> str:
    """Load and return the current rolling summary."""
    data = load_personality()
    summary = data.get("summary", "")
    if summary:
        logger.debug(f"Loaded summary ({len(summary)} chars).")
    return summary


# ── Legacy helpers (kept for backward compatibility with brain.py) ─────────────

def update_context(user_input: str) -> dict:
    data = load_personality()
    if "history" not in data:
        data["history"] = []
    data["history"].append(user_input)
    if len(data["history"]) > 20:
        data["history"] = data["history"][-20:]
    save_personality(data)
    return data
