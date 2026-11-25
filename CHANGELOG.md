# Changelog

All notable changes to **Friday** are documented in this file.

## [Unreleased] - Phase 1 Professionalization
- **CLI & README Polish:** Added `argparse` CLI (`--help`, `--version`, `--debug`, `--provider`) in `src/friday/cli.py`, package entry point `friday`, `CHANGELOG.md`, and polished `README.md`.
- **Package Restructuring (PR #11):** Organized modules into `src/friday/` with backward-compatible `main.py` and 3-job parallel CI (`Ruff Lint`, `Python Syntax`, `Pytest`).
- **Unit Tests & CI (PR #9):** Added offline `pytest` suite under `tests/` and upgraded GitHub Actions CI.
- **Error Handling (PR #7):** Replaced all 11 bare `except:` clauses with specific exceptions and structured logging.
- **Packaging Standardization (PR #5):** Added `pyproject.toml` and MIT `LICENSE`; removed unused `utils.py` and duplicate `requirement.txt`.
- **Ollama Integration (PR #4):** Added local Ollama support to `llm_router.py` and `brain.py`.
- **Repository Hygiene (PR #2):** Added GitHub Issue/PR templates, initial CI workflow, and `requirements.txt`.
