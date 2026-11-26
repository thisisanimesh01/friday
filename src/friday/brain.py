import json
import os
from collections.abc import Generator
import requests
from dotenv import load_dotenv
from groq import Groq
from commands import execute_command
from intent_parser import detect_intent, extract_filename
from memory.local import get_all
from memory.intelligence import parse_memory_command, sanitize_memory_text
from memory.memory_manager import (
    forget_memory,
    get_user_preferences,
    load_personality,
    retrieve_memory,
    save_personality,
    search_memory,
    store_memory,
    update_context,
)
from personality import build_personality_system_prompt
from plugin_loader import handle_plugin, load_plugins


load_plugins()
load_dotenv()

from logger import get_logger
from runtime_mode import cloud_fallback_allowed, is_offline_mode
logger = get_logger("Brain")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "20"))
OLLAMA_STRICT_OFFLINE = os.getenv("OLLAMA_STRICT_OFFLINE", "false").lower() in ("1", "true", "yes")
OLLAMA_STREAM = os.getenv("OLLAMA_STREAM", "true").lower() in ("1", "true", "yes")
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "2048"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "5m")
GROQ_API_KEY = os.getenv("GROQ_API")
GEMINI_API_KEY = os.getenv("GEMINI_API")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def handle_input(user_input):
    context = update_context(user_input)

    # 0. Check for natural-language memory privacy / forget commands
    cmd_type, target = parse_memory_command(user_input)
    if cmd_type and cmd_type.startswith("forget"):
        _success, msg = forget_memory(cmd_type, target)
        return msg

    if cmd_type == "remember" and target:
        resp = f"I will remember that {target}."
        store_memory(target, resp)
        return resp

    cleaned = user_input.lower().strip()

    if cleaned in ["what is my name", "who am i", "do you know my name"]:
        prefs = get_user_preferences()
        if "name" in prefs:
            return f"Your name is {prefs['name']}."
        rows = get_all()
        names = []

        for row in rows:
            text = row[1]
            words_local = text.replace(",", " ").split()

            for w in words_local:
                clean = w.replace("-", "").replace("_", "")
                if clean.isalpha() and len(clean) > 2 and clean.lower() not in {"and", "are", "building", "favorite", "friday", "language", "local", "name", "offline", "primary", "programming", "project", "software", "with"}:
                    names.append(w.capitalize())

        if names:
            return f"Your name is {names[0]}."

    if cleaned in ["friday", "hey friday", "hi friday"]:
        response = "I'm here. How can I help you today?"
        store_memory(user_input, response)
        return response

    if cleaned in ["what did i say", "recall", "remember", "what did i tell you"]:
        results = retrieve_memory(cleaned)

        if results:
            response = "You said:\n"
            for r in results:
                response += f"- {r[1]}\n"
        else:
            response = "I don’t remember anything yet."

        store_memory(user_input, response)
        return response

    plugin_response = handle_plugin(user_input)
    if plugin_response:
        store_memory(user_input, plugin_response)
        return plugin_response

    intent = detect_intent(user_input)

    if intent == "create_file":
        filename = extract_filename(user_input)
        response = execute_command(f"create {filename}")
        store_memory(user_input, response)
        return response

    command_response = None

    parts = cleaned.split()
    first_word = parts[0] if parts else ""

    if first_word in ["create", "make", "open", "read", "delete", "remove", "list", "restore", "empty"]:
        command_response = execute_command(user_input)

    if command_response:
        store_memory(user_input, command_response)
        return command_response

    # Context integration:
    # 1. Check for relevant user preferences from persistent storage
    user_prefs = get_user_preferences()
    pref_context = ""
    if user_prefs:
        pref_lines = [f"- {sanitize_memory_text(k)}: {sanitize_memory_text(v)}" for k, v in user_prefs.items()]
        pref_context = "\n[User Preferences & Profile]:\n" + "\n".join(pref_lines)

    # 2. Check for relevant semantic memories from persistent storage
    relevant_memories = retrieve_memory(user_input, limit=3, min_similarity=0.35)
    context_hint = ""
    if relevant_memories:
        context_hint = "\n[Relevant Past Context]:\n" + "\n".join(
            f"- When you asked '{sanitize_memory_text(m[1])}', Friday answered: '{sanitize_memory_text(m[2])}'"
            for m in relevant_memories
        )

    # 3. Extract recent conversation turns from session personality
    p_data = load_personality()
    full_history = p_data.get("full_history", [])
    recent_history = full_history[-4:] if full_history else []
    recent_context = ""
    if recent_history:
        recent_context = "\n[Recent Conversation]:\n" + "\n".join(
            f"User: {sanitize_memory_text(p['user'])}\nFriday: {sanitize_memory_text(p['bot'])}"
            for p in recent_history
        )

    enhanced_prompt = (
        f"{pref_context}\n{recent_context}\n{context_hint}\n\nUser: {user_input}\nFriday:".strip()
    )

    response = ask_friday(enhanced_prompt)

    store_memory(user_input, response)
    return response

