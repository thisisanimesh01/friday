import re

def extract_filename(text):
    match = re.search(r'(\w+\.\w+)', text)
    return match.group(1) if match else "test.txt"

def detect_intent(text):
    text = text.lower()

    if any(x in text for x in ["create file", "make file", "new file"]):
        return "create_file"

    if any(x in text for x in ["delete file", "remove file"]):
        return "delete_file"

    if "weather" in text:
        return "weather"

    # Play commands for media
    if text.startswith("play ") and ("youtube" in text or "on youtube" in text):
        return "play_youtube"
    if text.startswith("play ") and ("spotify" in text or "on spotify" in text):
        return "play_spotify"

    return "chat"

