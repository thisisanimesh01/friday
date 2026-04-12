import os
import warnings
import time
import threading

warnings.filterwarnings("ignore")

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

from brain import ask_friday
from commands import execute_command, extract_filename
from memory.memory_manager import store_memory, retrieve_memory
from sandbox.file_manager import delete_file, empty_trash, delete_folder
from security.permission_manager import confirm_action
from plugin_loader import load_plugins, handle_plugin

pending_action = None

def is_sensitive(text: str) -> bool:
    text = text.lower()

    sensitive_keywords = [
        "password",
        "pass",
        "api_key",
        "apikey",
        "token",
        "secret",
        ".env",
        "private",
        "confidential",
        "friday_workspace",
        "ssh",
        "key",
        "credential"
    ]

    return any(word in text for word in sensitive_keywords)

def is_last_message_query(query: str) -> bool:
    query = query.lower()
    triggers = [
        "what did i say",
        "last message",
        "what did i just say",
        "repeat what i said"
    ]
    return any(t in query for t in triggers)

def extract_user_bot(p):
    if isinstance(p, (list, tuple)):
        if len(p) >= 3:
            return p[1], p[2]
        elif len(p) == 2:
            return p[0], p[1]
    return "", ""

def get_last_user_message(rows):
    if not rows:
        return None
    last = rows[-1]
    if isinstance(last, (list, tuple)):
        if len(last) >= 3:
            return last[1]
        elif len(last) >= 1:
            return last[0]
    return None

def run_friday():
    global pending_action

    load_plugins()

    animation = "Starting Friday..."
    for i in range(len(animation) + 1):
        print(animation[:i], end="\r")
        time.sleep(0.1)
    print("friday is online! ")

    while True:
        user_input = input("Admin: ").strip()

        if any(word in user_input.lower() for word in ["bye", "goodbye", "see you", "exit", "quit"]):
            print("Friday: Alright, see you later")
            break

        if is_last_message_query(user_input):
            rows = retrieve_memory(user_input)
            last_user_msg = get_last_user_message(rows)
            if last_user_msg:
                print(f"\nFriday: You said {last_user_msg}\n")
            else:
                print("\nFriday: You haven't said anything yet.\n")
            continue

        if pending_action:
            if confirm_action(user_input):

                if pending_action["type"] == "delete_file":
                    result = delete_file(pending_action["file"], confirm=True)

                elif pending_action["type"] == "delete_folder":
                    result = delete_folder(pending_action["file"], confirm=True)

                elif pending_action["type"] == "empty_trash":
                    result = empty_trash()

                else:
                    result = "Unknown pending action"

            else:
                result = "Action cancelled."

            pending_action = None
            print(f"\nFriday: {result}\n")

            threading.Thread(target=store_memory, args=(user_input, result)).start()
            continue

        if is_sensitive(user_input):
            print("\nFriday: I won’t process sensitive or private information.\n")
            continue

        plugin_response = handle_plugin(user_input)
        if plugin_response:
            print(f"\nFriday: {plugin_response}\n")
            threading.Thread(target=store_memory, args=(user_input, plugin_response)).start()
            continue

        result = execute_command(user_input)

        if result:

            if isinstance(result, dict) and result.get("status") == "confirmation_required":

                command_lower = user_input.lower()

                if "empty trash" in command_lower:
                    pending_action = {
                        "type": "empty_trash"
                    }

                elif "delete" in command_lower or "remove" in command_lower:
                    filename = extract_filename(user_input)
                    path = os.path.join(os.path.expanduser("~/Desktop/friday_workspace"), filename)

                    if os.path.isdir(path):
                        pending_action = {
                            "type": "delete_folder",
                            "file": filename
                        }
                    else:
                        pending_action = {
                            "type": "delete_file",
                            "file": filename
                        }

                else:
                    pending_action = None

                print(f"\nFriday: {result['message']}\n")

                threading.Thread(target=store_memory, args=(user_input, result)).start()
                continue

            print(f"\nFriday: {result}\n")

            threading.Thread(target=store_memory, args=(user_input, result)).start()

        else:
            past = retrieve_memory(user_input)

            context = ""
            for p in past:
                user_text, bot_text = extract_user_bot(p)
                context += f"User: {user_text}\nFriday: {bot_text}\n"

            enhanced_input = context + f"\nUser: {user_input}\nFriday:"

            try:
                response = ask_friday(enhanced_input)
            except:
                if past:
                    response = "I'm offline, but from what I remember:\n\n"
                    for p in past:
                        user_text, _ = extract_user_bot(p)
                        response += f"- You said: {user_text}\n"
                else:
                    response = "I'm offline and don't have enough memory yet."

            print(f"\nFriday: {response}\n")

            threading.Thread(target=store_memory, args=(user_input, response)).start()

if __name__ == "__main__":
    run_friday()