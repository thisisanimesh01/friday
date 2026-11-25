# Changelog

All notable changes to **Friday** are documented in this file.

## [Unreleased] - Phase 5, Milestone 5.1: Consistent Friday Personality & Terminal-Only Architecture
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
