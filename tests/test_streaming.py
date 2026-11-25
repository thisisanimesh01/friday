import json
from unittest.mock import MagicMock

import brain
import requests


def test_ask_friday_stream_success(monkeypatch):
    monkeypatch.setattr(brain, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(brain, "OLLAMA_BASE_URL", "http://localhost:11434")

    chunks = [
        json.dumps({"message": {"content": "Hello"}}).encode("utf-8"),
        json.dumps({"message": {"content": " boss!"}}).encode("utf-8"),
        json.dumps({"done": True}).encode("utf-8"),
    ]

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.iter_lines.return_value = chunks
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: mock_resp)

    streamed = list(brain.ask_friday_stream("hi"))
    assert "".join(streamed) == "Hello boss!"


def test_ask_friday_stream_fallback_offline(monkeypatch):
    monkeypatch.setattr(brain, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(brain, "OLLAMA_STRICT_OFFLINE", True)
    monkeypatch.setattr(brain, "retrieve_memory", lambda p: [("1", "hi", "I remember you.")])

    def fail_post(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, "post", fail_post)
    streamed = list(brain.ask_friday_stream("hi"))
    assert any("I'm offline" in s for s in streamed)


def test_ask_friday_stream_cancellation(monkeypatch):
    monkeypatch.setattr(brain, "LLM_PROVIDER", "ollama")

    def infinite_chunks():
        yield json.dumps({"message": {"content": "Token 1"}}).encode("utf-8")
        raise KeyboardInterrupt()

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.iter_lines.return_value = infinite_chunks()
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: mock_resp)

    # Calling generator should stop on KeyboardInterrupt cleanly when consumed
    gen = brain.ask_friday_stream("test")
    first_token = next(gen)
    assert first_token == "Token 1"
    try:
        next(gen)
    except KeyboardInterrupt:
        pass  # cancellation caught
