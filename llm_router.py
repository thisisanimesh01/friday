import os
import json
import requests
from dotenv import load_dotenv
from groq import Groq
from logger import get_logger

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

    return {"intent": "chat", "args": {}}
