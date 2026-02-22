"""Sentence-aware text chunker for embedding generation.

Splits text into overlapping chunks that respect sentence boundaries
where possible. See ADR-003 for the design rationale.
"""

import re

# Sentence-ending punctuation followed by whitespace or end of string
_SENTENCE_END = re.compile(r"(?<=[.!?])(?:\s+)")


class TextChunker:
    """Splits text into overlapping chunks for embedding.

    Prefers sentence boundaries when splitting. Falls back to character
    boundaries for sentences longer than chunk_size.
    """

    def __init__(
        self, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[str]:
        """Split text into overlapping chunks.

        Returns an empty list for empty or whitespace-only text.
        Returns a single-element list if the text fits in one chunk.
        """
        text = text.strip()
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        sentences = _SENTENCE_END.split(text)
        # Filter out empty strings from split
        sentences = [s for s in sentences if s.strip()]

        chunks: list[str] = []
        current = ""

        for sentence in sentences:
            candidate = (current + " " + sentence).strip() if current else sentence

            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                    # Start next chunk with overlap from the end of current
                    overlap_text = current[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                    current = (overlap_text + " " + sentence).strip()
                else:
                    # Single sentence exceeds chunk_size — force-split it
                    current = sentence

                # If current still exceeds chunk_size (long sentence), force-split
                while len(current) > self.chunk_size:
                    # Split at chunk_size boundary
                    split_at = self.chunk_size
                    # Try to split at a space
                    space_pos = current.rfind(" ", 0, split_at)
                    if space_pos > self.chunk_size // 2:
                        split_at = space_pos

                    chunks.append(current[:split_at].rstrip())
                    overlap_start = max(0, split_at - self.chunk_overlap)
                    current = current[overlap_start:].lstrip()

        if current:
            chunks.append(current)

        return chunks
