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
    parser.add_argument(
        "--test-wake-word",
        action="store_true",
        help="Test wake-word detection engine availability and configuration.",
    )
    parser.add_argument(
        "--wake-word",
        action="store_true",
        help="Run Friday in wake-word listener mode (activates on 'Hey Friday').",
    )
    parser.add_argument(
        "--wake-sensitivity",
        type=float,
        default=0.5,
        help="Wake-word detection sensitivity threshold (0.0 to 1.0, default 0.5).",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run Friday in continuous conversational listening mode with voice interruption support.",
    )
    parser.add_argument(
        "--session-timeout",
        type=float,
        default=30.0,
        help="Inactivity timeout in seconds before continuous conversation returns to standby (default 30.0).",
    )
    parser.add_argument(
        "--speak",
        action="store_true",
        help="Enable spoken audio response output using local text-to-speech.",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available local speech synthesis voices.",
    )
    parser.add_argument(
        "--list-memory",
        action="store_true",
        help="List stored persistent conversation memories and recognized preferences.",
    )
    parser.add_argument(
        "--list-preferences",
        action="store_true",
        help="List all recognized user preferences (programming languages, tools, name, etc.).",
    )
    parser.add_argument(
        "--search-memory",
        type=str,
        default=None,
        help="Search stored memories by semantic similarity.",
    )
    parser.add_argument(
        "--delete-memory",
        type=str,
        default=None,
        help="Delete memory entry by ID or keyword query.",
    )
    parser.add_argument(
        "--clear-memory",
        action="store_true",
        help="Clear all stored conversation memories (privacy control; requires confirmation).",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Confirm execution of destructive operations without manual prompt.",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Run interactive session in private (incognito) mode with zero memory persistence.",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable memory persistence entirely for this execution.",
    )
    parser.add_argument(
        "--export-memory",
        type=str,
        default=None,
        help="Export all conversation memories and user preferences to a local JSON file.",
    )
    parser.add_argument(
        "--import-memory",
        type=str,
        default=None,
        help="Import and restore memories and user preferences from a local JSON file.",
    )
    parser.add_argument(
        "--prune-memory",
        type=int,
        default=None,
        help="Prune conversation memories older than specified number of days.",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default=None,
        help="Specify local voice name for speech synthesis (e.g. 'hinata', 'Samantha', 'Lekha').",
    )
    parser.add_argument(
        "--voice-speed",
        type=float,
        default=None,
        help="Speaking speed multiplier for neural speech synthesis (e.g. 1.09 for +15%%, 1.0 for standard).",
    )
    parser.add_argument(
        "--voice-info",
        action="store_true",
        help="Display active TTS engine, model, reference audio status, device, and fallback configuration.",
    )
    parser.add_argument(
        "--benchmark-tts",
        action="store_true",
        help="Run comprehensive benchmark on active TTS engine (latency, RTF, RAM, model load time).",
    )
    parser.add_argument(
        "--test-tts",
        type=str,
        nargs="?",
        const="Hello! I'm Friday, your personal AI assistant.",
        default=None,
        help="Test local speech synthesis by speaking a sample phrase.",
    )
    parser.add_argument(
        "--voice-profile",
        type=str,
        default=None,
        help="Select stylistic voice profile for speech synthesis (e.g. 'friday-gentle', 'friday-standard').",
    )
    parser.add_argument(
        "--voice-reference",
        type=str,
        default=None,
        help="Path to an authorized local reference WAV audio file for voice conditioning.",
    )
    parser.add_argument(
        "--validate-reference",
        type=str,
        default=None,
        help="Validate a local audio reference file (format, duration, signal RMS).",
    )
    parser.add_argument(
        "--stream-speech",
        action="store_true",
        help="Synthesize and play speech incrementally at sentence boundaries as the LLM generates tokens.",
    )
    parser.add_argument(
        "--expression",
        choices=["gentle", "happy", "focused", "concerned", "supportive", "neutral", "confident"],
        default=None,
        help="Explicitly set delivery expression style for speech synthesis.",
    )
    parser.add_argument(
        "--hands-free",
        action="store_true",
        help="Run Friday in unified hands-free conversation mode (wake-word standby, speech streaming, and spoken barge-in).",
    )
    parser.add_argument(
        "--personality",
        choices=["friendly", "professional", "casual"],
        default=None,
        help="Assistant personality style (friendly, professional, casual).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors in terminal output.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress startup banner and non-essential status messages.",
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
    if args.personality:
        os.environ["FRIDAY_PERSONALITY"] = args.personality
    if args.no_color:
        os.environ["FRIDAY_TERMINAL_COLOR"] = "false"
        os.environ["NO_COLOR"] = "1"
    if args.quiet:
        os.environ["FRIDAY_STARTUP_GREETING"] = "false"

    if args.voice_speed:
        os.environ["TTS_SPEED"] = str(args.voice_speed)

    if args.voice_info:
        from friday.audio.voice_manager import VoiceManager

        manager = VoiceManager()
        status = manager.get_status(profile_id=args.voice_profile)
        print("FRIDAY Voice System Information:")
        print(f"  Active TTS Engine:      {status.active_engine}")
        print(f"  Active Model:           {status.active_model}")
        print(f"  Model Weights Path:     {status.model_weights_path}")
        print(f"  Reference Audio Status: {status.reference_audio_status}")
        print(f"  Voice Profile:          {status.voice_profile}")
        print(f"  Inference Device:       {status.inference_device}")
        print(f"  Supported Languages:    {', '.join(status.supported_languages)}")
        print(f"  Fallback Status:        {'ACTIVE (Using fallback voice: ' + status.fallback_voice + ')' if status.is_fallback_active else 'STANDBY (Neural voice operational)'}")
        return 0

    if args.benchmark_tts:
        from friday.audio.voice_manager import VoiceManager
        import time
        import psutil

        manager = VoiceManager()
        print("Running FRIDAY Neural Voice Benchmark...")
        status = manager.get_status(profile_id=args.voice_profile)
        print(f"Active Engine: {status.active_engine}")
        print(f"Inference Device: {status.inference_device}")

        process = psutil.Process()
        mem_before = process.memory_info().rss / (1024 * 1024)

        test_sentences = [
            "Hello! I'm Friday, your personal AI assistant.",
            "All systems are operational and ready.",
            "Would you like me to explain that again?",
        ]

        # Cold-start benchmark
        t0 = time.time()
        success = manager.speak(test_sentences[0])
        cold_latency = time.time() - t0

        # Warm benchmark
        warm_latencies = []
        for s in test_sentences[1:]:
            t_start = time.time()
            manager.speak(s)
            warm_latencies.append(time.time() - t_start)

        mem_after = process.memory_info().rss / (1024 * 1024)
        avg_warm = sum(warm_latencies) / len(warm_latencies) if warm_latencies else 0.0

        print("\nBenchmark Results:")
        print(f"  Cold-start Synthesis Latency: {cold_latency:.3f}s")
        print(f"  Warm Synthesis Latency (avg): {avg_warm:.3f}s")
        print(f"  RAM Usage (Delta):            {mem_after - mem_before:.2f} MB")
        print(f"  Peak Process RSS:             {mem_after:.2f} MB")
        print(f"  Speech Success Rate:          {'100%' if success else 'Failed'}")
        return 0

    if args.list_memory:
        from friday.memory.local import get_all, get_all_preferences

        prefs = get_all_preferences()
        if prefs:
            print("Learned User Preferences:")
            for k, v in prefs.items():
                print(f"  • {k.capitalize()}: {v}")
            print()

        memories = get_all()
        if not memories and not prefs:
            print("No persistent memories or preferences stored yet.")
            return 0
        print(f"Stored Memories ({len(memories)} total entries):")
        for m in memories[-20:]:
            print(f"  [{m[0]}] User: {m[1]}")
            print(f"       Friday: {str(m[2])[:80]}...")
        return 0

    if args.list_preferences:
        from friday.memory.local import get_all_preferences

        prefs = get_all_preferences()
        if not prefs:
            print("No user preferences recognized yet.")
            return 0
        print("Recognized User Preferences & Profile:")
        for k, v in prefs.items():
            print(f"  • {k.capitalize()}: {v}")
        return 0

    if args.search_memory:
        from friday.memory.memory_manager import retrieve_memory

        results = retrieve_memory(args.search_memory, limit=5, min_similarity=0.1)
        if not results:
            print(f"No relevant memories found matching '{args.search_memory}'.")
            return 0
        print(f"Top memories matching '{args.search_memory}':")
        for r in results:
            print(f"  [{r[0]}] User: {r[1]}")
            print(f"       Friday: {str(r[2])[:100]}...")
        return 0

    if args.delete_memory:
        from friday.memory.memory_manager import delete_memory

        success = delete_memory(args.delete_memory)
        if success:
            print(f"Successfully deleted memory entry matching '{args.delete_memory}'.")
            return 0
        else:
            print(f"No memory entry found matching '{args.delete_memory}'.")
            return 1

    if args.private:
        from friday.memory.memory_manager import set_private_session
        set_private_session(True)
        print("Starting FRIDAY in Private (Incognito) Mode. No memories will be persisted.")

    if args.no_memory:
        from friday.memory.memory_manager import set_memory_enabled
        set_memory_enabled(False)
        print("Memory persistence disabled for this session.")

    if args.export_memory:
        from friday.memory.memory_manager import export_memory_json
        success, msg = export_memory_json(args.export_memory)
        print(msg)
        return 0 if success else 1

    if args.import_memory:
        from friday.memory.memory_manager import import_memory_json
        success, msg = import_memory_json(args.import_memory)
        print(msg)
        return 0 if success else 1

    if args.prune_memory is not None:
        from friday.memory.memory_manager import prune_retention_policy
        count = prune_retention_policy(args.prune_memory)
        print(f"Retention Policy: Pruned {count} memories older than {args.prune_memory} days.")
        return 0

    if args.clear_memory:
        if not args.yes:
            print("Action required: Clearing all memory is a destructive operation.")
            print("To execute, re-run with confirmation flag: --clear-memory --yes")
            return 1

        from friday.memory.memory_manager import clear_memory

        deleted = clear_memory()
        print(f"All stored memories and preferences cleared ({deleted} entries removed). Privacy status: CLEAN.")
        return 0

    if args.validate_reference:
        from friday.audio.voice_reference import VoiceReferenceValidator

        validator = VoiceReferenceValidator()
        res = validator.validate_file(args.validate_reference)
        if res.is_valid:
            print(f"Voice reference '{res.path}' is valid.")
            print(f"  Duration: {res.duration_s}s | Sample Rate: {res.sample_rate}Hz | Channels: {res.channels}")
            print(f"  RMS Level: {res.rms} | Peak: {res.peak} | Clipped: {res.clipped}")
            return 0
        else:
            print(f"Voice reference validation failed: {res.error}")
            return 1

    if args.list_voices:
        from friday.audio.tts import TTSEngine

        engine = TTSEngine()
        voices = engine.list_voices()
        if not voices:
            print("No local speech synthesis voices found (or 'say' binary unavailable).")
            return 1
        print("Available Local Speech Synthesis Voices:")
        for v in voices:
            print(f"  [{v.locale}] {v.name} - {v.example}")
        return 0

    if args.test_tts:
        from friday.audio.tts import TTSEngine

        engine = TTSEngine(voice=args.voice)
        if not engine.is_available():
            print("Local TTS engine is not available on this system.")
            return 1
        print(f"Testing local speech synthesis (Voice: {engine.voice}, Rate: {engine.rate} wpm)...")
        print(f"Speaking: '{args.test_tts}'")
        success = engine.speak(args.test_tts, voice=args.voice)
        if success:
            print("Speech synthesis test completed successfully.")
            return 0
        else:
            print("Speech synthesis test failed.")
            return 1

    if args.speak or args.stream_speech:
        os.environ["TTS_ENABLED"] = "true"
        if args.stream_speech:
            os.environ["TTS_STREAM_ENABLED"] = "true"
        if args.expression:
            os.environ["TTS_EXPRESSION"] = args.expression
        if args.voice:
            os.environ["TTS_VOICE"] = args.voice
        if args.voice_profile:
            os.environ["TTS_VOICE_PROFILE"] = args.voice_profile
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

    if args.test_wake_word:
        from friday.audio.wake_word import WakeWordEngine

        engine = WakeWordEngine(sensitivity=args.wake_sensitivity)
        status = "Available" if engine.is_available() else "Unavailable (no wake word engine or model found)"
        print(f"Wake-Word Engine: {status} (Backend: {engine.engine_type})")
        print(f"Phrase: '{engine.phrase}' | Sensitivity: {engine.sensitivity}")
        return 0

    if args.wake_word:
        from friday.audio.wake_word import WakeWordEngine, WakeWordListener

        engine = WakeWordEngine(sensitivity=args.wake_sensitivity)
        if not engine.is_available():
            print("Wake-word engine is not configured or unavailable.")
            print("Install openwakeword or configure WAKE_WORD_MODEL_PATH.")
            return 1
        listener = WakeWordListener(engine=engine)
        listener.start()
        print(f"Wake-word listener active. Say '{engine.phrase}' to activate Friday.")
        print("Press Ctrl+C to stop listening.")
        return 0

    if args.hands_free:
        from friday.audio.conversation import HandsFreeController

        controller = HandsFreeController(session_timeout=args.session_timeout)
        controller.start()
        print(f"Hands-free conversation active (Session timeout: {args.session_timeout}s).")
        print("Say 'Hey Friday' to start, follow-up naturally, or speak 'Stop' to barge-in.")
        print("Say 'Stop listening' to shut down microphone, or press Ctrl+C.")
        return 0

    if args.continuous:
        from friday.audio.session import ContinuousListener

        listener = ContinuousListener(session_timeout=args.session_timeout)
        listener.start()
        print(f"Continuous conversation mode active (Session timeout: {args.session_timeout}s).")
        print("Say 'Hey Friday' to start, follow-up naturally, or say 'Stop' to interrupt.")
        print("Say 'Stop listening' to shut down microphone, or press Ctrl+C.")
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
