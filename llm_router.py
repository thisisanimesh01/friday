import os
import json
import requests
from dotenv import load_dotenv
from groq import Groq
from logger import get_logger
import re

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API")
GEMINI_API_KEY = os.getenv("GEMINI_API")
logger = get_logger("LLMRouter")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """You are an intent classifier for a personal AI assistant called Friday.
Given a user input, classify it into one of the available commands OR "chat" if it doesn't match any command.

IMPORTANT RULES:
- If the user asks about time, date, day, weather, news, location, distance — those ARE commands, NOT chat.
- If the user wants to create, delete, open, read, restore files/folders — those ARE commands.
- If the user wants to play something on youtube, open a website, send a message, set a reminder — those ARE commands.
- If the user types a raw shell/terminal command (e.g. "tail -f log", "ls -la", "ps aux", "ping google.com") — classify as "terminal_command".
- ONLY classify as "chat" if the input is truly conversational (greetings, opinions, questions about life, etc.)

Available commands and their JSON format:
- get_time() → {"intent": "get_time", "args": {}}
- get_date() → {"intent": "get_date", "args": {}}
- get_day() → {"intent": "get_day", "args": {}}
- get_weather(location) → {"intent": "get_weather", "args": {"location": "mumbai"}}
- get_news(query) → {"intent": "get_news", "args": {"query": "tech"}}
- get_location() → {"intent": "get_location", "args": {}}
- get_distance(from_loc, to_loc) → {"intent": "get_distance", "args": {"from_loc": "delhi", "to_loc": "mumbai"}}
- create_file(filename) → {"intent": "create_file", "args": {"filename": "hello.txt"}}
- create_folder(folder_name) → {"intent": "create_folder", "args": {"folder_name": "projects"}}
- delete_file(filename) → {"intent": "delete_file", "args": {"filename": "hello.txt"}}
- delete_folder(folder_name) → {"intent": "delete_folder", "args": {"folder_name": "projects"}}
- open_file(filename) → {"intent": "open_file", "args": {"filename": "hello.txt"}}
- read_file(filename) → {"intent": "read_file", "args": {"filename": "hello.txt"}}
- restore_file(filename) → {"intent": "restore_file", "args": {"filename": "hello.txt"}}
- list_trash() → {"intent": "list_trash", "args": {}}
- empty_trash() → {"intent": "empty_trash", "args": {}}
- list_files() → {"intent": "list_files", "args": {}}
- set_reminder(time, message) → {"intent": "set_reminder", "args": {"time": "18:30", "message": "meeting"}}
- send_telegram(name, message) → {"intent": "send_telegram", "args": {"name": "john", "message": "hello"}}
- open_code() → {"intent": "open_code", "args": {}}
- play_youtube(query) → {"intent": "play_youtube", "args": {"query": "lofi beats"}}
- open_website(website_name) → {"intent": "open_website", "args": {"website_name": "github"}}
- terminal_command (shell/system command the user typed literally) → {"intent": "terminal_command", "args": {"command": "tail -f friday.log"}}
- chat (for general conversation) → {"intent": "chat", "args": {}}

Respond with ONLY a valid JSON object, nothing else. No markdown, no explanation."""

def _clean_json_text(text: str) -> dict:
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())

