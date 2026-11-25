"""Runtime operating mode and cloud-fallback policy for Friday."""

import os
import socket


def get_mode() -> str:
    mode = os.getenv("FRIDAY_MODE", "auto").strip().lower()
    if mode in ("offline", "online", "auto"):
        return mode
    return "auto"


def is_offline_mode() -> bool:
    return get_mode() == "offline"


def cloud_fallback_allowed() -> bool:
    if is_offline_mode():
        return False
    return os.getenv("ALLOW_CLOUD_FALLBACK", "false").strip().lower() in ("1", "true", "yes")


def check_connectivity(host: str = "1.1.1.1", port: int = 53, timeout: float = 1.5) -> bool:
    """Check internet connectivity; never probes external hosts in offline mode."""
    if is_offline_mode():
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
