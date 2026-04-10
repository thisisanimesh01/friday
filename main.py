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
from sandbox.file_manager import delete_file
from security.permission_manager import confirm_action

pending_action = None


def run_friday():
    global pending_action

    # animation
    animation = "Starting Friday..."
    for i in range(len(animation) + 1):
        print(animation[:i], end="\r")
        time.sleep(0.1)
    print("friday is online! ")

    while True:
        user_input = input("Admin: ").strip()


        if any(word in user_input.lower() for word in ["bye", "goodbye", "see you", "exit", "quit"]):
            print("Friday: Alright, see you later 👋")
            break


        if pending_action:
            if confirm_action(user_input):
                if pending_action["type"] == "delete":
                    result = delete_file(pending_action["file"], confirm=True)
                else:
                    result = "Unknown pending action"
            else:
                result = "Action cancelled."

            pending_action = None
            print(f"\nFriday: {result}\n")

            threading.Thread(target=store_memory, args=(user_input, result)).start()
            continue


        result = execute_command(user_input)

        if result:

            if isinstance(result, dict) and result.get("status") == "confirmation_required":
                filename = extract_filename(user_input)

                pending_action = {
                    "type": "delete",
                    "file": filename
                }

                print(f"\nFriday: {result['message']}\n")

                threading.Thread(target=store_memory, args=(user_input, result)).start()
                continue

            print(f"\nFriday: {result}\n")


            threading.Thread(target=store_memory, args=(user_input, result)).start()

        else:
            past = retrieve_memory(user_input)

            context = ""
            for p in past:
                context += f"User: {p[1]}\nFriday: {p[2]}\n"

            enhanced_input = context + f"\nUser: {user_input}\nFriday:"

            try:
                response = ask_friday(enhanced_input)
            except:
                if past:
                    response = "⚠️ I'm offline, but from what I remember:\n\n"
                    for p in past:
                        response += f"- You said: {p[1]}\n"
                else:
                    response = "⚠️ I'm offline and don't have enough memory yet."

            print(f"\nFriday: {response}\n")

            threading.Thread(target=store_memory, args=(user_input, response)).start()


if __name__ == "__main__":
    run_friday()