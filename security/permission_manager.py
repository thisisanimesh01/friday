def require_confirmation(action: str, action_type: str = None, target: str = None) -> dict:
    data = {
        "status": "confirmation_required",
        "message": f"Are you sure you want to {action}? (yes/no)"
    }
    if action_type:
        data["action_type"] = action_type
    if target:
        data["target"] = target
    return data

def confirm_action(user_input: str) -> bool:
    return user_input.strip().lower() in ["yes", "y"]


# Simple site -> browser permission mapping
# - Coursera: chrome
# - everything else browsing: brave
_site_browser_prefs = {
    "coursera.org": "chrome",
    "www.coursera.org": "chrome",
}

# Ensure Spotify uses Brave (web player)
_site_browser_prefs.update({
    "open.spotify.com": "brave",
    "spotify.com": "brave",
})

def get_browser_for_url(url: str) -> str:
    """Return preferred browser for a given URL.

    If the URL matches a known site mapping (e.g. Coursera), return that.
    Otherwise return 'brave' for general browsing.
    """
    try:
        # Simple heuristic: check hostname contains key
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
    except Exception:
        host = url

    host = host.lower()

    for key, browser in _site_browser_prefs.items():
        if key in host:
            return browser

    return "brave"

def set_site_browser(site: str, browser: str):
    """Allow runtime updates to the site->browser mapping."""
    _site_browser_prefs[site.lower()] = browser.lower()

def get_all_mappings():
    return dict(_site_browser_prefs)