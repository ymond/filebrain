"""Tests for the embedding generator.

TDD Red phase: these tests define the EmbeddingGenerator interface.
The generator calls ollama's embedding API to convert text into vectors.

These tests require a running ollama instance with nomic-embed-text pulled.
They are marked with @pytest.mark.ollama and skipped if ollama is unreachable.
"""

import urllib.request

import pytest

from filebrain.embeddings.generator import EmbeddingGenerator

# nomic-embed-text produces 768-dimensional vectors
EXPECTED_DIMS = 768


def _ollama_available() -> bool:
    """Check if ollama is running and reachable."""
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


ollama = pytest.mark.skipif(
    not _ollama_available(), reason="ollama not running"
)


@ollama
class TestEmbeddingGeneration:
    """EmbeddingGenerator produces vectors from text via ollama."""

    def test_generates_embedding_from_text(self) -> None:
        gen = EmbeddingGenerator()
        embedding = gen.embed("The quick brown fox jumps over the lazy dog.")
        assert isinstance(embedding, list)
        assert all(isinstance(v, float) for v in embedding)

    def test_embedding_has_correct_dimensionality(self) -> None:
        gen = EmbeddingGenerator()
        embedding = gen.embed("Test text for dimensionality check.")
        assert len(embedding) == EXPECTED_DIMS

    def test_different_texts_produce_different_embeddings(self) -> None:
        gen = EmbeddingGenerator()
        emb1 = gen.embed("Python is a programming language.")
        emb2 = gen.embed("The weather is sunny today.")
        # Embeddings should differ (not identical vectors)
        assert emb1 != emb2

    def test_similar_texts_have_high_cosine_similarity(self) -> None:
        gen = EmbeddingGenerator()
        emb1 = gen.embed("Machine learning is a subset of artificial intelligence.")
        emb2 = gen.embed("AI includes machine learning as a subfield.")
        # Compute cosine similarity
        dot = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = sum(a * a for a in emb1) ** 0.5
        norm2 = sum(b * b for b in emb2) ** 0.5
        similarity = dot / (norm1 * norm2)
        assert similarity > 0.7  # similar texts should have high similarity

    def test_embed_batch(self) -> None:
        gen = EmbeddingGenerator()
        texts = ["First text.", "Second text.", "Third text."]
        embeddings = gen.embed_batch(texts)
        assert len(embeddings) == 3
        assert all(len(e) == EXPECTED_DIMS for e in embeddings)

    def test_embed_batch_empty(self) -> None:
        gen = EmbeddingGenerator()
        assert gen.embed_batch([]) == []

    def test_custom_model_name(self) -> None:
        gen = EmbeddingGenerator(model="nomic-embed-text")
        embedding = gen.embed("Test with explicit model name.")
        assert len(embedding) == EXPECTED_DIMS
