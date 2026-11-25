"""Reproducible local Ollama benchmark for Friday."""

import json
import os
import statistics
import time
import urllib.request
from typing import Any

DEFAULT_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

INTENT_PROMPTS = [
    ("what is the weather in tokyo", "get_weather"),
    ("play lofi beats on youtube", "play_youtube"),
    ("create file notes.txt", "create_file"),
    ("tell me a joke about robots", "chat"),
]

CHAT_PROMPTS = [
    "In one sentence, introduce yourself as Friday.",
    "Write a Python one-liner to reverse a string.",
    "What is 15 * 12?",
]


def query_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_URL,
    json_mode: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    elapsed = time.perf_counter() - t0
    eval_count = data.get("eval_count", 0)
    eval_dur_ns = data.get("eval_duration", 0)
    tps = (eval_count / (eval_dur_ns / 1e9)) if eval_dur_ns else 0.0
    return {
        "content": data.get("message", {}).get("content", ""),
        "elapsed_s": elapsed,
        "eval_count": eval_count,
        "tokens_per_sec": tps,
    }


def run_benchmark(model: str = DEFAULT_MODEL, base_url: str = DEFAULT_URL) -> dict[str, Any]:
    cold = query_ollama("Say hello in 5 words.", model=model, base_url=base_url)
    warm_latencies = []
    tps_values = []
    for p in CHAT_PROMPTS:
        r = query_ollama(p, model=model, base_url=base_url)
        warm_latencies.append(r["elapsed_s"])
        if r["tokens_per_sec"] > 0:
            tps_values.append(r["tokens_per_sec"])

    valid_json = 0
    for text, _ in INTENT_PROMPTS:
        r = query_ollama(
            f'Classify intent as JSON {{"intent": "..."}} for: {text}',
            model=model,
            base_url=base_url,
            json_mode=True,
        )
        try:
            parsed = json.loads(r["content"])
            if isinstance(parsed, dict) and "intent" in parsed:
                valid_json += 1
        except json.JSONDecodeError:
            pass

    return {
        "model": model,
        "cold_start_s": round(cold["elapsed_s"], 3),
        "warm_median_s": round(statistics.median(warm_latencies), 3),
        "warm_min_s": round(min(warm_latencies), 3),
        "warm_max_s": round(max(warm_latencies), 3),
        "median_tps": round(statistics.median(tps_values), 2) if tps_values else 0.0,
        "valid_json_rate": f"{valid_json}/{len(INTENT_PROMPTS)}",
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2))
