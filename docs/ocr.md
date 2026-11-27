# FRIDAY Local OCR & Text Extraction Engine (Milestone 7.2)

## 1. Overview & Architecture

The FRIDAY Local OCR & Text Extraction Engine provides high-performance, strictly offline, privacy-safe optical character recognition tailored for Apple Silicon M1 (8GB RAM).

```mermaid
flowchart TD
    A[Image Input File] --> B[PrivacyGuard Verification]
    B -->|Forbidden Location / Symlink Trap| C[Fail-Closed Rejection: PrivacyViolationError]
    B -->|Valid Workspace Image| D[Engine Selector]
    D -->|Apple Vision Framework| E[VNRecognizeTextRequest / friday_vision_ocr]
    D -->|Fallback / Tesseract| F[Tesseract CLI tsv mode]
    E --> G[Text & Bounding Boxes Normalization]
    F --> G
    G --> H[Prompt Injection Detection & Redaction]
    H --> I[Structured OCRResult]
    I -->|User Requested Export| J[Atomic Save in ~/Desktop/friday workspace/exports/]
    I -->|Conversational Output| K[CLI / Assistant Response]
```

---

## 2. Key Capabilities & Engineering Highlights

1. **Dual-Backend Offline Architecture**:
   - **Primary Engine**: Apple Vision Framework (`VNRecognizeTextRequest`) compiled natively as an optimized Swift helper (`src/friday/macos/bin/friday_vision_ocr`).
   - **Secondary Engine**: Lightweight Tesseract OCR (`/opt/homebrew/bin/tesseract`) for fallback operations.
   - **Zero Cloud Transmissions**: 100% local inference, zero external HTTP/socket connections.

2. **Language Support & Runtime Inspection**:
   - Detects 33 supported recognition languages dynamically via the Vision framework.
   - Supports **English (`en-US`)**, **Hindi / Devanagari (`hi-IN`)**, mixed **Hinglish**, alphanumeric identifiers, and code snippets.
   - Runtime revision inspection (`VNRecognizeTextRequest.supportedRevisions`: Revisions 1, 2, 3).

3. **Structured Geometry & Confidence Scoring**:
   - Normalized top-left pixel bounding boxes `[x, y, width, height]`.
   - Confidence scoring calibrated on a `[0.0 .. 1.0]` scale.
   - Image dimension parsing without third-party dependencies.

4. **PrivacyGuard Enclosure & Boundary Protection**:
   - Deny-by-default access to the permanently protected folder (`~/Desktop/me and she/`).
   - Hardened realpath resolution preventing directory traversal, symlinks, and hardlinks.
   - Workspace confinement: Image inputs and exports reside exclusively inside `~/Desktop/friday workspace/`.
   - Private session enforcement: OCR data processed entirely in-memory; disk exports, caching, and persistence suppressed.

5. **Prompt Injection Containment & Sensitive Redaction**:
   - Extracted OCR text is treated strictly as **untrusted data**, never as executable instructions or tool triggers.
   - Automated regex scanning for prompt-injection markers (`ignore previous instructions`, `rm -rf`, system overrides).
   - Sensitive credentials (API keys, AWS tokens, passwords) are automatically redacted before logging.

---

## 3. CLI Commands & Usage

```bash
# Inspect runtime OCR languages and engine revisions
python -m friday.cli --inspect-ocr-languages

# Check operational OCR readiness status
python -m friday.cli --ocr-status

# Extract text from an authorized workspace image with JSON export
python -m friday.cli --ocr-image "$HOME/Desktop/friday workspace/images/sample.png" --ocr-export json

# Extract text with custom languages
python -m friday.cli --ocr-image "$HOME/Desktop/friday workspace/images/hindi_sample.png" --ocr-languages "hi-IN,en-US"

# Run end-to-end performance and accuracy benchmark
python -m friday.cli --benchmark-ocr
```

---

## 4. Benchmark & Performance Profile (Apple Silicon M1, 8GB RAM)

Measured using `scripts/milestone_7_2_validation.py` and `--benchmark-ocr`:

| Metric | Target | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Cold Inference Latency** | < 0.60 s | **0.228 s** (228.0 ms) | PASS |
| **Warm Inference Latency (avg)** | < 0.30 s | **0.183 s** (182.7 ms) | PASS |
| **Incremental RSS Memory** | < 40 MB | **0.09 MB** | PASS |
| **Peak Process RSS** | < 120 MB | **25.38 MB** | PASS |
| **Character Error Rate (CER - English)** | < 0.05 | **0.0000** (0.0%) | PASS |
| **Character Error Rate (CER - Hindi)** | < 0.10 | **0.0000** (0.0%) | PASS |
| **Word Error Rate (WER - Hinglish)** | < 0.10 | **0.0000** (0.0%) | PASS |
| **Resource Leakage after 10 runs** | < 5 MB | **0.00 MB** | PASS |