def sanitize_prompt(prompt):
    secrets = [
        os.getenv("GROQ_API"),
        os.getenv("GEMINI_API"),
        os.getenv("DEEPSEEK_API")
    ]

    for s in secrets:
        if s:
            prompt = prompt.replace(s, "[REDACTED]")

    return prompt

def build_context(user_input):
    data = load_personality()

    data["history"].append(user_input)
    if len(data["history"]) > 5:
        data["history"].pop(0)

    save_personality(data)

    return data

def generate_response(user_input):
    context = build_context(user_input)

    tone = context.get("tone", "chill")

    if tone == "chill":
        return f"Chill bro, I got you. You said: {user_input}"
    else:
        return f"Processing request: {user_input}"

def ask_friday_stream(prompt: str) -> Generator[str, None, None]:
    """Stream response tokens progressively. Yields string chunks.

    Handles KeyboardInterrupt / cancellation cleanly without losing state.
    """
    prompt = sanitize_prompt(prompt)
    system_prompt = build_personality_system_prompt()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    def _stream_ollama() -> Generator[str, None, None]:
        url = f"{OLLAMA_BASE_URL}/api/chat"
        data = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": True,
            "options": {
                "num_ctx": OLLAMA_NUM_CTX,
            },
            "keep_alive": OLLAMA_KEEP_ALIVE,
        }
        res = requests.post(url, json=data, timeout=OLLAMA_TIMEOUT, stream=True)
        res.raise_for_status()
        for line in res.iter_lines():
            if not line:
                continue
            chunk = json.loads(line.decode("utf-8"))
            msg = chunk.get("message", {})
            content = msg.get("content", "")
            if content:
                yield content
            if chunk.get("done", False):
                break

    if LLM_PROVIDER in ("ollama", "auto"):
        try:
            yield from _stream_ollama()
            return
        except Exception as e:
            logger.error(f"Ollama stream failed: {e}")
            if is_offline_mode() or OLLAMA_STRICT_OFFLINE or not cloud_fallback_allowed():
                past = retrieve_memory(prompt)
                if past:
                    yield f"I'm offline, but from what I remember: {past[0][2]}"
                else:
                    yield "I'm offline and don't have enough memory yet."
                return

    # Fallback to non-streaming ask_friday if streaming not applicable or failed
    yield ask_friday(prompt)


def ask_friday(prompt):
    prompt = sanitize_prompt(prompt)
    system_prompt = build_personality_system_prompt()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    def _try_ollama():
        url = f"{OLLAMA_BASE_URL}/api/chat"
        data = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        }
        res = requests.post(url, json=data, timeout=OLLAMA_TIMEOUT)
        res.raise_for_status()
        payload = res.json()
        content = payload["message"]["content"]
        if "</think>" in content:
            content = content.split("</think>")[-1].strip()
        return content

    if LLM_PROVIDER in ("ollama", "auto"):
        try:
            return _try_ollama()
        except Exception as e:
            logger.error(f"Ollama failed: {e}")
            if is_offline_mode() or OLLAMA_STRICT_OFFLINE or not cloud_fallback_allowed():
                past = retrieve_memory(prompt)
                if past:
                    best = past[0]
                    return f"I'm offline, but from what I remember: {best[2]}"
                return "I'm offline and don't have enough memory yet."

    if is_offline_mode() or not cloud_fallback_allowed():
        past = retrieve_memory(prompt)
        if past:
            best = past[0]
            return f"I'm offline, but from what I remember: {best[2]}"
        return "I'm offline and don't have enough memory yet."

    if client:
        try:
            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=messages
            )
            content = response.choices[0].message.content
            if "</think>" in content:
                content = content.split("</think>")[-1].strip()
            return content
        except Exception as e:
            logger.error(f"Groq API failed: {e}")

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"

        data = {
            "contents": [{
                "parts": [{"text": system_prompt + "\nUser: " + prompt}]
            }]
        }

        res = requests.post(url, json=data, timeout=10).json()
        return res["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini API failed: {e}")

    try:
        url = "https://api.deepseek.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": messages
        }

        res = requests.post(url, headers=headers, json=data, timeout=10).json()
        return res["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"DeepSeek API failed: {e}")

    past = retrieve_memory(prompt)

    if past:
        # Return the most relevant stored bot response rather than mangling words
        best = past[0]  # already ranked by embedding similarity
        return f"I'm offline, but from what I remember: {best[2]}"

    return "I'm offline and don't have enough memory yet."