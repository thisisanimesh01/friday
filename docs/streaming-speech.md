"""Comprehensive documentation of Real-Time Streaming Speech & Emotional Expression architecture."""

# Real-Time Streaming Speech & Context-Aware Emotional Expression (Milestone 4.4)

## Architecture Overview
Milestone 4.4 introduces sentence-level incremental speech synthesis and context-driven delivery expression:
- **SpeechSegmenter**: Buffers incoming token chunks from LLM streaming responses (`ask_friday_stream`) and yields speakable segments as soon as sentence or natural phrase punctuation (`.`, `!`, `?`, `।`, `\n`) is reached.
- **StreamingTTSCoordinator**: Feeds segments sequentially into `TTSEngine`, enabling speech playback to start on the first sentence before the entire response finishes.
- **SpeechExpression**: Evaluates conversational context to map delivery styles (`gentle`, `happy`, `focused`, `concerned`, `supportive`, `neutral`, `confident`), modulating speech pacing and volume appropriately.
- **Coordinated Cancellation**: Ensures `cancel()` immediately stops active playback, resets segmentation buffers, and discards stale segments.
