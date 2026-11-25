# Friday v2

> A modular AI-powered terminal assistant that remembers, automates, browses, and gets things done.

Friday is a command-driven personal AI assistant built with Python. It combines deterministic command routing, LLM-powered conversation, persistent memory, browser automation, plugins, system utilities, and a security layer into a single terminal-based assistant.

---

## ✨ What's New in v2.1

Friday v2.1 focuses on making the assistant more reliable and practical for everyday use.

### 🚀 Major Improvements

- Intelligent command routing
- Explicit URL detection and routing
- Browser tab reuse
- Google/Gmail domain separation
- Brave and Chrome browser routing
- YouTube search and playback
- Spotify Web Player search and playback
- GitHub browser navigation
- Dynamic plugin loading
- Persistent SQLite memory
- Conversation summarization
- LLM provider fallback
- Secure file operations
- Permission and danger protection
- Improved error handling
- Local fallback for common commands
- Project-root based path handling
- Safer repository configuration

---

# 🧠 Architecture

```text
                    ┌──────────────────┐
                    │      User        │
                    │    Terminal      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Command Input  │
                    └────────┬─────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │ Command / Intent      │
                 │      Router           │
                 └──────────┬────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
   │ Deterministic│   │     LLM     │   │   Plugins   │
   │   Commands   │   │   Routing   │   │   System    │
   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                            ▼
                 ┌───────────────────────┐
                 │      Actions          │
                 │ Browser / Files /     │
                 │ System / APIs / etc.  │
                 └──────────┬────────────┘
                            │
                            ▼
                 ┌───────────────────────┐
                 │    Memory System      │
                 │ SQLite + Context      │
                 └───────────────────────┘
```

---

## ⚙️ Setup & Installation

```bash
# 1. Clone the repository
git clone https://github.com/thisisanimesh01/friday.git
cd friday

# 2. Create & activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Add your API keys (GROQ_API, GEMINI_API, etc.) to .env

# 5. Run Friday
python3 main.py
```

---

## 🤝 Contributing

1. Check open issues or create a new one using the **Bug Report** or **Feature Request** template.
2. Create a feature branch (`git checkout -b feat/your-feature`).
3. Commit your changes and open a Pull Request using the PR template.
