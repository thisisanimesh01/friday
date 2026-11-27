# Friday

[![Friday CI](https://github.com/thisisanimesh01/friday/actions/workflows/ci.yml/badge.svg)](https://github.com/thisisanimesh01/friday/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A modular AI-powered terminal assistant that remembers context, routes deterministic and LLM-backed commands, automates browser workflows, and protects local file operations.

---

## Implemented Features

- **Hybrid Command & Intent Routing:** Deterministic pattern matching for URLs, media, files, time/weather/news, with LLM intent classification fallback.
- **Multi-Provider LLM Support:** Supports local **Ollama** (`LLM_PROVIDER=ollama`), **Groq**, **Gemini**, and **DeepSeek** with automatic fallback.
- **Persistent Memory:** Local SQLite conversation storage with semantic retrieval and rolling summarization, plus optional Supabase sync.
- **Sandboxed File Operations:** Workspace-scoped file/folder management with path traversal protection, symlink blocking, and `.trash` recovery.
- **Browser & Plugin Automation:** Brave/Chrome routing, YouTube/Spotify playback, and dynamic plugin loading (`github_plugin`, `spotify_plugin`, `system_monitor`).
- **CLI Interface:** `argparse`-based CLI (`--help`, `--version`, `--debug`, `--provider`) via `friday` or `python3 main.py`.

---

## Architecture

```text
User Terminal (friday / python3 main.py)
        │
        ▼
  CLI & App Loop (src/friday/cli.py -> src/friday/app.py)
        │
        ├──► Deterministic & LLM Router (llm_router.py / intent_parser.py)
        │         ├──► Commands & Browser (commands.py / browser_manager.py)
        │         ├──► Plugins (plugin_loader.py / plugins/)
        │         └──► Sandboxed Files & Security (sandbox/ / security/)
        │
        └──► Conversational Brain & Memory (brain.py / memory/)
```

---

## Installation & Configuration

```bash
# 1. Clone the repository
git clone https://github.com/thisisanimesh01/friday.git
cd friday

# 2. Create & activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies (or editable package)
pip install -r requirements.txt
pip install -e .

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your API keys or local Ollama settings
```

### Key Environment Variables (`.env`)

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | Primary provider (`auto`, `ollama`, `groq`, `gemini`, `deepseek`) | `ollama` |
| `OLLAMA_BASE_URL` | Local Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Local Ollama model name | `llama3.2` |
| `GROQ_API` | Groq API key (optional cloud fallback) | — |
| `GEMINI_API` | Gemini API key (optional cloud fallback) | — |

---

## CLI Usage

```bash
# Show help and available flags (no API keys required)
python3 main.py --help

# Show version
python3 main.py --version

# Run with local Ollama and debug logging
python3 main.py --provider ollama --debug

# Or use the installed package entry point
friday --provider ollama
```

---

## Project Structure

```text
friday/
├── .github/                # Issue/PR templates & 3-job CI workflow
├── src/friday/             # Core package
│   ├── __init__.py
│   ├── app.py              # Main interactive loop
│   ├── cli.py              # argparse CLI entry point
│   ├── brain.py            # Conversational LLM & fallback
│   ├── llm_router.py       # Hybrid deterministic + LLM router
│   ├── memory/             # SQLite, embeddings & Supabase sync
│   ├── plugins/            # Dynamic plugins
│   ├── sandbox/            # Safe file & trash operations
│   └── security/           # Path validation & permission guards
├── tests/                  # Offline pytest unit suite
├── main.py                 # Backward-compatible root entry point
├── pyproject.toml          # Packaging, pytest & ruff config
├── requirements.txt        # Runtime dependencies
├── CHANGELOG.md            # Release & milestone history
└── LICENSE                 # MIT License
```

---

## Testing & Security

```bash
# Run unit tests (offline, all external APIs mocked)
pytest

# Run linter on tests
ruff check tests/

# Verify Python syntax
python3 -m compileall -q .
```

* **Security:** Never commit `.env`, `memory.db`, or `friday.log`. File operations and media are strictly confined to `~/Desktop/friday workspace/` via `security/privacy_guard.py`. The folder `~/Desktop/me and she/` and macOS personal data repositories are permanently blocked under deny-by-default rules.

---

## Master Roadmap

* **Phase 1 — Engineering Foundation:** Completed (Repository hygiene, packaging, error handling, unit tests, restructured package, CLI).
* **Phase 2 — Hybrid AI Intelligence:** Completed (Local Ollama integration, hybrid router, streaming responses, offline privacy).
* **Phase 3 — Hearing & Voice Input:** Completed (Microphone capture, local Whisper STT, Hey Friday wake word, continuous listening).
* **Phase 4 — Hinata Voice & Speech Output:** Completed (Local TTS, voice model feasibility, voice profile tuning, streaming speech, hands-free conversation).
* **Phase 5 — Personality & Advanced Memory:** Completed (Personality consistency, terminal-only architecture, Hinata neural voice at 1.14x, contextual memory, intelligent personalization, memory privacy & management).
* **Phase 6 — macOS Control & Automation:**
  - **Milestone 6.1:** macOS Control Foundation & Permission Framework — **Completed**.
  - **Milestone 6.2:** Application Management, Window Control & Privacy Protection — **Completed**.
  - **Milestone 6.2.1:** Privacy Hardening & Real-World Validation — **Completed**.
  - **Milestone 6.3:** AppleScript & Shortcuts Automation — **Completed**.
  - **Milestone 6.4:** System Settings & Audio/Display Controls — **Completed**.
  - **Milestone 6.5:** Multi-Step Desktop Workflows — **Completed**.
* **Phase 7 — Vision & Screen Awareness:**
  - **Milestone 7.1:** Screen Capture Foundation & Permission Hardening — **Completed**.
  - **Milestone 7.2:** Local OCR & Text Extraction Engine — **Completed**.
  - **Milestone 7.3:** Active Window Awareness & Desktop Context — **Completed**.
  - **Milestone 7.4:** Visual Document Understanding — **Completed**.
  - **Milestone 7.5:** Vision Privacy, Redaction & Real-World Validation.
* **Phase 8 — Online Intelligence & Plugins:** Internet tool improvements, web research, browser automation, productivity plugins.
* **Phase 9 — Personal Developer Assistant:** Project workspace awareness, code analysis & debugging, Git/GitHub assistance, safe terminal execution.
* **Phase 10 — Proactive Intelligence:** Calendar & reminders, morning briefings, system monitoring, scheduled background service.
* **Phase 11 — Terminal Experience & System Integration:** Advanced terminal presentation, live voice & system indicators, command shortcuts & history, terminal diagnostics, CLI configuration, optional launch-at-login.
* **Phase 12 — Final Integration & Release:** End-to-end integration, full security & privacy audit, performance optimization, v3.0 stable release.

---

## Contributing

1. Open an issue using the **Bug Report** or **Feature Request** template.
2. Create a feature branch (`git checkout -b feat/your-feature`).
3. Ensure `pytest`, `ruff check tests/`, and `python3 -m compileall -q .` pass.
4. Open a Pull Request referencing your issue (`Closes #<id>`).
