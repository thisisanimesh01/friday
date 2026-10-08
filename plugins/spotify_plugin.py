def can_handle(text):
    text_lower = text.lower()
    if "youtube" in text_lower:
        return False
    keywords = ["spotify", "play music", "play song", "pause music", "pause song", "skip song", "next song", "previous song", "resume music"]
    return any(k in text_lower for k in keywords)

def run(command):
    command_lower = command.lower()
    
    # Simple mocked or terminal-based spotify control using applescript (since the user is on Mac)
    import subprocess
    
    if "play" in command_lower and "song" not in command_lower and len(command_lower.split("play")) > 1:
        # Just tell spotify to play in general
        script = 'tell application "Spotify" to play'
    elif "pause" in command_lower or "stop" in command_lower:
        script = 'tell application "Spotify" to pause'
    elif "skip" in command_lower or "next" in command_lower:
        script = 'tell application "Spotify" to next track'
    elif "previous" in command_lower:
        script = 'tell application "Spotify" to previous track'
    else:
        script = 'tell application "Spotify" to play'

    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        return "I've sent the command to Spotify."
    except Exception as e:
        return f"Couldn't control Spotify. Make sure it is open. Error: {str(e)}"
