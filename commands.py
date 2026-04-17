import os
import webbrowser
import urllib.parse
import yt_dlp
from reminder import set_reminder, send_telegram_to
from contacts import get_chat_id
import re
from news import get_news
from weather import get_weather
from time_date import get_time, get_date, get_day
from maps import get_distance, get_location
from memory.memory_manager import store_memory, retrieve_memory
from sandbox.file_manager import create_file, read_file, delete_file, list_files, open_file, restore_file, list_trash, empty_trash
from sandbox.file_manager import create_folder , delete_folder
from security.action_guard import is_dangerous
from security.permission_manager import require_confirmation
from security.path_validator import get_safe_path

def extract_filename(command: str):
    match = re.search(
        r"(?:create|make|read|delete|remove|open|show|restore|empty)\s+(?:file\s+)?([\w\.\-]+)",
        command.lower()
    )
    return match.group(1) if match else None

def open_website(command):
    sites = {
        "leetcode": "https://leetcode.com/u/animeshyadav/",
        "github": "https://github.com/thisisanimesh01",
        "linkedin": "https://www.linkedin.com/in/animesh-yadav-39460b276/",
        "instagram": "https://www.instagram.com/thisisanimesh.01/",
        "gmail": "https://mail.google.com",
        "outlook": "https://outlook.office.com/mail/",
        "whatsapp": "https://web.whatsapp.com",
        "chess": "https://www.chess.com/member/animeshyadav",
        "google": "https://google.com",
        "youtube": "https://youtube.com"
    }

    for site in sites:
        if site in command:
            webbrowser.open(sites[site])
            return f"Opening {site}"

    return None

def execute_command(command):
    if is_dangerous(command):
        return "Blocked: Dangerous command detected."

    command = command.lower()

    if "make folder" in command or "create folder" in command:
        match = re.search(r"(?:make|create)\s+folder\s+(.+)", command)
        if match:
            folder_name = match.group(1).strip()
            return create_folder(folder_name)
        else:
            return "Please specify folder name."

    filename = extract_filename(command)

    if any(word in command for word in ["open", "go to", "launch"]):
        web_result = open_website(command)
        if web_result:
            return web_result

    if command.startswith("create") or command.startswith("make"):
        try:
            path = get_safe_path(filename)
            if os.path.exists(path):
                return f"File '{filename}' already exists."
        except:
            return "Invalid file name."
        return create_file(filename, "Hello from Friday v2")

    elif command.startswith("delete") or command.startswith("remove"):
        if not filename:
            return "Please specify a file or folder name."

        path = os.path.join(os.path.expanduser("~/Desktop/friday_workspace"), filename)

        if not os.path.exists(path):
            return f"'{filename}' does not exist."

        if os.path.isdir(path):
            return require_confirmation(f"delete the folder '{filename}'")
        else:
            return require_confirmation(f"delete the file '{filename}'")

    elif command.startswith("open"):
        if not filename:
            return "Please specify a file name."
        return open_file(filename)

    elif command.startswith("read") or command.startswith("show"):
        if not filename:
            return "Please specify a file name."
        return read_file(filename)

    elif command.startswith("delete") or command.startswith("remove"):
        if not filename:
            return "Please specify a file name."
        try:
            path = get_safe_path(filename)
        except:
            return "Invalid file path."
        if not os.path.exists(path):
            return f"File '{filename}' does not exist."
        return require_confirmation(f"delete the file '{filename}'")

    elif "restore" in command:
        if not filename:
            return "Please specify a file name."
        return restore_file(filename)

    elif "list trash" in command or "show trash" in command:
        return list_trash()

    elif "empty trash" in command:
        return require_confirmation("empty the trash")

    elif "list files" in command or "show files" in command:
        return list_files()

    if "remind me" in command:
        match = re.search(r"(\d{1,2}:\d{2})", command)
        if match:
            time_input = match.group(1)
            message = command.replace(match.group(1), "").replace("remind me", "").strip()
            set_reminder(time_input, message)
            return f"Got it. I’ll remind you at {time_input}."
        return "Tell me the time like 18:30."

    if "send" in command and "to" in command:
        try:
            msg_match = re.search(r'"(.*?)"', command)
            name = command.split("to")[-1].strip()

            if msg_match:
                message = msg_match.group(1)
                chat_id = get_chat_id(name)

                if chat_id:
                    send_telegram_to(chat_id, message)
                    return f"Message going to {name}"
                else:
                    return f"I don’t know {name} yet."
            else:
                return "Put message in quotes."
        except:
            return "Couldn't send message."

    if command in ["open code", "launch code", "open vs code", "launch vs code"]:
        try:
            os.system("code .")
            return "Launching VS Code..."
        except:
            return "Couldn't launch VS Code."

    if "youtube" in command:
        query = command.replace("youtube", "").replace("play", "").strip()

        if query:
            try:
                ydl_opts = {"quiet": True, "extract_flat": True}

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch:{query}", download=False)

                    if "entries" in info and len(info["entries"]) > 0:
                        video = info["entries"][0]
                        url = f"https://www.youtube.com/watch?v={video['id']}"
                        webbrowser.open(url)
                        return f"Playing {query} on YouTube..."
                    else:
                        raise Exception()

            except:
                search_query = urllib.parse.quote(query)
                url = f"https://www.youtube.com/results?search_query={search_query}"
                webbrowser.open(url)
                return "Error playing video, showing results instead."
        else:
            webbrowser.open("https://youtube.com")
            return "Opening YouTube..."

    if command in ["what time is it", "current time", "time"]:
        return get_time()
    elif "date" in command:
        return get_date()
    elif command.strip() == "day":
        return get_day()

    if any(word in command for word in ["news", "headlines"]):
        query = command.replace("news", "").strip()
        if not query:
            query = "latest"
        news = get_news(query)
        return f"Here’s what’s happening right now\n{news}"

    elif "where am i" in command or "my location" in command:
        return get_location()

    elif "distance" in command:
        return get_distance(command)

    elif "weather" in command or "temperature" in command:
        return get_weather(command)

    elif "google" in command:
        webbrowser.open("https://google.com")
        return "Opening Google..."

    elif command.strip() in ["bye","see you",  "goodbye", "exit", "quit"]:
        return "exit"

    else:
        return None