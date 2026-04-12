import subprocess
import os

WORKSPACE = os.path.expanduser("~/Desktop/friday_workspace")


def can_handle(text):
    keywords = ["github", "git", "commit", "push", "status", "add"]
    return any(k in text.lower() for k in keywords)


def run(command):
    command = command.lower()

    try:
        if "status" in command:
            return run_cmd("git status")

        elif "add" in command:
            return run_cmd("git add .")

        elif "commit" in command:
            return run_cmd('git commit -m "auto commit by friday"')

        elif "push" in command:
            return run_cmd("git push")

        elif "pull" in command:
            return run_cmd("git pull")

        else:
            return "Git command not recognized."

    except Exception as e:
        return f"Git error: {str(e)}"


def run_cmd(cmd):
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=WORKSPACE,
        capture_output=True,
        text=True
    )
    return result.stdout if result.stdout else result.stderr