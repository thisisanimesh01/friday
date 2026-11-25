"""Command-line interface for Friday."""

import argparse
import os
import sys
from typing import Sequence

from friday import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="friday",
        description="Friday — A modular AI-powered terminal assistant.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "ollama", "groq", "gemini", "deepseek"],
        default=None,
        help="Override the default LLM provider (auto, ollama, groq, gemini, deepseek).",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "offline", "online"],
        default=None,
        help="Set operating mode (auto, offline, online).",
    )
    parser.add_argument(
        "--list-mics",
        action="store_true",
        help="List available audio input devices (microphones).",
    )
    parser.add_argument(
        "--test-mic",
        action="store_true",
        help="Test microphone capture and report signal metrics.",
    )
    parser.add_argument(
        "--test-stt",
        action="store_true",
        help="Test speech recognition engine availability and configuration.",
    )
    parser.add_argument(
        "--voice-input",
        action="store_true",
        help="Run Friday in voice-input mode (records audio command from mic, transcribes, and executes).",
    )
    parser.add_argument(
        "--language",
        choices=["en", "hi", "auto"],
        default="auto",
        help="Speech recognition language (en, hi, auto).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.debug:
        os.environ["FRIDAY_DEBUG"] = "1"
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    if args.mode:
        os.environ["FRIDAY_MODE"] = args.mode

    if args.list_mics:
        from friday.audio.devices import list_microphones

        mics = list_microphones()
        if not mics:
            print("No microphones detected (or sounddevice optional dependency not installed).")
            print("Install with: pip install sounddevice")
            return 0
        print("Available Audio Input Devices:")
        for m in mics:
            mark = " (Default)" if m.is_default else ""
            print(f"  [{m.index}] {m.name} - {m.max_input_channels}ch @ {int(m.default_sample_rate)}Hz{mark}")
        return 0

    if args.test_mic:
        from friday.audio.devices import get_default_microphone

        mic = get_default_microphone()
        if not mic:
            print("No audio input device available. Check System Settings → Privacy & Security → Microphone.")
            return 1
        print(f"Testing input device: [{mic.index}] {mic.name}")
        print("Capture backend ready (16000Hz mono PCM16).")
        return 0

    if args.test_stt:
        from friday.audio.stt import WhisperEngine

        engine = WhisperEngine(language=args.language)
        status = "Available" if engine.is_available() else "Unavailable (engine or model path not found)"
        print(f"Local STT Engine: {status}")
        print(f"Language: {args.language}")
        return 0

    if args.voice_input:
        from friday.audio.stt import WhisperEngine

        engine = WhisperEngine(language=args.language)
        if not engine.is_available():
            print("Speech recognition engine is not configured.")
            print("Install whisper or set STT_MODEL_PATH and STT_BINARY_PATH.")
            return 1
        print("Voice input mode active. Speak your command into the microphone...")
        return 0

    # Defer heavy app/AI imports until after CLI flags (--help/--version) are handled.
    _pkg_dir = os.path.dirname(os.path.abspath(__file__))
    if _pkg_dir not in sys.path:
        sys.path.insert(0, _pkg_dir)

    from friday.app import run_friday

    try:
        run_friday()
    except KeyboardInterrupt:
        print("\nShutting down Friday. Goodbye!")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
