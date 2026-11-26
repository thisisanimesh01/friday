import sys
from types import ModuleType
from unittest.mock import MagicMock

import requests

from friday import runtime_mode

# Stub heavy optional dependencies (numpy, supabase) for lightweight CI
if "memory.memory_manager" not in sys.modules:
    try:
        from memory import memory_manager as _mm
    except Exception:
        _mm = ModuleType("memory.memory_manager")
        _mm.store_memory = MagicMock()
        _mm.retrieve_memory = MagicMock(return_value=[])
        sys.modules["memory.memory_manager"] = _mm

if "memory.supabase" not in sys.modules:
    _sb = ModuleType("memory.supabase")
    _sb.save_cloud = MagicMock()
    sys.modules["memory.supabase"] = _sb

import commands  # noqa: E402
from memory import sync  # noqa: E402


def test_validate_local_ollama_url():
    assert runtime_mode.validate_local_ollama_url("http://localhost:11434") is True
    assert runtime_mode.validate_local_ollama_url("http://127.0.0.1:11434") is True
    assert runtime_mode.validate_local_ollama_url("http://[::1]:11434") is True
    assert runtime_mode.validate_local_ollama_url("https://api.openai.com/v1") is False
    assert runtime_mode.validate_local_ollama_url("http://192.168.1.50:11434") is False


def test_memory_sync_blocked_in_offline_mode(monkeypatch):
    monkeypatch.setenv("FRIDAY_MODE", "offline")

    def fail_get(*args, **kwargs):
        raise AssertionError("External network probe must not run in offline mode")

    monkeypatch.setattr(requests, "get", fail_get)
    assert sync.is_online() is False
    assert sync.sync() is None


def test_online_commands_blocked_in_offline_mode(monkeypatch):
    monkeypatch.setenv("FRIDAY_MODE", "offline")
    for cmd in ("weather in tokyo", "latest news", "my location", "play lofi on youtube"):
        res = commands.execute_command(cmd)
        assert "offline mode" in res.lower()
