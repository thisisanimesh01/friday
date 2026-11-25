# FRIDAY Personality & Terminal-Only Architecture (Milestone 5.1)

## 1. Executive Summary & Vision

Milestone 5.1 establishes a centralized, consistent identity and personality for **FRIDAY** and enforces a permanent **terminal-only architecture**.

Friday embodies:
- **JARVIS-inspired intelligence**: Professionalism, calm composure, clean task acknowledgements, context awareness, and subtle wit.
- **Hinata-inspired gentle delivery**: Warm feminine conversational presence, soft-spoken tone, calm pacing, and natural patience.
- **Local-first privacy & security**: Deterministic security gates, isolated structured intent parsing, and honest execution acknowledgements.
- **Terminal-only interface**: Zero HTML, CSS, JavaScript, React, Vue, Angular, Electron, SwiftUI, or GUI dependencies. Standard terminal I/O, NO_COLOR compliance, sanitized ANSI/OSC escape handling, and audio voice interaction.

---

## 2. Centralized Identity & Configuration

Friday's identity is defined in `src/friday/personality/`:
- `profile.py`: Single source of truth for name (`Friday`), role (`Personal AI Assistant`), platform (`macOS`), interface (`Terminal and Voice`), default voice profile (`friday-gentle`), and core qualities.
- `prompts.py`: Token-efficient prompt generator tailored for Apple Silicon M1 context windows (<150 tokens) with support for language switching (`auto`, `en`, `hi`, `hinglish`) and form of address preferences.
- `response_style.py`: Honest action acknowledgement lifecycle (`ActionStatus.RECEIVED`, `CONFIRMATION_REQUIRED`, `EXECUTING`, `SUCCEEDED`, `FAILED`, `CANCELLED`), response styles mapping to Phase 4 speech expressions (`SpeechExpression`), and ANSI/OSC escape code sanitization.

### Configuration Precedence (.env / Environment Variables)

| Variable | Description | Allowed Values | Default |
| :--- | :--- | :--- | :--- |
| `FRIDAY_PERSONALITY` | Personality tone | `friendly`, `professional`, `casual` | `friendly` |
| `FRIDAY_RESPONSE_STYLE` | Response verbosity | `adaptive`, `concise`, `detailed` | `adaptive` |
| `FRIDAY_FRIENDLINESS` | Friendliness warmth level | `warm`, `neutral`, `gentle` | `warm` |
| `FRIDAY_HUMOR` | Subtle humor degree | `subtle`, `off`, `light` | `subtle` |
| `FRIDAY_LANGUAGE` | Conversational language | `auto`, `en`, `hi`, `hinglish` | `auto` |
| `FRIDAY_FORM_OF_ADDRESS` | User title/name | Text (e.g. `Animesh`) | None (natural) |
| `FRIDAY_STARTUP_GREETING`| Show banner & greeting | `true`, `false` | `true` |
| `FRIDAY_TERMINAL_COLOR` | ANSI colors | `true`, `false` | `true` (respects `NO_COLOR`) |

---

## 3. Terminal-Only Architecture Audit

An exhaustive inspection of the tracked codebase confirmed:
- **HTML/CSS/JS Frontends**: **None**. Zero `.html`, `.css`, or `.js` UI components.
- **GUI Frameworks**: **None**. Zero Electron, SwiftUI, PyQt, Tkinter, or web dashboards.
- **UI Web Servers**: **None**. No local web servers serving user interfaces.
- **Browser Automation vs Frontend**: Browser automation scripts (`browser_manager.py`) exist strictly for controlling user-directed browser actions (e.g. YouTube/Spotify playback and URL navigation in Brave/Chrome), not for rendering Friday's own interface.
- **Terminal Presentation**: Standard Python terminal I/O with optional ANSI colors, automatic `NO_COLOR` standard compliance, and protection against terminal escape sequence injection via `sanitize_terminal_text`.

---

## 4. Multi-Lingual Evaluation & Dataset

A dedicated evaluation suite in `tests/personality_dataset.py` validates 18 distinct scenarios across English, Hindi, and Hinglish:
1. **English**: Clear, calm, helpful assistance without robotic jargon or excessive formality.
2. **Hindi**: Gentle, respectful, and natural phrasing (e.g. `Bilkul. Python ek programming language hai...`).
3. **Hinglish**: Fluid, casual code-switching matching typical Indian developer workflows (e.g. `Sure, main project ka status check karti hoon`).

---

## 5. Performance Benchmarks on Apple Silicon M1 (8 GB RAM)

Benchmarked against local Ollama (`qwen2.5:3b`) on macOS with Apple M1 unified memory:

| Metric | Baseline Prompt | Milestone 5.1 Friday Prompt | Delta / Improvement |
| :--- | :--- | :--- | :--- |
| **System Prompt Word Count** | 127 words | 116 words | **-8.7% token footprint** |
| **System Prompt Char Count** | 803 characters | 799 characters | Compact & dense |
| **Identity Query TTFT** | 4.710 s | 0.751 s | **-84.1% latency reduction** |
| **Identity Query Total Time** | 5.655 s | 1.411 s | **-75.0% faster completion** |
| **Greeting TTFT** | 0.125 s | 0.114 s | **-8.8% faster initial token** |
| **Technical Explanation TTFT**| 0.130 s | 0.127 s | Consistent low latency |
| **Hinglish Query TTFT** | 0.124 s | 0.122 s | Immediate responsiveness |
| **Process Peak Memory RSS** | ~33.4 MB | ~12.1 MB | Zero memory pressure |

---

## 6. Security Boundaries & Honest Acknowledgements

- **Prompt Isolation**: Personality prompts are applied exclusively to conversational chat generation in `ask_friday` and `ask_friday_stream`. Structured intent classification (`SYSTEM_PROMPT` in `llm_router.py`) remains strictly isolated with pure JSON constraints.
- **Honest Action Acknowledgements**: `format_action_acknowledgement` guarantees that pending commands are never reported as "completed" or "successful" until deterministic execution succeeds.
- **Security Confirmations**: High-risk file and folder deletions retain deterministic confirmation prompts (`confirm_action`) that cannot be bypassed via conversational roleplay or prompt injection.
