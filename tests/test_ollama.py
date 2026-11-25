from unittest.mock import MagicMock

import llm_router
import requests


def test_ollama_router_success(monkeypatch):
    monkeypatch.setattr(llm_router, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(llm_router, "OLLAMA_STRICT_OFFLINE", True)

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "message": {"content": '{"intent": "get_weather", "args": {"location": "tokyo"}}'}
    }
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: mock_resp)

    res = llm_router.route_command("how is the sky in tokyo")
    assert res["intent"] == "get_weather"
    assert res["args"]["location"] == "tokyo"


def test_ollama_router_strict_offline_skips_cloud(monkeypatch):
    monkeypatch.setattr(llm_router, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(llm_router, "OLLAMA_STRICT_OFFLINE", True)
    monkeypatch.setattr(llm_router, "GEMINI_API_KEY", "fake-key")

    def fail_post(*args, **kwargs):
        raise requests.Timeout("timed out")

    monkeypatch.setattr(requests, "post", fail_post)

    res = llm_router.route_command("tell me something interesting")
    assert res["intent"] == "chat"


def test_ollama_router_malformed_json_falls_back(monkeypatch):
    monkeypatch.setattr(llm_router, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(llm_router, "OLLAMA_STRICT_OFFLINE", True)

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"message": {"content": "not valid json"}}
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: mock_resp)

    res = llm_router.route_command("tell me something interesting")
    assert res["intent"] == "chat"
