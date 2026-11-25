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

* **Security:** Never commit `.env`, `memory.db`, or `friday.log`. File operations are restricted to `~/Desktop/friday_workspace` via `security/path_validator.py`.

---

## Roadmap

* **Completed (Phase 1):** Repository hygiene, packaging (`pyproject.toml`, `LICENSE`), error-handling hardening, offline `pytest` + 3-job CI, `src/friday/` package restructuring, CLI & README polish.
* **Planned (Phase 2–4):** Ollama validation & optimization, Hinata-inspired voice TTS pipeline, and final integration/release.

---

## Contributing

1. Open an issue using the **Bug Report** or **Feature Request** template.
2. Create a feature branch (`git checkout -b feat/your-feature`).
3. Ensure `pytest`, `ruff check tests/`, and `python3 -m compileall -q .` pass.
4. Open a Pull Request referencing your issue (`Closes #<id>`).
