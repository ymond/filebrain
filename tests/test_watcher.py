"""Tests for the filesystem watcher.

TDD Red phase: these tests define the FileWatcher interface.
The watcher detects filesystem changes and feeds files to the pipeline.

Watcher tests use short timeouts and polling to be fast and deterministic.
"""

import hashlib
import time
from pathlib import Path

import pytest

from filebrain.embeddings.chunker import TextChunker
from filebrain.extractors.registry import ExtractorRegistry
from filebrain.pipeline import ProcessingPipeline
from filebrain.store.metadata import FileStatus, MetadataStore
from filebrain.store.vector import VectorStore
from filebrain.watcher.watcher import FileWatcher

DIMS = 768


class FakeEmbeddingGenerator:
    """A fake that returns deterministic embeddings without calling ollama."""

    def embed(self, text: str) -> list[float]:
        h = hashlib.md5(text.encode()).hexdigest()
        return [int(c, 16) / 15.0 for c in h] * (DIMS // 32)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


@pytest.fixture
def watcher_setup(tmp_path: Path):
    """Set up watcher with all dependencies."""
    db_dir = tmp_path / "_db"
    db_dir.mkdir()
    watch_dir = tmp_path / "watched"
    watch_dir.mkdir()

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
    watcher = FileWatcher(pipeline=pipeline, metadata_store=metadata, vector_store=vectors)
    return watcher, pipeline, metadata, vectors, watch_dir


class TestBatchScan:
    """FileWatcher.scan() processes all files in a directory tree."""

    def test_scan_processes_all_supported_files(self, watcher_setup) -> None:
        watcher, _, metadata, _, watch_dir = watcher_setup

        (watch_dir / "a.txt").write_text("File A content.")
        (watch_dir / "b.md").write_text("# File B\nSome markdown.")
        sub = watch_dir / "subdir"
        sub.mkdir()
        (sub / "c.py").write_text("x = 42\n")

        stats = watcher.scan(watch_dir)

        assert stats["processed"] >= 3
        assert metadata.get_file(watch_dir / "a.txt") is not None
        assert metadata.get_file(sub / "c.py") is not None

    def test_scan_skips_already_processed(self, watcher_setup) -> None:
        watcher, _, metadata, vectors, watch_dir = watcher_setup

        (watch_dir / "a.txt").write_text("Stable content.")
        watcher.scan(watch_dir)
        count1 = vectors.count()

        stats = watcher.scan(watch_dir)
        assert stats["skipped"] >= 1
        assert vectors.count() == count1

    def test_scan_picks_up_changed_files(self, watcher_setup) -> None:
        watcher, _, metadata, _, watch_dir = watcher_setup

        f = watch_dir / "a.txt"
        f.write_text("Version 1.")
        watcher.scan(watch_dir)

        f.write_text("Version 2 with different content.")
        stats = watcher.scan(watch_dir)
        assert stats["processed"] >= 1

        record = metadata.get_file(f)
        assert "Version 2" in record.extracted_text


class TestWatchEvents:
    """FileWatcher.watch() detects live filesystem events."""

    def test_detects_new_file(self, watcher_setup) -> None:
        watcher, _, metadata, _, watch_dir = watcher_setup

        watcher.start(watch_dir)
        try:
            (watch_dir / "new.txt").write_text("New file content.")
            # Give the watcher time to notice and process
            _wait_for(lambda: metadata.get_file(watch_dir / "new.txt") is not None,
                       timeout=5.0)
            record = metadata.get_file(watch_dir / "new.txt")
            assert record is not None
            assert record.status == FileStatus.PROCESSED
        finally:
            watcher.stop()

    def test_detects_modified_file(self, watcher_setup) -> None:
        watcher, pipeline, metadata, _, watch_dir = watcher_setup

        f = watch_dir / "mod.txt"
        f.write_text("Original.")
        pipeline.process_file(f)

        watcher.start(watch_dir)
        try:
            f.write_text("Modified content that is different.")
            _wait_for(
                lambda: (r := metadata.get_file(f)) is not None
                and "Modified" in (r.extracted_text or ""),
                timeout=5.0,
            )
            record = metadata.get_file(f)
            assert "Modified" in record.extracted_text
        finally:
            watcher.stop()

    def test_detects_deleted_file(self, watcher_setup) -> None:
        watcher, pipeline, metadata, vectors, watch_dir = watcher_setup

        f = watch_dir / "del.txt"
        f.write_text("To be deleted.")
        pipeline.process_file(f)
        assert vectors.count() >= 1

        watcher.start(watch_dir)
        try:
            f.unlink()
            _wait_for(
                lambda: metadata.get_file(watch_dir / "del.txt") is None,
                timeout=5.0,
            )
            # Embeddings should be cleaned up too
            results = vectors.search([0.0] * DIMS, limit=10)
            paths = {r.source_path for r in results}
            assert watch_dir / "del.txt" not in paths
        finally:
            watcher.stop()


def _wait_for(condition, timeout: float = 5.0, poll: float = 0.1) -> None:
    """Poll until condition() is truthy, or raise after timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(poll)
    raise TimeoutError(f"Condition not met within {timeout}s")
