# Hinata-Inspired Voice Model Feasibility Report

## 1. Executive Summary & Objective
This report evaluates the technical, acoustic, legal, and hardware feasibility of integrating a gentle, warm, Hinata Hyuga-inspired female voice for **FRIDAY** on an **Apple Silicon M1 Mac with 8 GB unified memory** running Python 3.12.

---

## 2. Target Voice Characteristics
The vocal persona for Friday requires an original or appropriately licensed synthetic voice embodying:
- **Tone & Delivery**: Soft, gentle, feminine vocal presentation with calm, warm, and natural conversational cadence.
- **Pacing**: Slightly relaxed speaking rate (approx. 160–170 wpm) allowing clear pauses and natural breathing intervals.
- **Pitch**: Moderately high but comfortable, avoiding shrill, artificially squeaky, or whispery extremes.
- **Intelligibility**: Clear articulation of English technical vocabulary and clean handling of Hindi and Hinglish dialogues.
- **Legal Boundaries**: Distinct from any specific copyrighted anime character or voice actress; 100% original voice synthesis without extracting unauthorized media clips.

---

## 3. Candidate Voice Model Architecture Comparison

| Model | Parameters | License | RAM Requirement | Apple Silicon (M1) Support | Python 3.12 | Multi-Lingual (EN / HI / Hinglish) | Feasibility Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Native macOS `say`** | Built-in OS | Apple Proprietary (macOS) | ~0 MB (OS service) | 100% Native (CoreAudio) | 100% | Full EN & HI (`Lekha`), 68+ voices | **Recommended Production Baseline** |
| **Kokoro 82M** | 82M | Apache-2.0 | ~350 MB | Native (ONNX/Torch) | Compatible | Excellent EN; Hindi requires custom phonemization | **Recommended Neural Candidate (Milestone 4.3)** |
| **Piper TTS** | 15M–50M | MIT | ~80–120 MB | Native (ONNX) | Compatible | Distinct separate models per language | **Viable Embedded Fallback** |
| **F5-TTS** | 300M+ | MIT | ~1.8–2.5 GB | PyTorch MPS | Heavy | Heavy memory pressure on 8GB RAM | **Future Research Only** |
| **XTTS v2** | 460M+ | Coqui Public Model License | ~2.5–3.2 GB | Heavy on CPU/MPS | Potential conflicts | Multilingual, but high RAM when paired with Ollama | **Not Recommended for 8GB RAM** |
| **StyleTTS2** | ~200M | MIT | ~1.2–1.8 GB | PyTorch MPS | Complex C extensions | High latency on M1 CPU/MPS | **Research Only** |

---

## 4. Hardware Coexistence on Apple M1 (8 GB RAM)
On an 8 GB unified memory machine running Ollama (`qwen2.5:3b` occupying ~2.0 GB RAM), Whisper STT (~200–500 MB), and Friday processes (~150 MB):
- **Native macOS `say`**: Zero additional memory pressure, executes independently via CoreAudio daemon.
- **Kokoro 82M**: At ~350 MB RAM, Kokoro is the only neural TTS architecture capable of coexisting alongside Ollama without inducing memory swap or pressure.
- **Sequential Pipeline**: For hands-free conversational turns, processing remains strictly sequential:
  $$\text{Audio Frame Capture (VAD)} \longrightarrow \text{Whisper STT} \longrightarrow \text{Ollama LLM} \longrightarrow \text{TTS Synthesis \& Playback}$$

---

## 5. Next Steps for Milestone 4.3 (Voice Tuning & References)
1. Maintain `friday-gentle` as the default voice profile across the native baseline.
2. Formally evaluate authorized open-source female reference audio samples for Kokoro 82M voice blending and style conditioning.
3. Ensure zero copyrighted anime or celebrity voice cloning is utilized.
