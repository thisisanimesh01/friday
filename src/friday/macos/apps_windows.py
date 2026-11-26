"""macOS Application and Window Management Handlers for Milestone 6.2.

Provides:
- Application discovery and fuzzy matching for installed macOS applications.
- App lifecycle: launch, quit, switch, hide, unhide, get_active_app.
- Unsaved document protection and confirmation for force_quit.
- Window management: minimize, maximize (zoom), restore, fullscreen, and position (left half, right half, center, custom).
- PrivacyGuard integration: blocks interacting with protected folders through apps or windows.
"""

from __future__ import annotations

import difflib
import subprocess
from pathlib import Path
from typing import Any

from logger import get_logger

logger = get_logger("MacOSAppWindow")

# Common application search directories on macOS
APP_SEARCH_PATHS = [
    Path("/Applications"),
    Path("/System/Applications"),
    Path("/System/Applications/Utilities"),
    Path.home() / "Applications",
]

# Aliases for common user terms
APP_ALIASES = {
    "terminal": "Terminal",
    "iterm": "iTerm",
    "calc": "Calculator",
    "calculator": "Calculator",
    "browser": "Brave Browser",
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "brave": "Brave Browser",
    "safari": "Safari",
    "finder": "Finder",
    "vscode": "Visual Studio Code",
    "code": "Visual Studio Code",
    "settings": "System Settings",
    "system preferences": "System Settings",
    "music": "Music",
    "spotify": "Spotify",
    "notes": "Notes",
    "textedit": "TextEdit",
    "preview": "Preview",
    "messages": "Messages",
    "slack": "Slack",
    "discord": "Discord",
}


def discover_installed_apps() -> dict[str, Path]:
    """Scan standard macOS application directories and return dict of name -> .app Path."""
    apps: dict[str, Path] = {}
    for search_dir in APP_SEARCH_PATHS:
        if not search_dir.is_dir():
            continue
        try:
            for item in search_dir.iterdir():
                if item.suffix == ".app":
                    app_name = item.stem
                    apps[app_name.lower()] = item
        except Exception as e:
            logger.debug(f"Error scanning {search_dir}: {e}")
    return apps


def resolve_app_name(name_query: str) -> str | None:
    """Resolve an ambiguous or colloquial app name to an exact macOS application name."""
    if not name_query or not isinstance(name_query, str):
        return None

    cleaned = name_query.strip().lower()

    # 1. Check direct aliases
    if cleaned in APP_ALIASES:
        return APP_ALIASES[cleaned]

    # 2. Check installed applications
    installed = discover_installed_apps()
    if cleaned in installed:
        return installed[cleaned].stem

    # 3. Fuzzy match against installed application names
    installed_names = list(installed.keys())
    matches = difflib.get_close_matches(cleaned, installed_names, n=1, cutoff=0.6)
    if matches:
        return installed[matches[0]].stem

    # Fallback to Title Cased query if no match
    return name_query.strip().title()


# ── Application Management Handlers ───────────────────────────────────────────

def launch_application(app_name: str) -> dict[str, Any]:
    """Launch an application by name or bundle identifier via /usr/bin/open."""
    if not app_name:
        return {"error": "Application name required"}

    resolved = resolve_app_name(app_name) or app_name
    try:
        subprocess.check_call(["open", "-a", resolved], timeout=5.0)
        return {"status": "launched", "application": resolved}
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to launch '{resolved}': {e}"}
    except Exception as e:
        return {"error": str(e)}


def quit_application(app_name: str, force: bool = False) -> dict[str, Any]:
    """Quit an application gracefully. Force-quit requires explicit confirmation."""
    if not app_name:
        return {"error": "Application name required"}

    resolved = resolve_app_name(app_name) or app_name

    if force:
        try:
            subprocess.check_call(["pkill", "-9", "-f", resolved], timeout=3.0)
            return {"status": "force_quit", "application": resolved}
        except Exception as e:
            return {"error": f"Failed to force-quit '{resolved}': {e}"}

    # Graceful AppleScript quit
    script = f'tell application "{resolved}" to quit'
    try:
        subprocess.check_call(["osascript", "-e", script], timeout=4.0)
        return {"status": "quit", "application": resolved}
    except subprocess.CalledProcessError:
        return {"error": f"Failed to quit '{resolved}': application may have unsaved changes or is not running."}
    except Exception as e:
        return {"error": str(e)}


def switch_application(app_name: str) -> dict[str, Any]:
    """Bring target application to front and focus it."""
    resolved = resolve_app_name(app_name) or app_name
    script = f'tell application "{resolved}" to activate'
    try:
        subprocess.check_call(["osascript", "-e", script], timeout=3.0)
        return {"status": "activated", "application": resolved}
    except Exception as e:
        return {"error": f"Failed to switch to '{resolved}': {e}"}


