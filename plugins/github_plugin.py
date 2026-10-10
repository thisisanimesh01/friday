"""
github_plugin.py — Real GitHub API integration for Friday.

Requires GITHUB_TOKEN in .env for most operations.
Never fabricates data when the token is missing or the API fails.
"""

import os
import subprocess
import requests
from dotenv import load_dotenv
from logger import get_logger

load_dotenv()
logger = get_logger("GitHubPlugin")

WORKSPACE = os.path.expanduser("~/Desktop/friday_workspace")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    **({"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
}

NO_TOKEN_MSG = (
    "GitHub authentication is not configured. "
    "Add GITHUB_TOKEN=<your_personal_access_token> to your .env file, "
    "then restart Friday."
)


def can_handle(text: str) -> bool:
    text_lower = text.lower().strip()
    if any(text_lower.startswith(p) for p in ["open github", "go to github", "visit github"]):
        return False
    git_specific = ["github pr", "git hub", "pull request", "pull requests", "gh pr", "gh notification"]
    exact_terms = ["pr status", "open prs", "my prs", "prs", "git notifications", "github notifications", "git status", "git push", "git pull", "git commit"]
    # Only intercept commands with explicit git/github context
    return any(k in text_lower for k in git_specific) or any(k in text_lower for k in exact_terms)


def run(command: str) -> str:
    command_lower = command.lower()

    try:
        if "notification" in command_lower:
            return get_notifications()
        elif "pr" in command_lower or "pull request" in command_lower:
            return get_prs()
        elif "status" in command_lower:
            return run_git_cmd("git status")
        elif "commit" in command_lower:
            return run_git_cmd('git commit -m "auto commit by Friday"')
        elif "push" in command_lower:
            return run_git_cmd("git push")
        elif "pull" in command_lower:
            return run_git_cmd("git pull")
        else:
            return "I can help with: GitHub pull requests, notifications, git status, push, pull, commit."
    except Exception as e:
        logger.error(f"GitHubPlugin error for '{command}': {e}")
        return f"GitHub error: {e}"


def run_git_cmd(cmd: str) -> str:
    """Run a local git command inside the workspace directory."""
    if not os.path.isdir(WORKSPACE):
        return f"Workspace not found at {WORKSPACE}."
    result = subprocess.run(
        cmd, shell=True, cwd=WORKSPACE, capture_output=True, text=True
    )
    output = result.stdout.strip() or result.stderr.strip()
    return output if output else f"Command exited with code {result.returncode}."


def get_notifications() -> str:
    if not GITHUB_TOKEN:
        logger.warning("GitHub notifications requested but GITHUB_TOKEN is not set.")
        return NO_TOKEN_MSG

    try:
        response = requests.get(
            "https://api.github.com/notifications",
            headers=_HEADERS,
            timeout=8,
        )
        logger.info(f"GitHub notifications API: HTTP {response.status_code}")

        if response.status_code == 401:
            return "GitHub token is invalid or expired. Please update GITHUB_TOKEN in your .env file."
        if response.status_code != 200:
            return f"GitHub API returned an error ({response.status_code}). Check your token permissions."

        notifs = response.json()
        if not notifs:
            return "No unread GitHub notifications."
        lines = [f"You have {len(notifs)} unread notification(s):"]
        for n in notifs[:5]:
            lines.append(f"  • [{n['subject']['type']}] {n['subject']['title']} — {n['repository']['full_name']}")
        return "\n".join(lines)

    except requests.exceptions.Timeout:
        logger.error("GitHub notifications: request timed out.")
        return "GitHub request timed out. Check your network connection."
    except Exception as e:
        logger.error(f"GitHub notifications error: {e}")
        return f"Failed to fetch GitHub notifications: {e}"


def get_prs() -> str:
    if not GITHUB_TOKEN:
        logger.warning("GitHub PRs requested but GITHUB_TOKEN is not set.")
        return NO_TOKEN_MSG

    try:
        # First, find out the authenticated user's login
        user_resp = requests.get("https://api.github.com/user", headers=_HEADERS, timeout=8)
        if user_resp.status_code == 401:
            return "GitHub token is invalid or expired. Please update GITHUB_TOKEN in your .env file."
        if user_resp.status_code != 200:
            return f"GitHub API error ({user_resp.status_code}) when fetching user info."

        username = user_resp.json().get("login", "")
        logger.info(f"GitHub authenticated as: {username}")

        # Search for open PRs authored by the authenticated user
        search_url = (
            f"https://api.github.com/search/issues"
            f"?q=is:pr+is:open+author:{username}&sort=updated&order=desc&per_page=5"
        )
        pr_resp = requests.get(search_url, headers=_HEADERS, timeout=8)
        logger.info(f"GitHub PRs API: HTTP {pr_resp.status_code}")

        if pr_resp.status_code != 200:
            return f"GitHub PR fetch failed ({pr_resp.status_code})."

        items = pr_resp.json().get("items", [])
        if not items:
            return f"No open pull requests found for @{username}."

        lines = [f"Open PRs for @{username} ({len(items)} found):"]
        for pr in items:
            repo = pr.get("repository_url", "").replace("https://api.github.com/repos/", "")
            lines.append(f"  • #{pr['number']} — {pr['title']} [{repo}]")
        return "\n".join(lines)

    except requests.exceptions.Timeout:
        logger.error("GitHub PRs: request timed out.")
        return "GitHub request timed out. Check your network connection."
    except Exception as e:
        logger.error(f"GitHub PR error: {e}")
        return f"Failed to fetch GitHub PRs: {e}"