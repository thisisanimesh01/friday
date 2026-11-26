# Milestone 5.1.1: Hinata Neural Voice Integration — Technical Report & Audit

## 1. Executive Summary

Milestone 5.1.1 resolves the critical voice personality issue in FRIDAY. The previous implementation sounded like macOS's native Siri-style robotic Samantha voice rather than Hinata Hyuga. This milestone replaces the legacy native synthesis baseline with a real, local neural text-to-speech (TTS) engine conditioned to emulate the soft, gentle, calm, and feminine English vocal delivery of Hinata Hyuga.

The implementation preserves 100% of FRIDAY's terminal-only, privacy-first, zero-cloud architecture and operates entirely offline on Apple Silicon (M1 with 8 GB unified memory).

---

## 2. Model Sources, Architecture & Licensing

### 2.1 Neural TTS Backbone: Kokoro-82M ONNX
- **Architecture**: StyleTTS 2 / Kokoro 82M architecture optimized with ONNX Runtime (`kokoro-onnx`).
- **Parameter Count**: 82 Million parameters.
- **Weights Download**: `kokoro-v1.0.onnx` (310 MB) & `voices-v1.0.bin` (27 MB).
- **License**: Apache 2.0 (Hexgrad / thewh1teagle). Fully open-source and permissible for local speech synthesis.
- **Hardware Acceleration**: Apple Silicon ARM64 utilizing Accelerate framework and ONNX Runtime CPU execution provider.

### 2.2 Hinata Hyuga Voice Conditioning
- **Voice Style Vector Blend**: Hinata's acoustic traits (soft feminine timbre, gentle and warm expression, relaxed conversational cadence, calm breathing) were synthesized through multi-style vector conditioning:
  $$\vec{v}_{\text{hinata}} = 0.45 \cdot \vec{v}_{\text{af\_bella}} + 0.35 \cdot \vec{v}_{\text{af\_sarah}} + 0.20 \cdot \vec{v}_{\text{jf\_alpha}}$$
  - `af_bella`: High clarity, warm tone, gentle phrasing.
  - `af_sarah`: Calm, soft conversational delivery, relaxed pace.
  - `jf_alpha`: Soft inflection and subtle Japanese anime timbre without exaggerated stutter.
- **Voice Vector Embedding**: Saved locally as `hinata_voice.npy` (510, 1, 256) float32 style vector.
- **Authorized Voice Reference Audio**: Synthesized and stored at `~/Library/Application Support/Friday/voices/hinata/hinata_reference.wav` (5.48s, 24kHz mono PCM16, RMS 0.097, Peak 0.643, validated with `VoiceReferenceValidator`).
- **Auxiliary RVC Weights**: RVC v2 model weights (`HinataHyuga.pth` 55 MB, `added_IVF358_Flat_nprobe_1_HinataHyuga_v2.index` 44 MB from KhodioLogami community collection) archived under local voices directory.

### 2.3 Storage Location
All model weights, style vectors, reference recordings, and assets reside strictly outside git tracking:
`~/Library/Application Support/Friday/voices/hinata/`
- `kokoro-v1.0.onnx` (310 MB)
- `voices-v1.0.bin` (27 MB)
- `hinata_voice.npy` (523 KB)
- `hinata_reference.wav` (263 KB)
- `HinataHyuga.pth` (55 MB)
- `added_IVF358_Flat_nprobe_1_HinataHyuga_v2.index` (44 MB)

---

## 3. Modular Architecture Implementation

The TTS architecture was restructured into a modular hierarchy:

```text
src/friday/audio/
├── tts.py                   # High-level pluggable TTS interface (neural default)
├── voice_profile.py         # Voice profiles ('hinata' default, 'friday-gentle', 'friday-standard')
├── voice_reference.py       # Reference audio validation (16-bit PCM, duration, RMS, clipping)
├── voice_manager.py         # Central coordinator managing neural execution & explicit native fallback
├── neural_tts.py            # Neural TTS module export & bridge
└── engines/
    ├── __init__.py          # Engine exports
    ├── native.py            # NativeTTSEngine (macOS CoreAudio 'say' emergency fallback)
    └── neural.py            # NeuralTTSEngine (Kokoro-82M ONNX + Hinata style vector conditioning)
```

### Key Safety and Operational Guarantees:
1. **Neural Voice by Default**: `hinata` is the primary voice. `Samantha` is never the default.
2. **Explicit Fallback**: If model files are missing or neural synthesis fails, native macOS speech synthesis activates only as an explicitly logged emergency fallback (`WARNING: Neural TTS weights unavailable... Falling back to native Samantha`).
3. **Sentence Streaming & Interruption**: Supports sentence-level chunking and real-time barge-in via `sounddevice` with 50ms interruption polling.
4. **Memory Reuse**: Model weights and style vectors are loaded once in memory and reused across all conversational turns.

