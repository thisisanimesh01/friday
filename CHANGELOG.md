# Changelog

All notable changes to **Friday** are documented in this file.

## [Unreleased] - Phase 6, Milestone 6.2: Application Management, Window Control & Privacy Protection
- **Permanent PrivacyGuard Protection:** Implemented deterministic, deny-by-default `PrivacyGuard` (`src/friday/security/privacy_guard.py`) providing absolute isolation for `~/Desktop/me and she/` across all case variants, symlinks, aliases, and traversal attempts. Blocks macOS Photos Library, Messages, Keychain, Mail, SSH, AWS, and GPG by default. Cannot be overridden by voice, CLI, or confirmation.
- **Dedicated Friday Workspace Confinement:** Established strict workspace boundary at `~/Desktop/friday workspace/` with 10 standard subdirectories (`documents`, `images`, `videos`, `screenshots`, `camera`, `projects`, `downloads`, `reports`, `exports`, `temp`).
- **Application Lifecycle Management:** Implemented application discovery, alias resolution, fuzzy matching (`difflib`), launch (`open -a`), graceful quit (`osascript`), confirmation-guarded force-quit (`pkill -9`), switch (`activate`), hide, and active application detection.
- **Window Management Handlers:** Added window operations for minimize, restore, fullscreen toggle, and snapping/positioning (`left_half`, `right_half`, `center`, `maximize`) via macOS System Events.
- **Explicit On-Demand Media Capture:** Created single-use, on-demand camera capture (`src/friday/macos/media_capture.py`) saved strictly to `friday workspace/camera/` and screenshot capture saved strictly to `friday workspace/screenshots/`. Device hardware is immediately released upon capture completion.
- **English, Hindi, and Hinglish Intent Routing:** Expanded macOS intent router (`src/friday/macos/router.py`) to handle natural-language queries (e.g., `open calculator`, `terminal kholo`, `calculator band karo`, `window minimize karo`, `left half karo`, `take a photo`, `screenshot lo`).
- **CLI & Inspection Flags:** Added `--launch-app <name>`, `--quit-app <name>`, `--window-action <action>`, `--take-photo`, `--take-screenshot`, and `--target-app <name>` with `--dry-run` and `--yes` support.
- **Voice & Resource Preservation:** Verified preserved approved Hinata neural voice embedding and 1.14x speed multiplier, cold-start latency ~7.5s, warm latency ~4.9s, and RSS <70MB.

## [Phase 6, Milestone 6.1] - macOS Control Foundation & Permission Framework
- **Modular Action Registry:** Implemented typed action registry (`src/friday/macos/registry.py`) with risk classification tiers (`READ_ONLY`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), strict argument schemas, and execution timeout protection.
- **Deterministic Intent Routing:** Added macOS natural-language intent router (`src/friday/macos/router.py`) mapping queries directly to allowlisted system actions without executing unrestricted LLM shell commands.
- **Harmless Read-Only Actions:** Added built-in allowlisted handlers for `get_battery`, `get_volume`, `set_volume`, `list_apps`, `get_appearance` (Dark/Light mode), and `get_storage`.
- **Privacy-Safe Audit Logging:** Structured audit log (`~/Library/Application Support/Friday/logs/macos_actions.jsonl`) recording action type, risk, duration, and parameter sanitization (redacting passwords, keys, and tokens).
- **CLI & Dry-Run Controls:** Added `--list-actions`, `--mac-action <name>`, and `--dry-run` to inspect and safely simulate system actions.
- **Preserved Approved Voice:** Maintained approved Hinata neural voice model and 1.14x speaking speed.

## [Phase 5, Milestone 5.4] - Memory Privacy & Management
- **Privacy & Memory Toggles:** Added `is_memory_enabled()`, `set_memory_enabled()`, `is_private_session()`, and `set_private_session()` providing instant incognito execution without touching persistent disk storage.
- **Natural-Language Remember & Forget Commands:** Supported conversational memory directives (e.g. `remember that I prefer Vim`, `forget my editor preference`, `forget about project FRIDAY`, `forget everything you know about me`).
- **Prompt Injection Defense:** Added `sanitize_memory_text()` to strip injected `<system>` tags, instruction overrides, and role-spoofing prefixes before injecting memories into LLM prompts.
- **Selective Deletion & Complete Invalidation:** Ensured deleted memories and forgotten preferences are purged from both SQLite and active in-memory session history and caches.
- **Automated Retention Policies:** Implemented `prune_retention_policy(days)` and CLI `--prune-memory <days>` to clean records older than a configured time window.
- **Export & Restore:** Added `--export-memory <file.json>` and `--import-memory <file.json>` for local encrypted/portable backups.
- **Destructive Confirmation Guards:** Guarded `--clear-memory` to require `--yes` / `-y` before executing destructive operations.
- **Preserved Approved Voice:** Hinata neural voice embedding (`hinata_voice.npy`) and 1.14x speed multiplier preserved permanently.