def route_command(user_input):
    # First: explicit pattern checks (highest priority) to avoid LLM misclassification
    lower = user_input.lower()

    # Explicit media intent detection (highest priority)
    m_spotify = re.search(r"(?is)play\s+(.+?)\s+on\s+spotify", user_input)
    if m_spotify:
        query = m_spotify.group(1).strip()
        logger.info(f"Detected explicit Spotify play intent. Query: {query}")
        return {"intent": "play_spotify", "args": {"query": query}}

    m_youtube = re.search(r"(?is)play\s+(.+?)\s+on\s+youtube", user_input)
    if m_youtube:
        query = m_youtube.group(1).strip()
        logger.info(f"Detected explicit YouTube play intent. Query: {query}")
        return {"intent": "play_youtube", "args": {"query": query}}

    # Coursera explicit triggers (must go to Chrome)
    coursera_triggers = ["coursera", "my coursera", "coursera course", "coursera lecture", "continue coursera", "open coursera"]
    for t in coursera_triggers:
        if t in lower:
            logger.info(f"Browser request detected (deterministic fallback). Input: {user_input}")
            logger.info("Intent: browser_action | Target: Coursera | Browser selected: chrome")
            return {"intent": "open_website", "args": {"website_name": "coursera"}}

    # Known websites routing (Brave)
    known_sites = [
        "spotify", "youtube", "google", "github", "wikipedia",
        "leetcode", "linkedin", "instagram", "gmail", "outlook",
        "whatsapp", "chess", "portfolio"
    ]
    for s in known_sites:
        if re.search(rf"\b{s}\b", lower):
            logger.info(f"Browser request detected (deterministic fallback). Input: {user_input}")
            logger.info(f"Intent: browser_action | Target: {s.title()} | Browser selected: brave")
            return {"intent": "open_website", "args": {"website_name": s}}

    # URL or explicit search queries (excluding file operations)
    if lower.startswith("http://") or lower.startswith("https://"):
        return {"intent": "open_website", "args": {"website_name": lower}}

    if re.search(r"\b(search for|search|browse)\b", lower) and not any(kw in lower for kw in ["file", "files", "folder", "trash", "code"]):
        logger.info(f"Browser request detected (deterministic fallback). Input: {user_input}")
        logger.info("Intent: browser_action | Target: general web | Browser selected: brave")
        return {"intent": "open_website", "args": {"website_name": lower}}

    # Primary: Groq Qwen
    if client:
        try:
            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                response_format={"type": "json_object"}
            )
            text = response.choices[0].message.content
            result = _clean_json_text(text)
            logger.info(f"[Groq Router] '{user_input}' → intent={result.get('intent')}, args={result.get('args')}")
            return result
        except Exception as e:
            logger.warning(f"[Groq Router] failed for '{user_input}': {e}. Falling back to Gemini.")

    # Fallback: Gemini Flash
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\nUser input: " + user_input}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            res = requests.post(url, json=payload, timeout=8).json()
            text = res["candidates"][0]["content"]["parts"][0]["text"]
            result = _clean_json_text(text)
            logger.info(f"[Gemini Router] '{user_input}' → intent={result.get('intent')}, args={result.get('args')}")
            return result
        except Exception as e:
            logger.error(f"[Gemini Router] failed for '{user_input}': {e}")

    # Deterministic fallback: give explicit media targets higher priority
    lower = user_input.lower()

    # Explicit media intent detection (highest priority)
    m_spotify = re.search(r"(?is)play\s+(.+?)\s+on\s+spotify", user_input)
    if m_spotify:
        query = m_spotify.group(1).strip()
        logger.info(f"Detected explicit Spotify play intent. Query: {query}")
        return {"intent": "play_spotify", "args": {"query": query}}

    m_youtube = re.search(r"(?is)play\s+(.+?)\s+on\s+youtube", user_input)
    if m_youtube:
        query = m_youtube.group(1).strip()
        logger.info(f"Detected explicit YouTube play intent. Query: {query}")
        return {"intent": "play_youtube", "args": {"query": query}}

    # Coursera explicit triggers (must go to Chrome)
    coursera_triggers = ["coursera", "my coursera", "coursera course", "coursera lecture", "continue coursera", "open coursera"]
    for t in coursera_triggers:
        if t in lower:
            logger.info(f"Browser request detected (deterministic fallback). Input: {user_input}")
            logger.info("Intent: browser_action | Target: Coursera | Browser selected: chrome")
            return {"intent": "open_website", "args": {"website_name": "coursera"}}

    # Known websites routing (Brave)
    known_sites = [
        "spotify", "youtube", "google", "github", "wikipedia",
        "leetcode", "linkedin", "instagram", "gmail", "outlook",
        "whatsapp", "chess", "portfolio"
    ]
    for s in known_sites:
        if re.search(rf"\b{s}\b", lower):
            logger.info(f"Browser request detected (deterministic fallback). Input: {user_input}")
            logger.info(f"Intent: browser_action | Target: {s.title()} | Browser selected: brave")
            return {"intent": "open_website", "args": {"website_name": s}}

    if lower.startswith("http://") or lower.startswith("https://"):
        return {"intent": "open_website", "args": {"website_name": lower}}

    if re.search(r"\b(search for|search|browse)\b", lower) and not any(kw in lower for kw in ["file", "files", "folder", "trash", "code"]):
        logger.info(f"Browser request detected (deterministic fallback). Input: {user_input}")
        logger.info("Intent: browser_action | Target: general web | Browser selected: brave")
        return {"intent": "open_website", "args": {"website_name": lower}}

    # Time / Date / Day fallbacks
    if re.search(r"\b(time|what time|current time)\b", lower):
        return {"intent": "get_time", "args": {}}
    if re.search(r"\b(today'?s? date|what is the date|what date)\b", lower):
        return {"intent": "get_date", "args": {}}
    if re.search(r"\b(what day|which day|day today)\b", lower):
        return {"intent": "get_day", "args": {}}

    # Weather fallback
    if "weather" in lower or "temperature" in lower:
        return {"intent": "get_weather", "args": {"location": user_input}}

    # News fallback
    if re.search(r"\b(news|headlines)\b", lower):
        return {"intent": "get_news", "args": {"query": user_input}}

    # Files / Folders fallbacks
    from sandbox.file_manager import BASE_DIR
    m_create_file = re.search(r"(?:create|make)\s+(?:file\s+)?([\w\.\-]+)", lower)
    if m_create_file and ("file" in lower or "." in m_create_file.group(1)):
        return {"intent": "create_file", "args": {"filename": m_create_file.group(1)}}

    m_create_folder = re.search(r"(?:create|make)\s+folder\s+([\w\.\-]+)", lower)
    if m_create_folder:
        return {"intent": "create_folder", "args": {"folder_name": m_create_folder.group(1)}}

    m_delete_file = re.search(r"(?:delete|remove)\s+(?:file\s+)?([\w\.\-]+)", lower)
    if m_delete_file and ("file" in lower or "." in m_delete_file.group(1)):
        return {"intent": "delete_file", "args": {"filename": m_delete_file.group(1)}}

    m_delete_folder = re.search(r"(?:delete|remove)\s+folder\s+([\w\.\-]+)", lower)
    if m_delete_folder:
        return {"intent": "delete_folder", "args": {"folder_name": m_delete_folder.group(1)}}

    if "empty trash" in lower:
        return {"intent": "empty_trash", "args": {}}
    if "list trash" in lower or "show trash" in lower:
        return {"intent": "list_trash", "args": {}}
    if "list files" in lower or "show files" in lower:
        return {"intent": "list_files", "args": {}}

    return {"intent": "chat", "args": {}}