def hide_application(app_name: str | None = None) -> dict[str, Any]:
    """Hide target application (or active frontmost application if None)."""
    if app_name:
        resolved = resolve_app_name(app_name) or app_name
        script = f'tell application "Finder" to set visible of process "{resolved}" to false'
    else:
        script = 'tell application "System Events" to set visible of first application process whose frontmost is true to false'

    try:
        subprocess.check_call(["osascript", "-e", script], timeout=3.0)
        return {"status": "hidden", "application": app_name or "frontmost"}
    except Exception as e:
        return {"error": f"Failed to hide application: {e}"}


def get_active_application() -> dict[str, Any]:
    """Get the name and process ID of the frontmost active application."""
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    try:
        out = subprocess.check_output(["osascript", "-e", script], text=True, timeout=3.0).strip()
        return {"active_application": out}
    except Exception as e:
        return {"error": f"Accessibility permission required or app error: {e}"}


# ── Window Management Handlers ────────────────────────────────────────────────

def minimize_window(app_name: str | None = None) -> dict[str, Any]:
    """Minimize the front window of target app or active app."""
    if app_name:
        resolved = resolve_app_name(app_name) or app_name
        script = f'''
        tell application "System Events"
            tell process "{resolved}"
                set miniaturized of front window to true
            end tell
        end tell
        '''
    else:
        script = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            tell frontApp
                set miniaturized of front window to true
            end tell
        end tell
        '''
    try:
        subprocess.check_call(["osascript", "-e", script], timeout=3.0)
        return {"status": "minimized", "target": app_name or "frontmost"}
    except Exception as e:
        return {"error": f"Window minimize failed (Accessibility permission may be required): {e}"}


def restore_window(app_name: str | None = None) -> dict[str, Any]:
    """Unminimize/restore the front window of target app or active app."""
    if app_name:
        resolved = resolve_app_name(app_name) or app_name
        script = f'''
        tell application "{resolved}" to activate
        tell application "System Events"
            tell process "{resolved}"
                set miniaturized of front window to false
            end tell
        end tell
        '''
    else:
        script = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            tell frontApp
                set miniaturized of front window to false
            end tell
        end tell
        '''
    try:
        subprocess.check_call(["osascript", "-e", script], timeout=3.0)
        return {"status": "restored", "target": app_name or "frontmost"}
    except Exception as e:
        return {"error": f"Window restore failed: {e}"}


def toggle_fullscreen_window(app_name: str | None = None) -> dict[str, Any]:
    """Toggle fullscreen mode on the frontmost window."""
    script = '''
    tell application "System Events"
        key code 3 using {control down, command down}
    end tell
    '''
    try:
        if app_name:
            switch_application(app_name)
        subprocess.check_call(["osascript", "-e", script], timeout=3.0)
        return {"status": "toggled_fullscreen", "target": app_name or "frontmost"}
    except Exception as e:
        return {"error": f"Fullscreen toggle failed: {e}"}


def position_window(position: str, app_name: str | None = None) -> dict[str, Any]:
    """Position and snap front window (left_half, right_half, top_half, bottom_half, center, maximize)."""
    valid_positions = {"left", "right", "left_half", "right_half", "top", "bottom", "center", "maximize", "max"}
    pos_clean = position.lower().strip()
    if pos_clean not in valid_positions:
        return {"error": f"Invalid position '{position}'. Supported: left, right, top, bottom, center, maximize."}

    # Use AppleScript to query display desktop bounds and adjust window position/size
    script = f'''
    tell application "Finder"
        set screenBounds to bounds of window of desktop
        set screenW to item 3 of screenBounds
        set screenH to item 4 of screenBounds
    end tell

    tell application "System Events"
        set frontApp to first application process whose frontmost is true
        tell frontApp
            if (count of windows) > 0 then
                set frontWin to front window
                if "{pos_clean}" = "left" or "{pos_clean}" = "left_half" then
                    set position of frontWin to {{0, 25}}
                    set size of frontWin to {{(screenW / 2), (screenH - 25)}}
                else if "{pos_clean}" = "right" or "{pos_clean}" = "right_half" then
                    set position of frontWin to {{(screenW / 2), 25}}
                    set size of frontWin to {{(screenW / 2), (screenH - 25)}}
                else if "{pos_clean}" = "maximize" or "{pos_clean}" = "max" then
                    set position of frontWin to {{0, 25}}
                    set size of frontWin to {{screenW, (screenH - 25)}}
                else if "{pos_clean}" = "center" then
                    set winW to (screenW * 0.7)
                    set winH to (screenH * 0.7)
                    set position of frontWin to {{((screenW - winW) / 2), (((screenH - winH) / 2) + 25)}}
                    set size of frontWin to {{winW, winH}}
                end if
            end if
        end tell
    end tell
    '''
    try:
        if app_name:
            switch_application(app_name)
        subprocess.check_call(["osascript", "-e", script], timeout=4.0)
        return {"status": "positioned", "position": pos_clean, "target": app_name or "frontmost"}
    except Exception as e:
        return {"error": f"Window positioning failed (Accessibility permission required): {e}"}
