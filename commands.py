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
from llm_router import route_command

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
        "chess": "https://www.chess.com/home",
        "google": "https://google.com",
        "youtube": "https://youtube.com",
        "portfolio": "https://thisisanimesh01.github.io/Portfolio/",
    }

    for site in sites:
        if site in command:
            webbrowser.open(sites[site])
            return f"Opening {site}..."

    return None

def execute_command(command):
    if is_dangerous(command):
        return "Blocked: Dangerous command detected."

    command_lower = command.lower()
    routed = route_command(command)
    intent = routed.get("intent", "chat")
    args = routed.get("args", {})

    if intent == "create_folder":
        folder_name = args.get("folder_name")
        if folder_name:
            return create_folder(folder_name)
        return "Please specify folder name."

    elif intent == "create_file":
        filename = args.get("filename")
        if not filename: return "Invalid file name."
        try:
            path = get_safe_path(filename)
            if os.path.exists(path):
                return f"File '{filename}' already exists."
        except:
            return "Invalid file name."
        return create_file(filename, "Hello sir , its Friday v2")

    elif intent == "delete_file":
        filename = args.get("filename")
        if not filename:
            return "Please specify a file name."
        try:
            path = get_safe_path(filename)
        except:
            return "Invalid file path."
        if not os.path.exists(path):
            return f"File '{filename}' does not exist."
        return require_confirmation(f"delete the file '{filename}'", action_type="delete_file", target=filename)

    elif intent == "delete_folder":
        folder_name = args.get("folder_name")
        if not folder_name:
            return "Please specify a folder name."
        path = os.path.join(os.path.expanduser("~/Desktop/friday_workspace"), folder_name)
        if not os.path.exists(path):
            return f"'{folder_name}' does not exist."
        return require_confirmation(f"delete the folder '{folder_name}'", action_type="delete_folder", target=folder_name)

    elif intent == "open_file":
        filename = args.get("filename")
        if not filename:
            return "Please specify a file name."
        return open_file(filename)

    elif intent == "read_file":
        filename = args.get("filename")
        if not filename:
            return "Please specify a file name."
        return read_file(filename)

    elif intent == "restore_file":
        filename = args.get("filename")
        if not filename:
            return "Please specify a file name."
        return restore_file(filename)

    elif intent == "list_trash":
        return list_trash()

    elif intent == "empty_trash":
        return require_confirmation("empty the trash", action_type="empty_trash")

    elif intent == "list_files":
        return list_files()

    elif intent == "set_reminder":
        time_input = args.get("time")
        message = args.get("message")
        if time_input:
            set_reminder(time_input, message)
            return f"Got it. I’ll remind you at {time_input}."
        return "Tell me the time like 18:30."

    elif intent == "send_telegram":
        name = args.get("name")
        message = args.get("message")
        if not name or not message:
            return "Put message in quotes."
        try:
            chat_id = get_chat_id(name)
            if chat_id:
                send_telegram_to(chat_id, message)
                return f"Message sent to {name}."
            else:
                return f"who is {name} sir?"
        except:
            return "Couldn't send message."

    elif intent == "open_code":
        try:
            os.system("code .")
            return "Launching VS Code..."
        except:
            return "Couldn't launch VS Code."

    elif intent == "play_youtube":
        query = args.get("query")
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

    elif intent == "get_time":
        return get_time()

    elif intent == "get_date":
        return get_date()

    elif intent == "get_day":
        return get_day()

    elif intent == "get_news":
        query = args.get("query", "latest")
        if not query:
            query = "latest"
        news = get_news(query)
        return f"Here’s what’s happening right now\n{news}"

    elif intent == "get_location":
        return get_location()

    elif intent == "get_weather":
        location = args.get("location")
        return get_weather(location if location else command)

    elif intent == "get_distance":
        from_loc = args.get("from_loc")
        to_loc = args.get("to_loc")
        if from_loc and to_loc:
            return get_distance(f"{from_loc} to {to_loc}")
        return get_distance(command)
    
    elif intent == "open_website":
        website_name = args.get("website_name")
        if website_name:
            web_result = open_website(website_name)
            if web_result:
                return web_result
        return open_website(command)

    if "distance" in command_lower:
        return get_distance(command)

    if command_lower.strip() in ["bye","see you", "goodbye", "exit", "quit"]:
        return "exit"

    return None