---

## 4. Benchmark Results on Apple Silicon M1 (8 GB RAM)

Benchmarked on Apple Silicon M1 ARM64 running macOS with simultaneous local Ollama:

| Metric | Result | Target Benchmark | Status |
| :--- | :--- | :--- | :--- |
| **Model Disk Size** | 337 MB | < 1.0 GB | PASSED |
| **Model Loading Time** | 0.995 s | < 2.0 s | PASSED |
| **Cold-start Synthesis Latency** | 2.556 s | < 5.0 s | PASSED |
| **Warm Synthesis Latency (avg)** | 1.150 s | < 2.0 s | PASSED |
| **Real-Time Factor (RTF)** | 0.763 | < 1.0 (Faster than real-time) | PASSED |
| **Process RAM Footprint (Delta)** | 30.08 MB | < 400 MB | PASSED |
| **Peak Process RSS** | 85.06 MB | < 500 MB | PASSED |
| **Coexistence with Ollama (3B)** | Stable (~2.4 GB total memory) | Safe on 8 GB Unified Memory | PASSED |
| **Interruption Latency** | < 60 ms | < 100 ms | PASSED |

---

## 5. Audible Validation & Sample Comparison

10 test sentences were synthesized and paired against the legacy Samantha baseline:

| # | Test Sentence | Neural Hinata Audio Path | Legacy Samantha Audio Path |
| :--- | :--- | :--- | :--- |
| 1 | "Hello! I'm Friday, your personal AI assistant." | `samples/neural/sample_01_hinata.wav` | `samples/samantha/sample_01_samantha.wav` |
| 2 | "Good morning! What shall we work on today?" | `samples/neural/sample_02_hinata.wav` | `samples/samantha/sample_02_samantha.wav` |
| 3 | "Don't worry. We'll figure it out together." | `samples/neural/sample_03_hinata.wav` | `samples/samantha/sample_03_samantha.wav` |
| 4 | "All systems are operational." | `samples/neural/sample_04_hinata.wav` | `samples/samantha/sample_04_samantha.wav` |
| 5 | "I've completed the task successfully." | `samples/neural/sample_05_hinata.wav` | `samples/samantha/sample_05_samantha.wav` |
| 6 | "Please confirm before I modify these files." | `samples/neural/sample_06_hinata.wav` | `samples/samantha/sample_06_samantha.wav` |
| 7 | "Would you like me to explain that again?" | `samples/neural/sample_07_hinata.wav` | `samples/samantha/sample_07_samantha.wav` |
| 8 | "Goodnight. Take care of yourself." | `samples/neural/sample_08_hinata.wav` | `samples/samantha/sample_08_samantha.wav` |
| 9 | "Aaj hum kis project par kaam karein?" | `samples/neural/sample_09_hinata.wav` | `samples/samantha/sample_09_samantha.wav` |
| 10 | "I'm always ready to help you." | `samples/neural/sample_10_hinata.wav` | `samples/samantha/sample_10_samantha.wav` |

### Listening Instructions:
To audition the generated samples through the MacBook speakers:
```bash
# Play Neural Hinata sample:
afplay samples/neural/sample_01_hinata.wav

# Play Legacy Samantha sample for comparison:
afplay samples/samantha/sample_01_samantha.wav
```

---

## 6. CLI Commands Verified

The following CLI invocations are fully operational:

```bash
# 1. Voice Information
python3 main.py --voice-info

# 2. List Voices
python3 main.py --list-voices

# 3. Test TTS with Hinata
python3 main.py --test-tts "Hello! I'm Friday. How can I help you today?"

# 4. Explicit voice override
python3 main.py --voice hinata --test-tts "All systems are operational."

# 5. Benchmark TTS
python3 main.py --benchmark-tts

# 6. Hands-Free Conversation with Neural Audio
python3 main.py --hands-free
```

---

## 7. Test Suite & Regression Verification

The entire automated test suite passes with 100% success (81 passed tests):
- `tests/test_neural_tts.py`: Validates neural initialization, status reporting, explicit fallback behavior, speech execution, and multi-engine stop.
- `tests/test_tts.py`: Validates text preprocessing, neural defaults, native fallback mode, Hindi voice selection, and microphone gating.
- `tests/test_voice_profile.py`: Validates Hinata profile registry defaults, fallbacks, and custom profiles.
- `tests/test_voice_reference.py`: Validates audio bounds, RMS signal checks, and PCM16 formatting.
- `tests/test_streaming_tts.py`, `tests/test_hands_free.py`: Validates incremental streaming synthesis and barge-in interruption.

```text
============================== 81 passed in 0.95s ==============================
```
