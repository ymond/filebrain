"""Tests for the text chunker.

TDD Red phase: these tests define the TextChunker interface.
The chunker splits text into overlapping, sentence-aware segments
suitable for embedding generation.
"""

from filebrain.embeddings.chunker import TextChunker


class TestShortText:
    """Text shorter than chunk_size passes through as a single chunk."""

    def test_short_text_returns_single_chunk(self) -> None:
        chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
        chunks = chunker.chunk("This is a short sentence.")
        assert chunks == ["This is a short sentence."]

    def test_empty_text_returns_empty_list(self) -> None:
        chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
        assert chunker.chunk("") == []

    def test_whitespace_only_returns_empty_list(self) -> None:
        chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
        assert chunker.chunk("   \n\t  ") == []


class TestBasicChunking:
    """Longer texts are split into overlapping chunks."""

    def test_splits_long_text_into_multiple_chunks(self) -> None:
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2

    def test_all_chunks_within_size_limit(self) -> None:
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "Short one. Another short. Yet another. And more. Plus extra. Final bit."
        chunks = chunker.chunk(text)
        for chunk in chunks:
            assert len(chunk) <= 50 + 10  # allow some tolerance at sentence boundary

    def test_no_content_lost(self) -> None:
        """Every word in the original text appears in at least one chunk."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "Alpha bravo charlie. Delta echo foxtrot. Golf hotel india. Juliet kilo lima."
        chunks = chunker.chunk(text)
        all_chunk_text = " ".join(chunks)
        for word in text.split():
            # Strip punctuation for comparison
            clean_word = word.rstrip(".")
            assert clean_word in all_chunk_text, f"Word '{clean_word}' missing from chunks"


class TestOverlap:
    """Adjacent chunks share overlapping text for context continuity."""

    def test_adjacent_chunks_overlap(self) -> None:
        chunker = TextChunker(chunk_size=50, chunk_overlap=15)
        text = "Alpha bravo charlie. Delta echo foxtrot. Golf hotel india. Juliet kilo lima."
        chunks = chunker.chunk(text)
        if len(chunks) >= 2:
            # The end of chunk[0] and start of chunk[1] should share some text
            # We check that chunk[1] starts with text that appeared in chunk[0]
            overlap_region = chunks[1][:15]
            assert overlap_region in chunks[0], (
                f"Expected overlap region '{overlap_region}' to appear in previous chunk"
            )


class TestSentenceBoundaries:
    """Chunks prefer to break at sentence boundaries."""

    def test_prefers_sentence_boundary(self) -> None:
        chunker = TextChunker(chunk_size=60, chunk_overlap=10)
        text = "First sentence ends here. Second sentence goes on and on and on."
        chunks = chunker.chunk(text)
        # The first chunk should end at a sentence boundary if possible
        if len(chunks) >= 2:
            # First chunk should end with "here." not mid-word
            assert chunks[0].rstrip().endswith("here.")

    def test_handles_question_marks(self) -> None:
        chunker = TextChunker(chunk_size=40, chunk_overlap=5)
        text = "What is this? It is a test. Does it work? Yes it does."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2

    def test_handles_exclamation_marks(self) -> None:
        chunker = TextChunker(chunk_size=40, chunk_overlap=5)
        text = "Hello world! This is great! More text here! And even more!"
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2

    def test_long_sentence_falls_back_to_char_split(self) -> None:
        """A single sentence longer than chunk_size still gets split."""
        chunker = TextChunker(chunk_size=30, chunk_overlap=5)
        text = "This is one very long sentence that definitely exceeds the chunk size limit without any breaks"
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2
        # All original words should still be present
        all_text = " ".join(chunks)
        for word in text.split():
            assert word in all_text


class TestDefaults:
    """TextChunker uses sensible defaults from ADR-003."""

    def test_default_chunk_size(self) -> None:
        chunker = TextChunker()
        assert chunker.chunk_size == 1000

    def test_default_overlap(self) -> None:
        chunker = TextChunker()
        assert chunker.chunk_overlap == 200
