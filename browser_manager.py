import subprocess
import urllib.parse
from logger import get_logger
import time
import os
import html

logger = get_logger("BrowserManager")


def _run_osascript(script: str) -> str:
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
        return res.stdout.strip()
    except Exception as e:
        logger.error(f"osascript failed: {e}")
        return ""


def _open_new_tab(app_name: str, url: str):
    """Open url in a single tab of app_name.

    Reuses an empty/newtab if open in front window, or makes a new tab,
    or creates a new window with the URL if no windows exist.
    Falls back to `open -a` if osascript fails.
    """
    safe_url = url.replace('"', '\\"')
    script = f'''
    tell application "{app_name}"
      if (count of windows) = 0 then
        make new window with properties {{URL:"{safe_url}"}}
      else
        tell window 1
          set curURL to URL of active tab
          if curURL is "" or curURL starts with "chrome://newtab" or curURL starts with "brave://newtab" or curURL starts with "about:blank" then
            set URL of active tab to "{safe_url}"
          else
            make new tab with properties {{URL:"{safe_url}"}}
          end if
        end tell
      end if
      activate
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
        if res.returncode == 0:
            return
    except Exception:
        pass
    # Fallback: open via system launch services if AppleScript failed
    subprocess.run(["open", "-a", app_name, url], check=False)


def is_app_installed(app_name: str) -> bool:
    # Check common locations for the .app bundle
    candidates = [f"/Applications/{app_name}.app", os.path.expanduser(f"~/Applications/{app_name}.app")]
    for p in candidates:
        if os.path.exists(p):
            return True
    return False


def _run_cmd(cmd: list) -> str:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return res.stdout.strip()
    except Exception as e:
        logger.error(f"cmd failed: {e}")
        return ""


def _extract_hostname(url: str) -> str:
    try:
        p = urllib.parse.urlparse(url)
        host = p.hostname or ""
        # strip leading www.
        if host.startswith("www."):
            host = host[4:]
        return host.lower()
    except Exception:
        return ""


def _urls_meaningfully_different(existing_url: str, requested_url: str) -> bool:
    """Return True if requested_url differs from existing_url beyond hostname equality.

    If hostnames match but paths/queries differ, consider it meaningfully different so we navigate.
    """
    try:
        e = urllib.parse.urlparse(existing_url)
        r = urllib.parse.urlparse(requested_url)
        # If host differs, they are different
        if (e.hostname or "").lower() != (r.hostname or "").lower():
            return True
        # Normalize paths
        epath = e.path or "/"
        rpath = r.path or "/"
        if epath.rstrip('/') != rpath.rstrip('/'):
            return True
        # If queries differ, consider different
        if (e.query or "") != (r.query or ""):
            return True
        return False
    except Exception:
        return True


def _find_and_activate_tab_by_domain(app_name: str, target_url: str) -> tuple[bool, str]:
    """Enumerate tabs and activate the first tab whose hostname matches target_url's hostname.

    Returns (True, full_tab_url) if found and activated, otherwise (False, "").
    """
    target_host = _extract_hostname(target_url)
    if not target_host:
        return False, ""

    # Build AppleScript to enumerate windows/tabs and return window	tab	url lines
    script = f'''tell application "{app_name}"
  set out to ""
  repeat with wi from 1 to count windows
    set w to window wi
    repeat with ti from 1 to (count of tabs of w)
      try
        set theURL to URL of tab ti of w
      on error
        set theURL to ""
      end try
      set out to out & wi & "\t" & ti & "\t" & theURL & "\n"
    end repeat
  end repeat
  return out
