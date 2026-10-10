"""
logger.py — Centralized logging for Friday.

Terminal:  WARNING and above only (no httpx/groq/urllib3 noise).
friday.log: Everything from INFO and above (full debug trail).

Usage:
    from logger import get_logger
    logger = get_logger("MyModule")
    logger.info("Something happened")
"""

import logging
import os

# ── File path (always relative to this file's directory = project root) ───────
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "friday.log")

# ── Shared formatter ───────────────────────────────────────────────────────────
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# ── File handler: full INFO+ log for debugging ────────────────────────────────
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# ── Console filter: block noisy HTTP/SDK libraries ────────────────────────────
_NOISY_PREFIXES = (
    "httpx", "httpcore", "urllib3", "groq", "requests",
    "sentence_transformers", "transformers", "huggingface_hub",
    "filelock", "asyncio",
)

class _SilenceNoisyLibs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        name = record.name or ""
        return not any(name.startswith(p) for p in _NOISY_PREFIXES)

# ── Console handler: WARNING+ only, without HTTP library chatter ──────────────
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)
console_handler.addFilter(_SilenceNoisyLibs())

# ── Root logger ───────────────────────────────────────────────────────────────
root = logging.getLogger()
root.setLevel(logging.INFO)
root.handlers.clear()
root.addHandler(file_handler)
root.addHandler(console_handler)

# ── Explicitly silence known noisy loggers at source ─────────────────────────
for _noisy in _NOISY_PREFIXES:
    logging.getLogger(_noisy).setLevel(logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger that propagates to the root handlers."""
    l = logging.getLogger(name)
    l.setLevel(logging.INFO)
    l.propagate = True
    return l
