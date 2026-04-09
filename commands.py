import os
import webbrowser
import urllib.parse
import yt_dlp
from brain import ask_friday
from reminder import set_reminder, send_telegram_to
from contacts import get_chat_id
import re
from news import get_news
from weather import get_weather
from time_date import get_time, get_date, get_day
from maps import get_distance, get_location
from memory.memory_manager import store_memory, retrieve_memory

def execute_command(command):
    command = command.lower()

    #for reminder
    if "remind me" in command:
        match = re.search(r"(\d{1,2}:\d{2})", command)

        if match:
            time_input = match.group(1)
            message = command.replace(match.group(1), "").replace("remind me", "").strip()

            set_reminder(time_input, message)
            return f"Got it. I’ll remind you at {time_input}."

        return "Tell me the time like 18:30."

    # for sending telegram message
    if "send" in command and "to" in command:
        try:
            msg_match = re.search(r'"(.*?)"', command)
            name = command.split("to")[-1].strip()

            if msg_match:
                message = msg_match.group(1)
                chat_id = get_chat_id(name)

                if chat_id:
                    send_telegram_to(chat_id, message)
                    return f"Message going to {name} "
                else:
                    return f"I don’t know {name} yet."
            else:
                return "Put message in quotes."

        except Exception as e:
            print("DEBUG:", e)
            return "Couldn't send message."

    if any(word in command for word in ["open", "go to", "launch"]):
        sites = {
            "leetcode": "https://leetcode.com/u/animeshyadav/",
            "github": "https://github.com/thisisanimesh01",
            "linkedin": "https://www.linkedin.com/in/animesh-yadav-39460b276/",
            "thisianimesh01": "https://www.instagram.com/thisisanimesh.01/",
            "gmail": "https://mail.google.com",
            "outlook" : "https://outlook.office.com/mail/",
            "brave" : "brave://newtab",
            "whatsapp" : "whatsapp://",
            "chess" : "https://www.chess.com/member/animeshyadav"

        }

        for site in sites:
            if site in command:
                webbrowser.open(sites[site])
                return f"Opening {site} ..."

    if "launch" in command and "code" in command:
        try:
            os.system("code .")
            return "Launching VS Code..."
        except Exception as e:
            print("DEBUG:", e)
            return "Couldn't launch VS Code."

    #for youtube and google
    if "youtube" in command:
        query = command.replace("youtube", "").replace("play", "").strip()

        if query:
            try:
                ydl_opts = {
                    "quiet": True,
                    "extract_flat": True
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch:{query}", download=False)

                    if "entries" in info and len(info["entries"]) > 0:
                        video = info["entries"][0]
                        url = f"https://www.youtube.com/watch?v={video['id']}"
                        webbrowser.open(url)
                        return f"Playing {query} on YouTube..."
                    else:
                        raise Exception("No results found")

            except Exception as e:
                print("DEBUG:", e)
                search_query = urllib.parse.quote(query)
                url = f"https://www.youtube.com/results?search_query={search_query}"
                webbrowser.open(url)
                return "Error playing video, showing results instead."

        else:
            webbrowser.open("https://youtube.com")
            return "Opening YouTube..."


    #date & time
    if "time" in command:
        return get_time()
    elif "date" in command:
        return get_date()
    elif "day" in command:
        return get_day()

   #news command
    if any(word in command for word in ["news", "headlines"]):
        query = command.replace("news", "").strip()

        if not query:
            query = "latest"

        news = get_news(query)
        return f"Here’s what’s happening right now 📰\n{news}"

    #for location & distance
    elif "where am i" in command or "my location" in command:
        return get_location()
    elif "distance" in command:
        return get_distance(command)

    #for weather
    elif "weather" in command.lower() or "temperature" in command.lower():
        return get_weather(command)

    #for goole search
    elif "google" in command:
        webbrowser.open("https://google.com")
        return "Opening Google..."

    #to exit
    elif "bye" in command:
        return "exit"

    else:
        return None