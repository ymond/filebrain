"""Tests for the query engine.

TDD Red phase: these tests define the QueryEngine interface.
The engine performs semantic search and optionally asks the LLM for
a natural language answer with source citations.

Unit tests use fake embeddings. Integration tests with ollama are
marked with @ollama.
"""

import hashlib
import urllib.request
from pathlib import Path

import pytest

from filebrain.query.engine import QueryEngine, SearchOnlyEngine
from filebrain.store.vector import VectorStore

DIMS = 768


class FakeEmbeddingGenerator:
    """Deterministic embeddings for testing search without ollama."""

    def embed(self, text: str) -> list[float]:
        h = hashlib.md5(text.encode()).hexdigest()
        return [int(c, 16) / 15.0 for c in h] * (DIMS // 32)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


def _ollama_available() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


ollama = pytest.mark.skipif(
    not _ollama_available(), reason="ollama not running"
)


# --- Semantic search (no LLM needed) ---


class TestSearchOnlyEngine:
    """SearchOnlyEngine returns file paths ranked by similarity."""

    def test_returns_relevant_files(self) -> None:
        vectors = VectorStore(dimensions=DIMS)
        embedder = FakeEmbeddingGenerator()
        engine = SearchOnlyEngine(vector_store=vectors, embedding_generator=embedder)

        # Add some documents
        vectors.add_embedding(
            Path("/docs/python.txt"), 0,
            "Python is a programming language", embedder.embed("Python is a programming language")
        )
        vectors.add_embedding(
            Path("/docs/cooking.txt"), 0,
            "How to make pasta", embedder.embed("How to make pasta")
        )

        results = engine.search("programming language")
        assert len(results) >= 1
        # All results have required fields
        for r in results:
            assert r.source_path is not None
            assert r.chunk_text is not None
            assert r.score is not None

    def test_returns_empty_on_no_data(self) -> None:
        vectors = VectorStore(dimensions=DIMS)
        embedder = FakeEmbeddingGenerator()
        engine = SearchOnlyEngine(vector_store=vectors, embedding_generator=embedder)
        results = engine.search("anything")
        assert results == []

    def test_respects_limit(self) -> None:
        vectors = VectorStore(dimensions=DIMS)
        embedder = FakeEmbeddingGenerator()
        engine = SearchOnlyEngine(vector_store=vectors, embedding_generator=embedder)

        for i in range(10):
            vectors.add_embedding(
                Path(f"/file{i}.txt"), 0, f"text {i}",
                embedder.embed(f"text {i}")
            )

        results = engine.search("text", limit=3)
        assert len(results) == 3


# --- LLM-powered query with citations ---


@ollama
class TestQueryEngine:
    """QueryEngine uses an LLM to answer questions citing source files."""

    @pytest.fixture
    def engine(self) -> QueryEngine:
        from filebrain.embeddings.generator import EmbeddingGenerator
        vectors = VectorStore(dimensions=DIMS)
        embedder = EmbeddingGenerator()
        engine = QueryEngine(
            vector_store=vectors,
            embedding_generator=embedder,
        )

        # Index some test content
        texts = {
            Path("/docs/python_guide.txt"): "Python is a high-level programming language created by Guido van Rossum. It emphasizes code readability and supports multiple programming paradigms.",
            Path("/docs/rust_guide.txt"): "Rust is a systems programming language focused on safety, speed, and concurrency. It was created by Mozilla.",
            Path("/notes/cooking.txt"): "To make a good pasta, boil water, add salt, and cook for 8-10 minutes.",
        }
        for path, text in texts.items():
            embedding = embedder.embed(text)
            vectors.add_embedding(path, 0, text, embedding)

        return engine

    def test_returns_answer_with_citations(self, engine: QueryEngine) -> None:
        answer = engine.query("What programming language was created by Guido van Rossum?")
        assert answer.text  # non-empty answer
        assert len(answer.sources) > 0  # at least one source cited
        # The answer should reference the python guide
        source_paths = {s.source_path for s in answer.sources}
        assert Path("/docs/python_guide.txt") in source_paths

    def test_answer_cites_real_file_paths(self, engine: QueryEngine) -> None:
        answer = engine.query("Tell me about Rust programming")
        # All cited paths should be from our indexed files
        known_paths = {
            Path("/docs/python_guide.txt"),
            Path("/docs/rust_guide.txt"),
            Path("/notes/cooking.txt"),
        }
        for source in answer.sources:
            assert source.source_path in known_paths, (
                f"Cited unknown path: {source.source_path}"
            )

    def test_query_returns_structured_result(self, engine: QueryEngine) -> None:
        answer = engine.query("What is Python?")
        assert hasattr(answer, "text")
        assert hasattr(answer, "sources")
        assert isinstance(answer.text, str)
        assert isinstance(answer.sources, list)
