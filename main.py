from brain import ask_friday
from commands import execute_command


def run_friday():
    print("\nFriday is online. What’s up?\n")

    while True:
        user_input = input("Admin: ")

        # Check command
        result = execute_command(user_input)

        if any(word in user_input for word in ["bye", "goodbye", "see you", "exit", "quit"]):
            print("Friday: Alright, see you later 👋")
            break

        elif result:
            print(f"friday : {result}")

        else:
            response = ask_friday(user_input)
            print(f"\nFriday: {response}\n")



if __name__ == "__main__":
    run_friday()