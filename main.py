import os
import warnings
import time
import sys
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
from memory.memory_manager import store_memory, retrieve_memory, trigger_summarization, get_current_summary, get_rich_context
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
        print(animation[:i], end="\r", flush=True)
        time.sleep(0.05)
    print("friday is online!\n", flush=True)

    def display_response(text: str):
        # Standardized response formatting:
        # - one blank line before the response
        # - the `friday:` prefix (lower-case)
        # - one blank line after the response so the next prompt appears on its own line
        print(f"\nfriday: {text}\n", flush=True)

    while True:
        try:
            sys.stdout.flush()
            user_input = input("admin: ").strip()
        except (EOFError, KeyboardInterrupt):
            display_response("Alright, see you later 👋")
            break

        if not user_input:
            continue

        exit_commands = ["bye", "goodbye", "exit", "quit"]
        if user_input.lower().strip() in exit_commands:
            display_response("Alright, see you later 👋")
            break

        if is_last_message_query(user_input):
            rows = retrieve_memory(user_input)
            last_user_msg = get_last_user_message(rows)
            if last_user_msg:
                display_response(f"You said {last_user_msg}")
            else:
                display_response("You haven't said anything yet.")
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
            display_response(result)

            threading.Thread(target=store_memory, args=(user_input, result)).start()
            continue

        # Deterministic priority: media and open-site commands should be handled
        # before plugins and before the generic sensitive filter to avoid false positives.
        import re

        # Media play explicit intents
        m_youtube = re.match(r"(?is)^play\s+(.+?)\s+on\s+youtube\s*$", user_input)
        m_spotify = re.match(r"(?is)^play\s+(.+?)\s+on\s+spotify\s*$", user_input)

        # Explicit URL: https://... or www.... — must go through execute_command unchanged
        # Do NOT intercept here; route_command handles URL-first detection.
        is_explicit_url = (
            user_input.strip().startswith("http://") or
            user_input.strip().startswith("https://") or
            user_input.strip().startswith("www.")
        )

        # Open site explicit intents (keyword-based, NOT for explicit URLs)
        m_open_site = None
        if not is_explicit_url:
            m_open_site = re.match(
                r"(?is)^(open|go to|visit)\s+"
                r"(youtube|spotify|github|coursera|wikipedia|google|leetcode|linkedin"
                r"|instagram|gmail|mail|outlook|whatsapp|chess|portfolio)\b",
                user_input
            )

        if m_youtube or m_spotify or m_open_site or is_explicit_url:
            # Directly handle deterministic commands to avoid plugin overrides
            result = execute_command(user_input)
            if result:
                display_response(result)
                threading.Thread(target=store_memory, args=(user_input, result), daemon=True).start()
            else:
                display_response(f"I couldn't complete that command.")
            continue

        if is_sensitive(user_input):
            display_response("Sorry Sir, I won’t process sensitive or private information.")
            continue

        plugin_response = handle_plugin(user_input)
        if plugin_response:
            display_response(plugin_response)
            threading.Thread(target=store_memory, args=(user_input, plugin_response)).start()
            continue

        result = execute_command(user_input)

        if result:

            if isinstance(result, dict) and result.get("status") == "confirmation_required":

                if "action_type" in result:
                    pending_action = {
                        "type": result["action_type"],
                        "file": result.get("target")
                    }
                else:
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

                display_response(result['message'])

                threading.Thread(target=store_memory, args=(user_input, result)).start()
                continue

            display_response(result)

            threading.Thread(target=store_memory, args=(user_input, result)).start()

        else:
            # Build rich context: rolling summary + recent pairs + semantic memory
            context = get_rich_context(user_input)
            enhanced_input = (context + "\n\n" if context else "") + f"User: {user_input}\nFriday:"

            trigger_summarization()
            try:
                response = ask_friday(enhanced_input)
            except Exception:
                past = retrieve_memory(user_input)
                if past:
                    response = "I'm having trouble reaching the AI right now. From what I remember:\n\n"
                    for p in past[:3]:
                        user_text, bot_text = extract_user_bot(p)
                        response += f"- You said: \"{user_text}\" → I replied: \"{bot_text}\"\n"
                else:
                    response = "I'm offline and don't have enough memory yet."

            display_response(response)
            threading.Thread(target=store_memory, args=(user_input, response), daemon=True).start()

if __name__ == "__main__":
    run_friday()