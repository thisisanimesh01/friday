import os
import warnings
import time

warnings.filterwarnings("ignore")

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

from brain import ask_friday
from commands import execute_command
from memory.memory_manager import store_memory, retrieve_memory


def run_friday():
    #adding animation
    animation = "Starting Friday..."
    for i in range(len(animation) + 1):
        print(animation[:i], end="\r")
        time.sleep(0.1)
    print("friday is online! ")

    while True:
        user_input = input("Admin: ")

        if any(word in user_input.lower() for word in ["bye", "goodbye", "see you", "exit", "quit"]):
            print("Friday: Alright, see you later 👋")
            break

        result = execute_command(user_input)

        if result:
            print(f"\nFriday: {result}\n")
            store_memory(user_input, result)
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

            store_memory(user_input, response)


if __name__ == "__main__":
    run_friday()