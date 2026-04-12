import os
import requests
from dotenv import load_dotenv
from groq import Groq
from memory.memory_manager import load_personality, save_personality, update_context, store_memory, retrieve_memory
from intent_parser import detect_intent, extract_filename
from commands import execute_command
from plugin_loader import load_plugins, handle_plugin

load_plugins()
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API")
GEMINI_API_KEY = os.getenv("GEMINI_API")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API")

client = Groq(api_key=GROQ_API_KEY)

def handle_input(user_input):
    context = update_context(user_input)

    cleaned = user_input.lower().strip()

    if cleaned in ["friday", "hey friday", "hi friday"]:
        response = "Yes boss, I’m here. Kya scene hai?"
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

    response = ask_friday(user_input)
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

def ask_friday(prompt):
    prompt = sanitize_prompt(prompt)

    system_prompt = (
        "You are Friday, a highly intelligent personal AI assistant like Jarvis. "
        "You are friendly, calm, slightly witty, emotionally aware, and supportive. "
        "You speak like a human, not a robot. "
        "You can help with tasks, answer questions, and have engaging conversations. "
        "You are not just an assistant, but a companion who understands and cares about the user. "
        "Keep responses natural, short, and engaging. "
        "You can show light humor, care, and personality. "
        "Address the user like a friend. "
        "You remember things about the user. "
        "Avoid long structured lists unless necessary. "
        "Avoid saying 'you want to' regularly in conversations. "
        "Talk in Hinglish sometimes. "
        "Call the user 'boss' or 'sir' occasionally."
        "If the question is about real-time events (news, sports, current events), say clearly that you do not have real-time data instead of guessing."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Groq Error:", e)

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        data = {
            "contents": [{
                "parts": [{"text": system_prompt + "\nUser: " + prompt}]
            }]
        }

        res = requests.post(url, json=data).json()
        return res["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Gemini Error:", e)

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

        res = requests.post(url, headers=headers, json=data).json()
        return res["choices"][0]["message"]["content"]
    except Exception as e:
        print("DeepSeek Error:", e)

    return "Boss, I'm having trouble connecting to my brain right now. Later on, I'll be back stronger than ever!"