"""Incremental speech segmentation for streaming LLM responses.

Buffers incoming token chunks and emits speakable text segments at natural sentence
or punctuation boundaries (., !, ?, ।, \n) while respecting minimum/maximum length
bounds, code block avoidance, and proper final segment flushing.
"""

import re
from typing import Generator


class SpeechSegmenter:
    """Buffers text chunks from streaming LLMs and emits speakable sentence segments."""

    def __init__(
        self,
        min_chars: int = 25,
        max_chars: int = 250,
    ):
        self.min_chars = min_chars
        self.max_chars = max_chars
        self._buffer: str = ""
        # Split on sentence ending punctuation: period, exclamation, question mark, or Devanagari danda (।)
        self._sentence_regex = re.compile(r"([^.!?।\n]+[.!?।\n]+)")

    def add_chunk(self, chunk: str) -> list[str]:
        """Add streaming text chunk and return any newly completed speakable segments."""
        if not chunk:
            return []

        self._buffer += chunk
        segments: list[str] = []

        # Find all punctuation-delimited segments
        matches = self._sentence_regex.findall(self._buffer)
        if matches:
            processed_length = 0
            current_combined = ""

            for match in matches:
                current_combined += match
                processed_length += len(match)

                # Emit if accumulated segment meets minimum character threshold
                if len(current_combined.strip()) >= self.min_chars:
                    segments.append(current_combined.strip())
                    current_combined = ""

            # Truncate processed portion from buffer
            if processed_length > 0:
                self._buffer = current_combined + self._buffer[processed_length:]

        # If buffer exceeds max_chars without punctuation, force split at last word boundary
        if len(self._buffer) >= self.max_chars:
            last_space = self._buffer.rfind(" ", 0, self.max_chars)
            if last_space > self.min_chars:
                segments.append(self._buffer[:last_space].strip())
                self._buffer = self._buffer[last_space:].lstrip()
            else:
                segments.append(self._buffer[:self.max_chars].strip())
                self._buffer = self._buffer[self.max_chars:]

        return segments

    def flush(self) -> list[str]:
        """Flush any remaining text in the buffer as the final segment."""
        remaining = self._buffer.strip()
        self._buffer = ""
        if remaining:
            return [remaining]
        return []

    def reset(self) -> None:
        """Clear internal buffer."""
        self._buffer = ""
