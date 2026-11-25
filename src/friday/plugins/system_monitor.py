import psutil

def can_handle(text):
    keywords = ["system status", "cpu", "ram", "disk"]
    return any(k in text.lower() for k in keywords)

def run(command):
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return (f"System Status:\n"
                f"CPU Usage: {cpu}%\n"
                f"RAM Usage: {ram.percent}% ({ram.used // (1024**3)}GB / {ram.total // (1024**3)}GB)\n"
                f"Disk Usage: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)")
    except Exception as e:
        return f"Error retrieving system status: {str(e)}"
