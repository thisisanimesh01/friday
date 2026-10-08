import subprocess
import os
import requests

WORKSPACE = os.path.expanduser("~/Desktop/friday_workspace")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def can_handle(text):
    text_lower = text.lower()
    git_specific = ["git ", "github", "gh ", "pull request", "pull requests"]
    exact_terms = ["pr status", "prs", "open prs", "my prs", "git notifications", "github notifications"]
    return any(k in text_lower for k in git_specific) or any(k in text_lower for k in exact_terms)

def run(command):
    command = command.lower()

    try:
        if "notification" in command:
            return get_notifications()
        elif "pr" in command or "pull request" in command:
            return get_prs()
        elif "status" in command:
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

def get_notifications():
    if not GITHUB_TOKEN:
        return "Mock Notification: [Action Required] Review PR #42 in project/friday"
    
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get("https://api.github.com/notifications", headers=headers)
        if response.status_code == 200:
            notifs = response.json()
            if not notifs:
                return "No new GitHub notifications."
            return f"You have {len(notifs)} unread notifications. Latest: {notifs[0]['subject']['title']}"
        return f"Failed to fetch notifications: {response.status_code}"
    except Exception as e:
        return f"Error fetching notifications: {str(e)}"

def get_prs():
    if not GITHUB_TOKEN:
        return "Mock PR Summary: PR #42 'Fix memory leak' is waiting for your review."
    
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get("https://api.github.com/search/issues?q=is:pr+is:open+assignee:@me", headers=headers)
        if response.status_code == 200:
            prs = response.json().get('items', [])
            if not prs:
                return "No open pull requests assigned to you."
            return f"You have {len(prs)} open PRs. Latest: {prs[0]['title']}"
        return f"Failed to fetch PRs: {response.status_code}"
    except Exception as e:
        return f"Error fetching PRs: {str(e)}"