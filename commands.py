import os
import webbrowser
import subprocess
from logger import get_logger
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
from security.permission_manager import require_confirmation, get_browser_for_url
from browser_manager import open_or_reuse_tab
from browser_manager import search_and_play_youtube, search_and_play_spotify, open_url

logger = get_logger("Browser")
from security.path_validator import get_safe_path
from llm_router import route_command

def extract_filename(command: str):
    match = re.search(
        r"(?:create|make|read|delete|remove|open|show|restore|empty)\s+(?:file\s+)?([\w\.\-]+)",
        command.lower()
    )
    return match.group(1) if match else None

def open_website(command, is_url=False):
    sites = {
        "mail": "https://mail.google.com",
        "leetcode": "https://leetcode.com/u/animeshyadav/",
        "coursera": "https://www.coursera.org",
        "github": "https://github.com/thisisanimesh01",
        "linkedin": "https://www.linkedin.com/in/animesh-yadav-39460b276/",
        "instagram": "https://www.instagram.com/thisisanimesh.01/",
        "gmail": "https://mail.google.com",
        "outlook": "https://outlook.office.com/mail/",
        "whatsapp": "https://web.whatsapp.com",
        "chess": "https://www.chess.com/home",
        "wikipedia": "https://www.wikipedia.org",
        "google": "https://google.com",
        "youtube": "https://youtube.com",
        "spotify": "https://open.spotify.com",
        "portfolio": "https://thisisanimesh01.github.io/Portfolio/",
    }

    cmd_stripped = command.strip()

    # ── EXPLICIT URL: pass through unchanged ─────────────────────────────────
    # If the input already is a URL (https://... or www....) or is_url flag set,
    # open it directly. Do NOT reduce it to a site name.
    if is_url or cmd_stripped.startswith("http://") or cmd_stripped.startswith("https://") or cmd_stripped.startswith("www."):
        url = cmd_stripped
        if url.startswith("www."):
            url = "https://" + url
        browser = "Chrome" if get_browser_for_url(url) == "chrome" else "Brave"
        open_in_preferred_browser(url)
        try:
            host = urllib.parse.urlparse(url).hostname or url
        except Exception:
            host = url
        return f"Opening {host} in {browser}."

    # ── SITE-NAME LOOKUP ─────────────────────────────────────────────────────
    cmd_lower = cmd_stripped.lower()

    # Exact key match (e.g. command passed as bare "google", "spotify", etc.)
    if cmd_lower in sites:
        url = sites[cmd_lower]
        browser = "Chrome" if get_browser_for_url(url) == "chrome" else "Brave"
        open_in_preferred_browser(url)
        return f"Opening {cmd_lower} in {browser}."

    # Keyword match anywhere in the command (e.g. "open google", "go to youtube")
    for site in sites:
        if site in cmd_lower:
            url = sites[site]
            browser = "Chrome" if get_browser_for_url(url) == "chrome" else "Brave"
            open_in_preferred_browser(url)
            return f"Opening {site} in {browser}."

    return None

def open_in_preferred_browser(url: str) -> bool:
    """Open `url` in the preferred browser, reusing an existing tab if the exact hostname matches."""
    browser_pref = get_browser_for_url(url)
    try:
        host = urllib.parse.urlparse(url).hostname or url
    except Exception:
        host = url
    logger.info("Browser request detected")
    logger.info(f"Target: {host}")
    logger.info(f"Browser selected: {browser_pref}")

    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""

        # Strip www. for matching purposes (same logic as browser_manager)
        if hostname.startswith("www."):
            hostname = hostname[4:]

        # Use the exact (www-stripped) hostname as the match key.
        # This means google.com only matches google.com tabs,
        # mail.google.com only matches mail.google.com tabs, etc.
        match_sub = hostname if hostname else None

        success = open_or_reuse_tab(url, browser_pref, match_substring=match_sub)
        if success:
            logger.info("Executing browser action")
            logger.info("Browser action successful")
            return True
        else:
            logger.error("Browser manager reported failure")
            return False
    except Exception as e:
        logger.error(f"Browser action failed: {e}")
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False


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
        # If query is not provided by router, try to extract from command
        if not query:
            m = re.search(r"(?is)play\s+(.+?)\s+on\s+youtube", command)
            if m:
                query = m.group(1).strip()

        if query:
            # Prefer resolving via yt_dlp to a watch URL (more reliable than DOM clicks)
            try:
                ydl_opts = {"quiet": True, "extract_flat": True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch:{query}", download=False)
                    if "entries" in info and len(info["entries"]) > 0:
                        video = info["entries"][0]
                        url = f"https://www.youtube.com/watch?v={video['id']}"
                        try:
                            from browser_manager import play_youtube_watch
                            ok, status = play_youtube_watch(url, browser_pref="brave")
                            if ok:
                                return f"Playing {query} on YouTube."
                            else:
                                if status == "playback_blocked_or_not_started":
                                    return "YouTube opened the video, but playback was blocked by the browser."
                                # else fallthrough to open search results
                        except Exception:
                            # If helper not available or failed, fall back to opening URL
                            open_in_preferred_browser(url)
                            return f"Playing {query} on YouTube."
            except Exception:
                pass
            # Fallback: open search results page in Brave
            search_query = urllib.parse.quote(query)
            url = f"https://www.youtube.com/results?search_query={search_query}"
            open_in_preferred_browser(url)
            return "Opening YouTube search results."
        else:
            open_in_preferred_browser("https://youtube.com")
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
        is_url = args.get("is_url", False)
        if website_name:
            web_result = open_website(website_name, is_url=is_url)
            if web_result:
                return web_result
        return open_website(command)

    elif intent == "play_spotify":
        query = args.get("query")
        if not query:
            m = re.search(r"play\s+(.+?)\s+(?:on\s+)?spotify", command, re.IGNORECASE)
            if m:
                query = m.group(1).strip()

        # Open Spotify web player and search for query
        if query:
            ok = search_and_play_spotify(query)
            if ok:
                return f"Playing {query} on Spotify."
            else:
                url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
                open_in_preferred_browser(url)
                return "Opening Spotify search results."
        else:
            open_in_preferred_browser("https://open.spotify.com")
            return "Opening Spotify in Brave."

    elif intent == "terminal_command":
        cmd = args.get("command", command)
        return (
            f"I see you typed a terminal command: `{cmd}`. "
            "Friday doesn't execute raw shell commands directly for safety. "
            "Run it in your terminal, or ask me to do a specific action like creating/deleting files."
        )

    if "distance" in command_lower:
        return get_distance(command)

    if command_lower.strip() in ["bye","see you", "goodbye", "exit", "quit"]:
        return "exit"

    return None