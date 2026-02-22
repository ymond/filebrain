"""Tests for the Qdrant-backed vector store.

TDD Red phase: these tests define the VectorStore interface.
The store manages embeddings with source file metadata and supports
semantic similarity search and cleanup on file deletion.
"""

from pathlib import Path

import pytest

from filebrain.store.vector import SearchResult, VectorStore

# nomic-embed-text produces 768-dimensional vectors
DIMS = 768


@pytest.fixture
def store() -> VectorStore:
    """Create an in-memory VectorStore for testing."""
    return VectorStore(dimensions=DIMS)


# --- Initialization ---


class TestStoreInit:
    """VectorStore creates its collection on init."""

    def test_creates_in_memory_store(self) -> None:
        store = VectorStore(dimensions=DIMS)
        assert store is not None

    def test_creates_persistent_store(self, tmp_path: Path) -> None:
        store = VectorStore(dimensions=DIMS, path=tmp_path / "vectors")
        store.add_embedding(
            source_path=Path("/a.txt"),
            chunk_index=0,
            chunk_text="hello",
            embedding=[0.1] * DIMS,
        )
        store.close()

        # Reopen and verify persistence
        store2 = VectorStore(dimensions=DIMS, path=tmp_path / "vectors")
        results = store2.search([0.1] * DIMS, limit=1)
        assert len(results) == 1
        assert results[0].source_path == Path("/a.txt")
        store2.close()


# --- Storing embeddings ---


class TestAddEmbedding:
    """add_embedding stores a vector with file reference metadata."""

    def test_add_and_search_single_embedding(self, store: VectorStore) -> None:
        store.add_embedding(
            source_path=Path("/docs/paper.pdf"),
            chunk_index=0,
            chunk_text="Neural networks are computational models...",
            embedding=[0.5] * DIMS,
        )
        results = store.search([0.5] * DIMS, limit=1)
        assert len(results) == 1
        assert results[0].source_path == Path("/docs/paper.pdf")
        assert results[0].chunk_index == 0
        assert results[0].chunk_text == "Neural networks are computational models..."
        assert results[0].score > 0.9  # cosine similarity to itself should be ~1.0

    def test_add_multiple_chunks_from_same_file(self, store: VectorStore) -> None:
        store.add_embedding(Path("/a.txt"), 0, "chunk zero", [0.1] * DIMS)
        store.add_embedding(Path("/a.txt"), 1, "chunk one", [0.2] * DIMS)
        store.add_embedding(Path("/a.txt"), 2, "chunk two", [0.3] * DIMS)

        results = store.search([0.3] * DIMS, limit=10)
        paths = {r.source_path for r in results}
        assert Path("/a.txt") in paths
        assert len(results) == 3


# --- Semantic search ---


class TestSearch:
    """search returns results ranked by cosine similarity."""

    def test_returns_ranked_results(self, store: VectorStore) -> None:
        # Create vectors that are clearly different in direction
        close_vec = [1.0] + [0.0] * (DIMS - 1)
        far_vec = [0.0] * (DIMS - 1) + [1.0]
        query_vec = [0.9] + [0.0] * (DIMS - 1)  # close to close_vec

        store.add_embedding(Path("/close.txt"), 0, "close", close_vec)
        store.add_embedding(Path("/far.txt"), 0, "far", far_vec)

        results = store.search(query_vec, limit=2)
        assert len(results) == 2
        assert results[0].source_path == Path("/close.txt")
        assert results[1].source_path == Path("/far.txt")
        assert results[0].score > results[1].score

    def test_respects_limit(self, store: VectorStore) -> None:
        for i in range(10):
            store.add_embedding(Path(f"/{i}.txt"), 0, f"text {i}", [float(i)] * DIMS)

        results = store.search([5.0] * DIMS, limit=3)
        assert len(results) == 3

    def test_search_result_has_all_fields(self, store: VectorStore) -> None:
        store.add_embedding(Path("/a.txt"), 2, "the text", [0.5] * DIMS)

        results = store.search([0.5] * DIMS, limit=1)
        result = results[0]
        assert isinstance(result, SearchResult)
        assert isinstance(result.source_path, Path)
        assert isinstance(result.chunk_index, int)
        assert isinstance(result.chunk_text, str)
        assert isinstance(result.score, float)

    def test_search_empty_store_returns_empty(self, store: VectorStore) -> None:
        results = store.search([0.5] * DIMS, limit=5)
        assert results == []


# --- Deletion by source path ---


class TestDeleteBySourcePath:
    """delete_by_source_path removes all embeddings for a file."""

    def test_delete_removes_all_chunks(self, store: VectorStore) -> None:
        store.add_embedding(Path("/a.txt"), 0, "chunk 0", [0.1] * DIMS)
        store.add_embedding(Path("/a.txt"), 1, "chunk 1", [0.2] * DIMS)
        store.add_embedding(Path("/b.txt"), 0, "other", [0.5] * DIMS)

        store.delete_by_source_path(Path("/a.txt"))

        results = store.search([0.1] * DIMS, limit=10)
        paths = {r.source_path for r in results}
        assert Path("/a.txt") not in paths
        assert Path("/b.txt") in paths

    def test_delete_nonexistent_is_noop(self, store: VectorStore) -> None:
        """Deleting a path with no embeddings should not raise."""
        store.delete_by_source_path(Path("/no/such/file.txt"))


# --- Count ---


class TestCount:
    """count returns the total number of stored embeddings."""

    def test_count_after_adds(self, store: VectorStore) -> None:
        assert store.count() == 0
        store.add_embedding(Path("/a.txt"), 0, "text", [0.1] * DIMS)
        store.add_embedding(Path("/a.txt"), 1, "text", [0.2] * DIMS)
        assert store.count() == 2

    def test_count_after_delete(self, store: VectorStore) -> None:
        store.add_embedding(Path("/a.txt"), 0, "text", [0.1] * DIMS)
        store.add_embedding(Path("/b.txt"), 0, "text", [0.2] * DIMS)
        store.delete_by_source_path(Path("/a.txt"))
        assert store.count() == 1
