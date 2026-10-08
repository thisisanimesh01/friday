import logging
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), 'friday.log')

# Formatter used for both file and console (console will be filtered)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# File handler: records everything for debugging
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Console handler: show clean output, but filter noisy httpx/httpcore/urllib3 logs
class ExcludeHttpFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        name = record.name or ""
        # Suppress logs from HTTP libraries in console output
        if name.startswith("httpx") or name.startswith("httpcore") or name.startswith("urllib3"):
            return False
        return True

console_handler = logging.StreamHandler()
# Only show warnings and errors in the console to keep the UI minimal and professional.
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)
console_handler.addFilter(ExcludeHttpFilter())

# Configure root logger: file handler receives all logs, console gets filtered view
root = logging.getLogger()
root.setLevel(logging.INFO)
# Clear existing handlers (if any) and attach our handlers
root.handlers = []
root.addHandler(file_handler)
root.addHandler(console_handler)

def get_logger(name: str):
    """Return a named logger that propagates to the root handlers.

    Do not attach per-logger handlers here so that the central filters
    and file routing remain consistent.
    """
    l = logging.getLogger(name)
    l.setLevel(logging.INFO)
    l.propagate = True
    return l
