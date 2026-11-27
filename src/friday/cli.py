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
        "--list-actions",
        action="store_true",
        help="List all registered allowlisted macOS system control actions and their risk tiers.",
    )
    parser.add_argument(
        "--mac-action",
        type=str,
        default=None,
        help="Execute a specific registered macOS system action by name.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without modifying macOS system state or files.",
    )
    # Milestone 6.2 Application, Window, and Media capture flags
    parser.add_argument(
        "--launch-app",
        type=str,
        default=None,
        help="Launch an installed macOS application by name.",
    )
    parser.add_argument(
        "--quit-app",
        type=str,
        default=None,
        help="Quit a running macOS application (force-quit requires --yes).",
    )
    parser.add_argument(
        "--window-action",
        choices=["minimize", "restore", "fullscreen", "left", "right", "center", "maximize"],
        default=None,
        help="Execute a window management action on the frontmost or active application.",
    )
    parser.add_argument(
        "--take-photo",
        action="store_true",
        help="Capture on-demand camera photo saved strictly to friday workspace/camera/.",
    )
    parser.add_argument(
        "--take-screenshot",
        choices=["fullscreen", "window", "region"],
        nargs="?",
        const="fullscreen",
        default=None,
        help="Capture on-demand screenshot saved strictly to friday workspace/screenshots/.",
    )
    parser.add_argument(
        "--target-app",
        type=str,
        default=None,
        help="Target application name for window actions or app operations.",
    )
    # Milestone 6.3 AppleScript & Shortcuts Automation flags
    parser.add_argument(
        "--run-script",
        type=str,
        default=None,
        help="Execute an allowlisted AppleScript automation template by name.",
    )
    parser.add_argument(
        "--list-scripts",
        action="store_true",
        help="List available allowlisted AppleScript automation templates.",
    )
    parser.add_argument(
        "--script-title",
        type=str,
        default=None,
        help="Title parameter for AppleScript template.",
    )
    parser.add_argument(
        "--script-message",
        type=str,
        default=None,
        help="Message/body parameter for AppleScript template.",
    )
    parser.add_argument(
        "--run-shortcut",
        type=str,
        default=None,
        help="Execute a verified macOS shortcut by name.",
    )
    parser.add_argument(
        "--list-shortcuts",
        action="store_true",
        help="List installed macOS shortcuts and their security approval status.",
    )
    parser.add_argument(
        "--shortcut-input",
        type=str,
        default=None,
        help="Optional input file path for running a macOS shortcut.",
    )
    parser.add_argument(
        "--shortcut-output",
        type=str,
        default=None,
        help="Optional output filename (confined to friday workspace/reports/) for a shortcut.",
    )
    parser.add_argument(
        "--approve-shortcut",
        type=str,
        default=None,
        help="Approve an installed macOS shortcut for automated execution.",
    )
    # Milestone 6.4 System Settings & Hardware Controls flags
    parser.add_argument(
        "--mute",
        action="store_true",
        help="Mute macOS system audio output.",
    )
    parser.add_argument(
        "--unmute",
        action="store_true",
        help="Unmute macOS system audio output.",
    )
    parser.add_argument(
        "--brightness",
        type=int,
        default=None,
        help="Set macOS display brightness level (0-100).",
    )
    parser.add_argument(
        "--appearance",
        choices=["dark", "light", "toggle"],
        default=None,
        help="Set or toggle macOS system appearance mode (dark, light, toggle).",
    )
    parser.add_argument(
        "--list-audio-devices",
        action="store_true",
        help="List available macOS audio input and output devices.",
    )
    parser.add_argument(
        "--focus-mode",
        choices=["status", "toggle"],
        default=None,
        help="Query or toggle macOS Focus Mode / Do Not Disturb.",
    )
    parser.add_argument(
        "--system-metrics",
        action="store_true",
        help="Display live CPU, RAM, and disk utilization metrics.",
    )
    parser.add_argument(
        "--thermal-status",
        action="store_true",
        help="Query macOS thermal and throttling status.",
    )
    parser.add_argument(
        "--wifi",
        choices=["status", "on", "off"],
        default=None,
        help="Query or control Wi-Fi networking (power on/off requires --yes).",
    )
    parser.add_argument(
        "--bluetooth",
        choices=["status", "on", "off"],
        default=None,
        help="Query or control Bluetooth adapter (power on/off requires --yes).",
    )
    parser.add_argument(
        "--lock-screen",
        action="store_true",
        help="Lock macOS screen display (requires --yes).",
    )
    parser.add_argument(
        "--sleep",
        action="store_true",
        help="Put macOS into sleep mode (requires --yes).",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Restart macOS safely protecting unsaved work (requires --yes).",
    )
    parser.add_argument(
        "--shutdown",
        action="store_true",
        help="Shut down macOS safely protecting unsaved work (requires --yes).",
    )
    parser.add_argument(
        "--health-report",
        action="store_true",
        help="Generate a comprehensive system health report saved in friday workspace/reports/.",
    )
    # Milestone 6.5 Desktop Workflows flags
    parser.add_argument(
        "--run-workflow",
        type=str,
        default=None,
        help="Execute a multi-step desktop workflow by ID or name.",
    )
    parser.add_argument(
        "--list-workflows",
        action="store_true",
        help="List available built-in and custom desktop workflows.",
    )
    parser.add_argument(
        "--workflow-preview",
        type=str,
        default=None,
        help="Preview steps and dependencies of a workflow by ID.",
    )
    parser.add_argument(
        "--stop-workflow",
        action="store_true",
        help="Signal cancellation to stop any currently running desktop workflow.",
    )
    parser.add_argument(
        "--create-workflow",
        type=str,
        default=None,
        help="Create a custom workflow from a JSON string or file path.",
    )
    parser.add_argument(
        "--delete-workflow",
        type=str,
        default=None,
        help="Delete a custom workflow from the workspace (requires --yes).",
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
        import time

        import psutil

        from friday.audio.voice_manager import VoiceManager

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

    if args.list_actions:
        from friday.macos.registry import default_registry

        actions = default_registry.list_actions()
        print(f"Registered Allowlisted macOS Actions ({len(actions)} total):")
        for a in actions:
            confirm = " [Requires Confirmation]" if a["requires_confirmation"] else ""
            print(f"  • {a['name']:<16} [{a['risk']:<9}] - {a['description']}{confirm}")
        return 0

    if args.mac_action:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(
            name=args.mac_action,
            dry_run=args.dry_run,
            confirmed=args.yes,
        )
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    # Milestone 6.2 CLI handlers
    if args.launch_app:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(
            name="launch_app",
            dry_run=args.dry_run,
            confirmed=args.yes,
            app_name=args.launch_app,
        )
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    if args.quit_app:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        force = args.yes
        res = default_registry.execute(
            name="quit_app",
            dry_run=args.dry_run,
            confirmed=args.yes,
            app_name=args.quit_app,
            force=force,
        )
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    if args.window_action:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        action_name = "position_window"
        kwargs = {}
        if args.window_action == "minimize":
            action_name = "minimize_window"
            if args.target_app:
                kwargs["app_name"] = args.target_app
        elif args.window_action == "restore":
            action_name = "restore_window"
            if args.target_app:
                kwargs["app_name"] = args.target_app
        elif args.window_action == "fullscreen":
            action_name = "fullscreen_window"
            if args.target_app:
                kwargs["app_name"] = args.target_app
        else:
            action_name = "position_window"
            kwargs["position"] = args.window_action
            if args.target_app:
                kwargs["app_name"] = args.target_app

        res = default_registry.execute(
            name=action_name,
            dry_run=args.dry_run,
            confirmed=args.yes,
            **kwargs,
        )
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    if args.take_photo:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(
            name="capture_photo",
            dry_run=args.dry_run,
            confirmed=args.yes,
        )
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    if args.take_screenshot:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(
            name="capture_screenshot",
            dry_run=args.dry_run,
            confirmed=args.yes,
            mode=args.take_screenshot,
        )
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    # Milestone 6.3 CLI Handlers
    if args.list_scripts:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="list_script_templates")
        print(format_action_result(res))
        return 0

    if args.run_script:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        params = {}
        if args.script_title:
            params["title"] = args.script_title
        if args.script_message:
            params["message"] = args.script_message
            params["body"] = args.script_message

        res = default_registry.execute(
            name="run_script_template",
            dry_run=args.dry_run,
            confirmed=args.yes,
            template_name=args.run_script,
            params=params,
        )
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    if args.list_shortcuts:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="list_shortcuts")
        print(format_action_result(res))
        return 0

    if args.approve_shortcut:
        from friday.macos.shortcuts_automation import ShortcutsManager

        sm = ShortcutsManager()
        sm.approve_shortcut(args.approve_shortcut)
        print(f"Approved shortcut '{args.approve_shortcut}' for automated execution.")
        return 0

    if args.run_shortcut:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        kwargs = {
            "shortcut_name": args.run_shortcut,
        }
        if args.shortcut_input:
            kwargs["input_path"] = args.shortcut_input
        if args.shortcut_output:
            kwargs["output_filename"] = args.shortcut_output

        res = default_registry.execute(
            name="run_shortcut",
            dry_run=args.dry_run,
            confirmed=args.yes,
            **kwargs,
        )
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    # Milestone 6.4 CLI Handlers
    if args.mute or args.unmute:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(
            name="set_mute",
            dry_run=args.dry_run,
            confirmed=args.yes,
            mute=args.mute,
        )
        print(format_action_result(res))
        return 0 if res.success else 1

    if args.brightness is not None:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(
            name="set_brightness",
            dry_run=args.dry_run,
            confirmed=args.yes,
            level=args.brightness,
        )
        print(format_action_result(res))
        return 0 if res.success else 1

    if args.appearance:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        if args.appearance == "toggle":
            res = default_registry.execute(name="toggle_appearance", dry_run=args.dry_run)
        else:
            is_dark = args.appearance == "dark"
            res = default_registry.execute(name="set_appearance", dark_mode=is_dark, dry_run=args.dry_run)
        print(format_action_result(res))
        return 0 if res.success else 1

    if args.list_audio_devices:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="get_audio_devices")
        print(format_action_result(res))
        return 0

    if args.focus_mode:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        act = "toggle_focus_mode" if args.focus_mode == "toggle" else "get_focus_mode"
        res = default_registry.execute(name=act, dry_run=args.dry_run)
        print(format_action_result(res))
        return 0

    if args.system_metrics:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="get_hardware_metrics")
        print(format_action_result(res))
        return 0

    if args.thermal_status:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="get_thermal")
        print(format_action_result(res))
        return 0

    if args.wifi:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        if args.wifi == "status":
            res = default_registry.execute(name="get_wifi")
        else:
            pwr = args.wifi == "on"
            res = default_registry.execute(name="set_wifi_power", enabled=pwr, confirmed=args.yes, dry_run=args.dry_run)
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    if args.bluetooth:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        if args.bluetooth == "status":
            res = default_registry.execute(name="get_bluetooth")
        else:
            pwr = args.bluetooth == "on"
            res = default_registry.execute(name="set_bluetooth_power", enabled=pwr, confirmed=args.yes, dry_run=args.dry_run)
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    if args.lock_screen:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="lock_screen", confirmed=args.yes, dry_run=args.dry_run)
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    if args.sleep:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="system_sleep", confirmed=args.yes, dry_run=args.dry_run)
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    if args.restart:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="system_restart", confirmed=args.yes, dry_run=args.dry_run)
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    if args.shutdown:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="system_shutdown", confirmed=args.yes, dry_run=args.dry_run)
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

    if args.health_report:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="generate_health_report")
        print(format_action_result(res))
        return 0 if res.success else 1

    # Milestone 6.5 Workflow CLI Handlers
    if args.list_workflows:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="list_workflows")
        print(format_action_result(res))
        return 0

    if args.stop_workflow:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(name="stop_workflow")
        print(format_action_result(res))
        return 0

    if args.workflow_preview:
        from friday.macos.workflows import get_workflow_by_id

        wf = get_workflow_by_id(args.workflow_preview)
        if not wf:
            print(f"Error: Workflow '{args.workflow_preview}' not found.")
            return 1
        print(f"Workflow: {wf.name} ({wf.id}) [Timeout: {wf.timeout_s}s, Author: {wf.author}]")
        print(f"Description: {wf.description}")
        print(f"Steps ({len(wf.steps)}):")
        for i, s in enumerate(wf.steps, 1):
            deps = f" [Depends on: {', '.join(s.depends_on)}]" if s.depends_on else ""
            rb = " [Reversible]" if s.reversible else ""
            retries = f" [Retries: {s.retry_count}]" if s.retry_count else ""
            print(f"  {i}. {s.id}: action '{s.action}' args={s.args}{deps}{rb}{retries}")
        return 0

    if args.run_workflow:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(
            name="run_workflow",
            workflow_name=args.run_workflow,
            simulated=args.dry_run,
            confirmed=args.yes,
        )
        print(format_action_result(res))
        return 0 if res.success else 1

    if args.create_workflow:
        import json
        from pathlib import Path
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        raw_json = args.create_workflow
        if Path(raw_json).exists():
            raw_json = Path(raw_json).read_text(encoding="utf-8")

        res = default_registry.execute(
            name="create_workflow",
            definition_json=raw_json,
        )
        print(format_action_result(res))
        return 0 if res.success else 1

    if args.delete_workflow:
        from friday.macos.registry import default_registry
        from friday.macos.router import format_action_result

        res = default_registry.execute(
            name="delete_workflow",
            workflow_id=args.delete_workflow,
            confirmed=args.yes,
        )
        print(format_action_result(res))
        return 0 if res.success or res.requires_confirmation else 1

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
