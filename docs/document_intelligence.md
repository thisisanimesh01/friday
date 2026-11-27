# Visual Document Understanding & Intelligence (Milestone 7.4)

## Architecture Overview

Milestone 7.4 introduces an offline-capable, privacy-confined Document Intelligence engine designed specifically for macOS (Apple Silicon M1, 8GB RAM). The engine unifies digital and scanned document ingestion, table and receipt extraction, extractive and LLM-grounded summarization, and interactive Q&A.

```
                           +--------------------------+
                           | Authorized Workspace File |
                           | (~/Desktop/friday.../)   |
                           +------------+-------------+
                                        |
                         [ PrivacyGuard Validation ]
                                        |
               +------------------------+-----------------------+
               |                                                |
        [ Digital Document ]                             [ Scanned / Image ]
     (.pdf, .txt, .md, .csv)                        (.pdf scanned, .png, .jpg)
               |                                                |
      [ Native PDFKit / Text ]                        [ Page-by-Page Rendering ]
      (Instant ~10-30ms/page)                                    |
               |                                      [ Apple Vision Swift OCR ]
               |                                     (VNRecognizeTextRequest)
               +------------------------+-----------------------+
                                        |
                         +--------------v--------------+
                         | DocumentAnalysisResult      |
                         | - Page citations ([Page N]) |
                         | - Markdown/CSV Tables       |
                         | - Deterministic Math Totals |
                         | - Prompt-Injection Scanner  |
                         +--------------+--------------+
                                        |
               +------------------------+-----------------------+
               |                                                |
     [ Deterministic Export ]                         [ Grounded Local LLM ]
    (txt, md, json in exports/)                       (Ollama qwen2.5:3b)
```

## Key Capabilities

1. **Dual Extraction Strategy**:
   - **Digital Documents**: Automatically detects native text layers via CoreGraphics / `PDFKit` with zero OCR overhead (~10–30ms per page).
   - **Scanned Documents & Images**: Bounded, page-by-page rendering to PNG (releasing image buffers page by page to avoid M1 8GB memory pressure), evaluated via native Apple Vision Swift OCR (`VNRecognizeTextRequest`).

2. **Deterministic Intelligence & Hallucination Resistance**:
   - **Deterministic Invoice & Receipt Math**: Automatically detects itemized amounts and declared totals; performs deterministic calculations in Python and flags arithmetic discrepancies.
   - **Table Extraction**: Reconstructs Markdown and delimiter-separated tables without LLM guesswork.
   - **Strict Grounding & Citations**: Requires explicit page citations (e.g. `[Page 1]`) in summaries and answers. If information is not in the document, explicitly states that the document does not contain the answer.

3. **Untrusted Data Handling & Prompt-Injection Neutralization**:
   - Content found within documents is treated as untrusted data.
   - Documents are scanned for prompt-injection markers (`ignore previous instructions`, `system override`, `you are now DAN`).
   - If an injection attempt is detected, an advisory alert is flagged and processing is strictly constrained to safe preview mode.

4. **PrivacyGuard Enclosure & Ephemeral Mode**:
   - Strictly enforces access only to files within the designated workspace (`~/Desktop/friday workspace/`).
   - Hard blocks sensitive directories (`~/Desktop/me and she/`, `~/Library/Messages`, `~/.ssh`).
   - All document exports are written exclusively to `~/Desktop/friday workspace/exports/`.
   - Ephemeral mode (`FRIDAY_MODE=private`): runs completely in-memory without persistent disk cache.

## CLI Usage

```bash
# Inspect a document (pages, structure, provenance)
friday --inspect-document "documents/sample.pdf"

# Summarize a document
friday --summarize-doc "documents/report.pdf"

# Ask a grounded question
friday --ask-doc "documents/report.pdf" --question "What was the revenue growth?"

# Extract tables
friday --extract-table "documents/metrics.csv"

# Export document analysis (txt, md, json)
friday --export-doc "documents/report.pdf" --export-format json

# Run benchmark
friday --benchmark-doc "documents/report.pdf"
```

## Natural Language Routing

- *"inspect document /Users/animeshyadav/Desktop/friday workspace/documents/notes.txt"*
- *"summarize doc /Users/animeshyadav/Desktop/friday workspace/documents/sample.pdf"*
- *"document summarize karo /Users/animeshyadav/Desktop/friday workspace/documents/report.pdf"*