end tell'''
    try:
        out = _run_cmd(["osascript", "-e", script])
        if not out:
            return False, ""
        lines = [l for l in out.splitlines() if l.strip()]
        for L in lines:
            parts = L.split('\t', 2)
            if len(parts) != 3:
                continue
            wi, ti, url = parts
            try:
                h = urllib.parse.urlparse(url).hostname or ''
                if h.startswith('www.'):
                    h = h[4:]
                if h.lower() == target_host.lower() or target_host.lower() in h.lower():
                    # Activate this tab explicitly
                    act = f'''tell application "{app_name}"
  tell window {wi} to set active tab index to {ti}
  set index of window {wi} to 1
  activate
end tell'''
                    _run_cmd(["osascript", "-e", act])
                    return True, url
            except Exception:
                continue
    except Exception:
        pass
    return False, ""


def open_or_reuse_tab(url: str, browser_pref: str, match_substring: str = None, js: str = None) -> bool:
    """Open URL in specified browser, reuse existing tab if match_substring present and found.

    browser_pref: 'chrome' or 'brave' or other
    match_substring: substring to look for in existing tabs (e.g., 'youtube.com')
    js: optional JavaScript to execute in the activated tab
    """
    app_name = "Google Chrome" if browser_pref == "chrome" else "Brave Browser"

    # Verify app installed
    if not is_app_installed(app_name):
        logger.error(f"Requested browser not installed: {app_name}")
        return False

    # Prefer to find existing tab by domain (robust hostname matching)
    try:
        match_target = match_substring
        if not match_target and url:
            try:
                parsed = urllib.parse.urlparse(url)
                host = parsed.hostname or ""
                match_target = host
            except Exception:
                match_target = None

        if match_target:
            target_for_match = match_target if str(match_target).startswith("http") else f"https://{match_target}"
            found = False
            existing_url = ""
            for _retry in range(2):
                found, existing_url = _find_and_activate_tab_by_domain(app_name, target_for_match)
                if found:
                    break
                time.sleep(0.1)
            if found:
                logger.info(f"Activated existing {app_name} tab matching domain {match_target}")
                if js:
                    exec_script = f'tell application "{app_name}" to tell front window to tell active tab to execute javascript "{js}"'
                    _run_cmd(["osascript", "-e", exec_script])
                # If requested URL differs meaningfully from existing tab URL, navigate it
                try:
                    if url and existing_url and _urls_meaningfully_different(existing_url, url):
                        safe_url = url.replace('"', '\\"')
                        nav_script = f'tell application "{app_name}" to tell front window to tell active tab to set URL to "{safe_url}"'
                        _run_cmd(["osascript", "-e", nav_script])
                except Exception:
                    pass
                return True

        # Not found: open tab
        _open_new_tab(app_name, url)
        time.sleep(0.3)
        if js:
            exec_script = f'tell application "{app_name}" to delay 0.3\n tell front window to tell active tab to execute javascript "{js}"'
            _run_cmd(["osascript", "-e", exec_script])
        return True
    except Exception as e:
        logger.error(f"Browser open_or_reuse_tab failed: {e}")
        try:
            subprocess.run(["open", "-a", app_name, url], check=False)
            return True
        except Exception as e2:
            logger.error(f"Fallback open failed: {e2}")
            return False


def execute_js_in_active_tab(app_name: str, js: str) -> str:
    """Execute JS in the active tab of app_name and return trimmed stdout."""
    if not is_app_installed(app_name):
        logger.error(f"execute_js: app not installed: {app_name}")
        return ""
    # Wrap JS to be a single-line string
    payload = js.replace('"', '\\"').replace('\n', ' ')
    script = f'tell application "{app_name}" to tell front window to tell active tab to execute javascript "{payload}"'
    return _run_cmd(["osascript", "-e", script])


def open_url(url: str, browser_pref: str, match_substring: str = None) -> bool:
    """Open or reuse a tab for the given URL in specified browser."""
    return open_or_reuse_tab(url, browser_pref, match_substring=match_substring, js=None)


def search_and_play_youtube(query: str) -> bool:
    """Search YouTube for query in Brave, reuse tab if present, then click first result."""
    browser_pref = "brave"
    app_name = "Brave Browser"
    if not is_app_installed(app_name):
        logger.error("Brave Browser not installed")
        return False

    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    opened = open_or_reuse_tab(search_url, browser_pref, match_substring="youtube.com")
    if not opened:
        return False

    click_js = (
        "(function(){var sels=['ytd-video-renderer a#thumbnail','a#video-title','ytd-rich-item-renderer a#video-title','ytd-video-renderer a#video-title'];"
        "for(var i=0;i<sels.length;i++){var el=document.querySelector(sels[i]); if(el){el.click(); return 'clicked';}} return 'notfound';})()"
    )

    for attempt in range(5):
        res = execute_js_in_active_tab(app_name, click_js)
        if res and 'clicked' in res.lower():
            logger.info("YouTube: clicked first result")
            return True
        time.sleep(0.6)

    logger.error("YouTube: failed to click first result")
    return False


def search_and_play_spotify(query: str) -> bool:
    """Search Spotify web player in Brave and attempt to play the first result."""
    browser_pref = "brave"
    app_name = "Brave Browser"
    if not is_app_installed(app_name):
        logger.error("Brave Browser not installed")
        return False

    search_url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
    opened = open_or_reuse_tab(search_url, browser_pref, match_substring="open.spotify.com")
    if not opened:
        return False

    nav_js = """(function(){var a=document.querySelector('a[href*="/track/"]'); if(a){window.location=a.href; return 'navigated';} return 'notfound';})()"""
    time.sleep(0.6)
    res = execute_js_in_active_tab(app_name, nav_js)
    if res and 'navigated' in res.lower():
        time.sleep(0.6)
        play_js = """(function(){var sels=['button[aria-label^="Play"]','button[aria-label*="Play"]','button[data-testid="play-button"]','button[class*="play"]','div[role=button][aria-label*="Play"]'];for(var i=0;i<sels.length;i++){try{var el=document.querySelector(sels[i]); if(el){el.click(); return 'clicked';}}catch(e){} } return 'notfound';})()"""
        for _ in range(6):
            p = execute_js_in_active_tab(app_name, play_js)
            if p and 'clicked' in p.lower():
                logger.info("Spotify: play clicked on track page")
                time.sleep(0.6)
                if _verify_spotify_playback(app_name):
                    return True
                else:
                    logger.info("Spotify: play clicked but playback not detected")
                    return False
            time.sleep(0.6)

    click_js = """(function(){var row=document.querySelector('div[role="row"] a[href*="/track/"]'); if(row){row.click(); return 'clicked';} var a=document.querySelector('a[href*="/track/"]'); if(a){a.click(); return 'clicked';} return 'notfound';})()"""
    for attempt in range(6):
        res2 = execute_js_in_active_tab(app_name, click_js)
        if res2 and 'clicked' in res2.lower():
            logger.info("Spotify: clicked track link")
            time.sleep(0.6)
            play_js_2 = """(function(){var b=document.querySelector('button[aria-label^="Play"]'); if(b){b.click(); return 'clicked';} return 'notfound';})()"""
            p2 = execute_js_in_active_tab(app_name, play_js_2)
            if p2 and 'clicked' in p2.lower():
                time.sleep(0.6)
                if _verify_spotify_playback(app_name):
                    return True
                else:
                    logger.info("Spotify: clicked play but playback not detected")
                    return False
        time.sleep(0.6)

    logger.error("Spotify: failed to find or play track via web player")
    return False


def _verify_spotify_playback(app_name: str) -> bool:
    """Attempt to verify playback state on Spotify web player by inspecting DOM."""
    try:
        pause_js = '''(function(){var p=document.querySelector('button[aria-label^="Pause"]'); if(p) return 'pause'; var pp=document.querySelector('button[class*="pause"]'); if(pp) return 'pause'; return 'none';})()'''
        res = execute_js_in_active_tab(app_name, pause_js)
        if res and 'pause' in res.lower():
            logger.info("Spotify: detected pause button — playback active")
            return True

        prog_js = '''(function(){var el=document.querySelector('[role="progressbar"]'); if(!el) return 'none'; var val=el.getAttribute('aria-valuenow'); if(val) return 'progress:'+val; return 'none';})()'''
        pres = execute_js_in_active_tab(app_name, prog_js)
        if pres and 'progress:' in pres.lower():
            logger.info("Spotify: detected progress bar — playback active")
            return True

        url_js = '''(function(){return window.location.href})()'''
        cur = execute_js_in_active_tab(app_name, url_js)
        if cur and '/track/' in cur:
            logger.info("Spotify: URL indicates track page — may be playing")
            playing_js = '''(function(){var el=document.querySelector('[data-testid=\'play-button\']'); if(el && el.getAttribute('aria-pressed')=='true') return 'playing'; return 'no';})()'''
            pp = execute_js_in_active_tab(app_name, playing_js)
            if pp and 'playing' in pp.lower():
                return True

        return False
    except Exception as e:
        logger.error(f"Playback verification failed: {e}")
        return False


def play_youtube_watch(url: str, browser_pref: str = "brave") -> tuple[bool, str]:
    """Open a YouTube watch URL in the given browser, attempt to start playback,
    and verify playback state. Returns (success, status_message).
    """
    app_name = "Google Chrome" if browser_pref == "chrome" else "Brave Browser"
    if not is_app_installed(app_name):
        logger.error(f"Requested browser not installed: {app_name}")
        return False, "browser_not_installed"

    opened = open_or_reuse_tab(url, browser_pref, match_substring="youtube.com/watch")
    if not opened:
        return False, "open_failed"

    play_js = '''(function(){try{var v=document.querySelector('video'); if(!v){return 'no_video';} v.play(); return JSON.stringify({paused:v.paused, currentTime: v.currentTime});}catch(e){return 'error:'+e.toString();}})()'''

    for attempt in range(6):
        res = execute_js_in_active_tab(app_name, play_js)
        if not res:
            time.sleep(0.6)
            continue
        r = res.strip()
        if r.startswith('no_video'):
            logger.debug("YouTube: no video element found yet")
            time.sleep(0.6)
            continue
        if r.startswith('error:'):
            logger.debug(f"YouTube play attempt error: {r}")
            time.sleep(0.6)
            continue
        try:
            if r.startswith('{'):
                import json
                info = json.loads(r)
                paused = info.get('paused')
                current = float(info.get('currentTime', 0) or 0)
                if paused is False and current > 0:
                    logger.info("YouTube: playback verified via video element")
                    return True, "playing"
                else:
                    logger.debug(f"YouTube: video present but paused={paused} current={current}")
                    click_js = "(function(){var btn=document.querySelector('button.ytp-large-play-button'); if(btn){btn.click(); return 'clicked';} var v=document.querySelector('video'); if(v){v.play(); return 'played';} return 'no_trigger';})()"
                    execute_js_in_active_tab(app_name, click_js)
                    time.sleep(0.6)
            else:
                time.sleep(0.6)
        except Exception as e:
            logger.debug(f"YouTube: parse/playback check failed: {e}")
            time.sleep(0.6)

    check_js = "(function(){var v=document.querySelector('video'); if(!v) return 'no_video'; return JSON.stringify({paused:v.paused, currentTime:v.currentTime});})()"
    final = execute_js_in_active_tab(app_name, check_js)
    if final and final.startswith('{'):
        try:
            import json
            info = json.loads(final)
            paused = info.get('paused')
            current = float(info.get('currentTime', 0) or 0)
            if paused is False and current > 0:
                logger.info("YouTube: final check indicates playback")
                return True, "playing"
        except Exception:
            pass

    logger.info("YouTube: playback not detected after attempts")
    return False, "playback_blocked_or_not_started"
