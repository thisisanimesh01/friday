import os
import requests
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

# API KEYS
GROQ_API_KEY = os.getenv("GROQ_API")
GEMINI_API_KEY = os.getenv("GEMINI_API")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API")

client = Groq(api_key=GROQ_API_KEY)

def sanitize_prompt(prompt):
    import os

    secrets = [
        os.getenv("GROQ_API_KEY"),
        os.getenv("GEMINI_API_KEY"),
        os.getenv("DEEPSEEK_API_KEY")
    ]

    for s in secrets:
        if s:
            prompt = prompt.replace(s, "[REDACTED]")

    return prompt


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

    # GROQ (PRIMARY - FAST)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        return response.choices[0].message.content

    except Exception as e:
        print("Groq Error:", e)


    # GEMINI (FALLBACK)
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


    # DEEPSEEK (FINAL FALLBACK)
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


    return "⚠️ Boss, all AI services are down right now."