## [Phase 5, Milestone 5.3] - Intelligent Memory & Personalization
- **Intelligent Memory Selection:** Added filtering in `src/friday/memory/intelligence.py` to prevent saving sensitive information (passwords, API keys, tokens, credit cards) and transient/ephemeral noise (greetings, short acknowledgments, diagnostics).
- **Preference Recognition & Upserting:** Extracted and categorized user preferences (name, primary programming language, project, database, editor, UI theme) into dedicated `user_preferences` SQLite table.
- **Contradiction Resolution & Fact Updates:** Implemented fact correction detection (e.g. "Actually I switched to...") that updates preferences and purges contradictory or superseded past memories.
- **Personalized Context Assembly:** Injected recognized user preferences directly into LLM prompts in `src/friday/brain.py` alongside short-term dialogue context and relevant semantic memories.
- **CLI Commands:** Added `--list-preferences` and updated `--list-memory` in `src/friday/cli.py` for full transparency and inspection.
- **Preserved Approved Voice:** Hinata neural voice embedding and 1.14x speed multiplier preserved permanently.

## [Phase 5, Milestone 5.2] - Contextual Memory Improvements
- **Short-Term Conversational Context:** Injected recent multi-turn conversation context (`full_history`) directly into local LLM generation.
- **Persistent Long-Term Memory:** Stored conversation turns and memory items offline in SQLite (`memory.db`) with zero external cloud dependencies.
- **Semantic Retrieval & Cosine Similarity:** Integrated feature hashing and vector similarity scoring to automatically recall relevant facts and preferences during conversation and post-restart sessions.
- **Duplicate Prevention:** Added semantic deduplication (similarity cutoff >= 0.95) to prevent storing duplicate user turns.
- **Memory Deletion & Inspection CLI:** Added CLI flags `--list-memory`, `--search-memory <query>`, `--delete-memory <id_or_text>`, and `--clear-memory` for transparency and user control.
- **Preserved Approved Voice:** Maintained approved Hinata neural voice embedding and 1.14x speaking speed.

## [Phase 5, Milestone 5.1.1] - Hinata Neural Voice Integration
- **Kokoro-82M ONNX Integration:** Replaced native macOS fallback with approved Hinata Hyuga neural voice model at 1.14x speed.

## [Phase 5, Milestone 5.1] - Consistent Friday Personality & Terminal-Only Architecture
- **Centralized Identity & Profile:** Added `src/friday/personality/` defining single source of truth for Friday's assistant identity, calm professional traits, and Hinata-inspired gentle warmth.
- **Terminal-Only Architecture:** Audited codebase confirming 0 HTML/CSS/JS frontend files, 0 GUI frameworks, and 0 web UI servers. Sanitized terminal escape sequences against ANSI/OSC injection.
- **Compact Personality Prompts:** Implemented compact personality prompt generator (<140 tokens) preserving Apple Silicon M1 context windows while strictly isolating personality from structured tool routing.
- **Honest Action Statuses:** Added `format_action_acknowledgement` guaranteeing transparent reporting across received, pending, confirming, executing, succeeded, failed, and cancelled states.
- **CLI & Configuration:** Added `--personality`, `--no-color`, and `--quiet` flags in `src/friday/cli.py`, with support for `NO_COLOR` standard.
- **Evaluation & Benchmarks:** Added reproducible 18-scenario dataset `tests/personality_dataset.py`, benchmark utility `scripts/benchmark_personality.py`, and comprehensive documentation in `docs/personality.md`.

## [Phase 4] - Speech Synthesis & Voice Pipeline
- **Hands-Free Conversation (PR #41):** Added `HandsFreeController` orchestrating wake-word standby, streaming TTS, and spoken barge-in.
- **Streaming Speech & Emotional Expression (PR #39):** Added `StreamingTTSCoordinator`, `SpeechSegmenter`, and `SpeechExpression` context delivery.
- **Authorized Voice Reference Tuning (PR #37):** Added `VoiceReferenceValidator` for 16-bit PCM WAV reference audio validation.
- **Voice Model Feasibility (PR #35):** Evaluated local TTS models for Apple M1 8GB memory footprint and registered `friday-gentle`.
- **Local TTS & Playback (PR #33):** Added `TTSEngine`, `PlaybackManager`, and half-duplex microphone gating.

## [Phase 1] - Engineering Foundation
- **CLI & README Polish:** Added `argparse` CLI (`--help`, `--version`, `--debug`, `--provider`) in `src/friday/cli.py`, package entry point `friday`, `CHANGELOG.md`, and polished `README.md`.
- **Package Restructuring (PR #11):** Organized modules into `src/friday/` with backward-compatible `main.py` and 3-job parallel CI (`Ruff Lint`, `Python Syntax`, `Pytest`).
- **Unit Tests & CI (PR #9):** Added offline `pytest` suite under `tests/` and upgraded GitHub Actions CI.
- **Error Handling (PR #7):** Replaced all 11 bare `except:` clauses with specific exceptions and structured logging.
- **Packaging Standardization (PR #5):** Added `pyproject.toml` and MIT `LICENSE`; removed unused `utils.py` and duplicate `requirement.txt`.
- **Ollama Integration (PR #4):** Added local Ollama support to `llm_router.py` and `brain.py`.
- **Repository Hygiene (PR #2):** Added GitHub Issue/PR templates, initial CI workflow, and `requirements.txt`.
