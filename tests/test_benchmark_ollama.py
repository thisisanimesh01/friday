import json
import urllib.request
from unittest.mock import MagicMock

from scripts import benchmark_ollama


def test_run_benchmark_mocked(monkeypatch):
    payload = json.dumps({
        "message": {"content": '{"intent": "chat"}'},
        "eval_count": 20,
        "eval_duration": 1_000_000_000,
    }).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False

    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: mock_resp)

    results = benchmark_ollama.run_benchmark(model="qwen2.5:3b", base_url="http://localhost:11434")
    assert results["model"] == "qwen2.5:3b"
    assert results["median_tps"] == 20.0
    assert results["valid_json_rate"] == "4/4"
