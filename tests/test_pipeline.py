"""Tests for the processing pipeline.

TDD Red phase: these tests define the ProcessingPipeline interface.
The pipeline coordinates: file → extractor → chunker → embedder → stores.

Unit tests use mocks/fakes for the embedding generator (ollama) to keep
tests fast and deterministic. Integration tests with real ollama are
in a separate class with the ollama marker.
"""

import hashlib
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from filebrain.embeddings.chunker import TextChunker
from filebrain.embeddings.generator import EmbeddingGenerator
from filebrain.extractors.registry import ExtractorRegistry
from filebrain.pipeline import ProcessingPipeline
from filebrain.store.metadata import FileStatus, MetadataStore
from filebrain.store.vector import VectorStore

DIMS = 768


class FakeEmbeddingGenerator:
    """A fake that returns deterministic embeddings without calling ollama."""

    def embed(self, text: str) -> list[float]:
        # Use hash to produce a deterministic but unique vector
        h = hashlib.md5(text.encode()).hexdigest()
        return [int(c, 16) / 15.0 for c in h] * (DIMS // 32)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


@pytest.fixture
def tmp_setup(tmp_path: Path):
    """Set up all pipeline dependencies.

    The metadata DB lives in a separate directory from the scan target
    so that .db files don't get picked up by process_directory.
    """
    db_dir = tmp_path / "_db"
    db_dir.mkdir()
    scan_dir = tmp_path / "files"
    scan_dir.mkdir()
    metadata = MetadataStore(db_dir / "meta.db")
    vectors = VectorStore(dimensions=DIMS)
    registry = ExtractorRegistry()
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    embedder = FakeEmbeddingGenerator()
    pipeline = ProcessingPipeline(
        metadata_store=metadata,
        vector_store=vectors,
        extractor_registry=registry,
        chunker=chunker,
        embedding_generator=embedder,
    )
    return pipeline, metadata, vectors, scan_dir


class TestProcessFile:
    """pipeline.process_file extracts, chunks, embeds, and stores."""

    def test_processes_text_file_end_to_end(self, tmp_setup) -> None:
        pipeline, metadata, vectors, tmp_path = tmp_setup
        # Create a test file
        f = tmp_path / "hello.txt"
        f.write_text("This is a test file with some content for processing.")

        pipeline.process_file(f)

        # Check metadata store
        record = metadata.get_file(f)
        assert record is not None
        assert record.status == FileStatus.PROCESSED
        assert record.extracted_text is not None
        assert "test file" in record.extracted_text

        # Check vector store has embeddings
        assert vectors.count() >= 1

    def test_processes_python_file(self, tmp_setup) -> None:
        pipeline, metadata, vectors, tmp_path = tmp_setup
        f = tmp_path / "example.py"
        f.write_text('def hello():\n    """Say hello."""\n    print("hello")\n')

        pipeline.process_file(f)

        record = metadata.get_file(f)
        assert record is not None
        assert record.status == FileStatus.PROCESSED

    def test_stores_content_hash(self, tmp_setup) -> None:
        pipeline, metadata, _, tmp_path = tmp_setup
        f = tmp_path / "test.txt"
        f.write_text("deterministic content")

        pipeline.process_file(f)

        record = metadata.get_file(f)
        assert record is not None
        assert record.content_hash  # non-empty hash

    def test_long_text_produces_multiple_chunks(self, tmp_setup) -> None:
        pipeline, _, vectors, tmp_path = tmp_setup
        f = tmp_path / "long.txt"
        # Create text that exceeds chunk_size (100 chars)
        f.write_text("This is sentence one. " * 20)

        pipeline.process_file(f)

        # Multiple chunks should create multiple embeddings
        assert vectors.count() >= 2


class TestSkipUnchanged:
    """Pipeline skips files that haven't changed since last processing."""

    def test_skips_already_processed_file(self, tmp_setup) -> None:
        pipeline, metadata, vectors, tmp_path = tmp_setup
        f = tmp_path / "stable.txt"
        f.write_text("Stable content that does not change.")

        pipeline.process_file(f)
        count_after_first = vectors.count()

        # Process again — should skip (same content hash)
        pipeline.process_file(f)
        assert vectors.count() == count_after_first

    def test_reprocesses_when_content_changes(self, tmp_setup) -> None:
        pipeline, metadata, vectors, tmp_path = tmp_setup
        f = tmp_path / "changing.txt"
        f.write_text("Version one of the content.")

        pipeline.process_file(f)
        record_v1 = metadata.get_file(f)

        f.write_text("Version two with completely different content.")
        pipeline.process_file(f)

        record_v2 = metadata.get_file(f)
        assert record_v2 is not None
        assert record_v2.content_hash != record_v1.content_hash
        assert record_v2.status == FileStatus.PROCESSED


class TestFailureHandling:
    """Pipeline marks failed files and continues to next."""

    def test_marks_unsupported_file_as_failed(self, tmp_setup) -> None:
        pipeline, metadata, _, tmp_path = tmp_setup
        f = tmp_path / "mystery.xyz"
        f.write_bytes(b"\x00\x01\x02\x03")  # binary gibberish

        pipeline.process_file(f)

        record = metadata.get_file(f)
        assert record is not None
        assert record.status == FileStatus.FAILED
        assert record.error_message is not None

    def test_marks_missing_file_as_failed(self, tmp_setup) -> None:
        pipeline, metadata, _, tmp_path = tmp_setup
        f = tmp_path / "does_not_exist.txt"

        pipeline.process_file(f)

        record = metadata.get_file(f)
        assert record is not None
        assert record.status == FileStatus.FAILED

    def test_failure_does_not_crash_pipeline(self, tmp_setup) -> None:
        """Processing a bad file doesn't prevent processing the next one."""
        pipeline, metadata, _, tmp_path = tmp_setup

        bad = tmp_path / "bad.xyz"
        bad.write_bytes(b"\x00\x01")

        good = tmp_path / "good.txt"
        good.write_text("This is fine.")

        pipeline.process_file(bad)
        pipeline.process_file(good)

        assert metadata.get_file(bad).status == FileStatus.FAILED
        assert metadata.get_file(good).status == FileStatus.PROCESSED


class TestProcessDirectory:
    """pipeline.process_directory processes all supported files in a tree."""

    def test_processes_all_files_in_directory(self, tmp_setup) -> None:
        pipeline, metadata, _, tmp_path = tmp_setup

        (tmp_path / "a.txt").write_text("File A content.")
        (tmp_path / "b.md").write_text("# File B")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "c.py").write_text("x = 1\n")

        results = pipeline.process_directory(tmp_path)

        assert results["processed"] >= 3
        assert results["failed"] == 0

    def test_reports_stats(self, tmp_setup) -> None:
        pipeline, metadata, _, tmp_path = tmp_setup

        (tmp_path / "a.txt").write_text("Good file.")
        (tmp_path / "b.xyz").write_bytes(b"\x00")

        results = pipeline.process_directory(tmp_path)

        assert "processed" in results
        assert "failed" in results
        assert "skipped" in results
