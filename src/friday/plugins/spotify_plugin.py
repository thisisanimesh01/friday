"""
spotify_plugin.py — macOS Spotify control via AppleScript for Friday.

Uses `osascript` to send commands to the Spotify desktop app.
Verifies Spotify is installed and running before sending commands.
Never claims success when the command failed.
"""

import subprocess
import os
import re
from logger import get_logger

logger = get_logger("SpotifyPlugin")

# Spotify app bundle path on macOS (standard location)
SPOTIFY_APP = "/Applications/Spotify.app"


def can_handle(text: str) -> bool:
    text_lower = text.lower()
    if "youtube" in text_lower:
        return False
    # Only handle if desktop Spotify is installed and the command is explicitly for the desktop app.
    # We must not intercept web-player intents like 'play ... on spotify' which should go to browser_manager.
    keywords = [
        "spotify desktop", "spotify app", "open spotify app", "launch spotify", "spotify player",
        "spotify:pause", "spotify:play", "spotify:next", "spotify:previous"
    ]

    # Quick heuristic: if the literal phrase 'on spotify' appears, prefer web player path elsewhere
    if re.search(r"(?is)on\s+spotify", text):
        return False

    # Only return True when desktop Spotify is installed and a desktop-specific keyword is found
    if _is_spotify_installed() and any(k in text_lower for k in keywords):
        return True

    return False


def _is_spotify_installed() -> bool:
    return os.path.isdir(SPOTIFY_APP)


def _is_spotify_running() -> bool:
    """Check if Spotify process is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-x", "Spotify"],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def _run_applescript(script: str) -> tuple[bool, str]:
    """
    Execute an AppleScript command via osascript.
    Returns (success: bool, message: str).
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=8
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            stderr = result.stderr.strip()
            logger.error(f"AppleScript failed (code {result.returncode}): {stderr}")
            return False, stderr
    except subprocess.TimeoutExpired:
        logger.error("AppleScript timed out after 8 seconds.")
        return False, "AppleScript timed out."
    except Exception as e:
        logger.error(f"AppleScript execution error: {e}")
        return False, str(e)


def run(command: str) -> str:
    command_lower = command.lower()

    # Check installation
    if not _is_spotify_installed():
        logger.warning("Spotify is not installed at /Applications/Spotify.app")
        return (
            "Spotify doesn't appear to be installed on this Mac. "
            "Install it from https://www.spotify.com/download/ and try again."
        )

    # Determine the AppleScript action
    if "pause" in command_lower or "stop" in command_lower:
        action = "pause"
        script = 'tell application "Spotify" to pause'
        action_label = "Paused"
    elif "next" in command_lower or "skip" in command_lower:
        action = "next track"
        script = 'tell application "Spotify" to next track'
        action_label = "Skipped to next track"
    elif "previous" in command_lower or "prev" in command_lower:
        action = "previous track"
        script = 'tell application "Spotify" to previous track'
        action_label = "Went back to previous track"
    elif "resume" in command_lower:
        action = "play"
        script = 'tell application "Spotify" to play'
        action_label = "Resumed playback"
    else:
        # Default: play / open Spotify
        action = "play"
        script = 'tell application "Spotify" to play'
        action_label = "Started playback"

    # If Spotify is not running, try to launch it first
    if not _is_spotify_running():
        logger.info("Spotify is not running — launching it.")
        launch_ok, launch_err = _run_applescript('tell application "Spotify" to activate')
        if not launch_ok:
            # Check if it might be an automation permission issue
            if "not allowed" in launch_err.lower() or "1002" in launch_err:
                return (
                    "macOS is blocking Friday from controlling Spotify. "
                    "Go to System Settings → Privacy & Security → Automation "
                    "and enable 'Terminal' (or whichever app runs Friday) to control Spotify."
                )
            return f"Couldn't launch Spotify: {launch_err}"

        # Small delay to let Spotify start
        import time
        time.sleep(2)

    # Execute the actual command
    success, error_msg = _run_applescript(script)

    if success:
        logger.info(f"Spotify command succeeded: {action}")
        return f"{action_label} on Spotify."
    else:
        # Diagnose the failure
        if "not allowed" in error_msg.lower() or "1002" in error_msg:
            logger.warning("Spotify AppleScript blocked by macOS automation permissions.")
            return (
                "macOS is blocking Friday from controlling Spotify. "
                "Go to System Settings → Privacy & Security → Automation "
                "and enable your terminal app to control Spotify, then try again."
            )
        elif "not running" in error_msg.lower():
            return "Spotify isn't running. Please open Spotify first, then try again."
        else:
            logger.error(f"Spotify command failed for '{command}': {error_msg}")
            return f"Couldn't control Spotify. Error: {error_msg}"
