"""Benchmark personality prompt overhead, token count, latency, and memory footprint.

Compares:
1. Baseline System Prompt (previous ad-hoc 175-word multi-role prompt)
2. New Compact Centralized Friday Personality Prompt
Across:
- Character and word count (token proxy)
- Context overhead
- Time-to-first-token (TTFT) and total generation time (via local Ollama qwen2.5:3b)
- Process peak memory and system resource impact
"""

import os
import sys
import time
import requests
import psutil

# Ensure src is in pythonpath
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from friday.personality.prompts import build_personality_system_prompt

BASELINE_PROMPT = (
    "you are a female AI assistant named Friday. "
    "You are Friday, a highly intelligent personal AI assistant like Jarvis. "
    "You are friendly, calm, slightly witty, emotionally aware, and supportive. "
    "You speak like a human, not a robot. "
    "You can help with tasks, answer questions, and have engaging conversations. "
    "You are not just an assistant, but a companion who understands and cares about the user. "
    "Keep responses natural, short, and engaging. "
    "You can show light humor, care, and personality. "
    "Address the user like a friend. "
    "You remember things about the user. "
    "Avoid long structured lists unless necessary. "
    "Avoid saying 'you want to' regularly in conversations. "
    "Talk in Hinglish sometimes. "
    "Don't always start the converstation with Sir or Boss. Use it occasionally. "
    "Call the user 'boss' or 'sir' occasionally."
)

NEW_PROMPT = build_personality_system_prompt()

TEST_USER_PROMPTS = [
    "Who are you?",
    "Good morning, Friday.",
    "Can you explain Python list comprehension simply in one sentence?",
    "Friday, mere project ka status check karo.",
]

def run_ollama_benchmark(system_prompt: str, user_prompt: str, model: str = "qwen2.5:3b", base_url: str = "http://localhost:11434"):
    url = f"{base_url}/api/chat"
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": True,
        "options": {
            "num_ctx": 2048,
        }
    }
    
    t0 = time.time()
    ttft = None
    first_token_time = None
    chunks = []
    
    try:
        res = requests.post(url, json=data, timeout=30, stream=True)
        res.raise_for_status()
        for line in res.iter_lines():
            if not line:
                continue
            if ttft is None:
                ttft = time.time() - t0
            import json
            chunk = json.loads(line.decode("utf-8"))
            content = chunk.get("message", {}).get("content", "")
            if content:
                chunks.append(content)
            if chunk.get("done", False):
                break
        total_time = time.time() - t0
        full_response = "".join(chunks)
        return {
            "ttft_s": ttft or total_time,
            "total_time_s": total_time,
            "response_len": len(full_response),
            "tokens_est": len(full_response.split()),
            "success": True,
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

def main():
    print("=" * 70)
    print("FRIDAY Personality Prompt Benchmark (Milestone 5.1)")
    print("=" * 70)
    
    print("\n1. Prompt Footprint Comparison:")
    baseline_words = len(BASELINE_PROMPT.split())
    baseline_chars = len(BASELINE_PROMPT)
    new_words = len(NEW_PROMPT.split())
    new_chars = len(NEW_PROMPT)
    
    print(f"  Baseline Prompt: {baseline_words} words | {baseline_chars} characters (~{int(baseline_words * 1.3)} tokens)")
    print(f"  New Friday Prompt: {new_words} words | {new_chars} characters (~{int(new_words * 1.3)} tokens)")
    reduction_pct = ((baseline_words - new_words) / baseline_words) * 100
    print(f"  Prompt Reduction: {reduction_pct:.1f}% more compact\n")
    
    process = psutil.Process()
    mem_before = process.memory_info().rss / (1024 * 1024)
    print(f"  Process Memory RSS: {mem_before:.2f} MB")
    
    print("\n2. Live Ollama Generation Benchmark (qwen2.5:3b):")
    print("-" * 70)
    for q in TEST_USER_PROMPTS:
        print(f"\nPrompt: '{q}'")
        res_base = run_ollama_benchmark(BASELINE_PROMPT, q)
        res_new = run_ollama_benchmark(NEW_PROMPT, q)
        
        if res_base["success"] and res_new["success"]:
            print(f"  Baseline -> TTFT: {res_base['ttft_s']:.3f}s | Total: {res_base['total_time_s']:.3f}s | Words: {res_base['tokens_est']}")
            print(f"  New      -> TTFT: {res_new['ttft_s']:.3f}s | Total: {res_new['total_time_s']:.3f}s | Words: {res_new['tokens_est']}")
        else:
            print(f"  Ollama query skipped or offline: {res_base.get('error') or res_new.get('error')}")
            
    mem_after = process.memory_info().rss / (1024 * 1024)
    print(f"\n  Final Process Memory RSS: {mem_after:.2f} MB (Delta: {mem_after - mem_before:+.2f} MB)")
    print("=" * 70)

if __name__ == "__main__":
    main()
