"""Tests for the SQLite metadata store.

TDD Red phase: these tests define the MetadataStore interface.
The store tracks file identity, extraction state, and pipeline status.
"""

from pathlib import Path

import pytest

from filebrain.store.metadata import FileRecord, FileStatus, MetadataStore


@pytest.fixture
def store(tmp_path: Path) -> MetadataStore:
    """Create a MetadataStore backed by a temp SQLite database."""
    return MetadataStore(tmp_path / "test.db")


# --- Schema and initialization ---


class TestStoreInit:
    """MetadataStore creates its database and tables on first use."""

    def test_creates_database_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "new.db"
        MetadataStore(db_path)
        assert db_path.exists()

    def test_is_reentrant(self, tmp_path: Path) -> None:
        """Opening the same database twice doesn't corrupt it."""
        db_path = tmp_path / "reuse.db"
        store1 = MetadataStore(db_path)
        store1.upsert_file(
            path=Path("/a.txt"),
            content_hash="abc123",
            size=100,
            mtime=1000.0,
            file_type=".txt",
        )
        store2 = MetadataStore(db_path)
        assert store2.get_file(Path("/a.txt")) is not None


# --- Storing and retrieving file records ---


class TestUpsertAndGet:
    """upsert_file stores a record; get_file retrieves it by path."""

    def test_store_and_retrieve_by_path(self, store: MetadataStore) -> None:
        store.upsert_file(
            path=Path("/home/user/docs/paper.pdf"),
            content_hash="sha256_abc",
            size=2048,
            mtime=1700000000.0,
            file_type=".pdf",
        )
        record = store.get_file(Path("/home/user/docs/paper.pdf"))
        assert record is not None
        assert record.path == Path("/home/user/docs/paper.pdf")
        assert record.content_hash == "sha256_abc"
        assert record.size == 2048
        assert record.mtime == 1700000000.0
        assert record.file_type == ".pdf"
        assert record.status == FileStatus.PENDING
        assert record.extracted_text is None
        assert record.error_message is None

    def test_get_nonexistent_returns_none(self, store: MetadataStore) -> None:
        assert store.get_file(Path("/no/such/file.txt")) is None

    def test_upsert_updates_existing_record(self, store: MetadataStore) -> None:
        """Upserting the same path updates the record instead of duplicating."""
        store.upsert_file(
            path=Path("/a.txt"),
            content_hash="hash_v1",
            size=100,
            mtime=1000.0,
            file_type=".txt",
        )
        store.upsert_file(
            path=Path("/a.txt"),
            content_hash="hash_v2",
            size=200,
            mtime=2000.0,
            file_type=".txt",
        )
        record = store.get_file(Path("/a.txt"))
        assert record is not None
        assert record.content_hash == "hash_v2"
        assert record.size == 200
        assert record.mtime == 2000.0

    def test_upsert_resets_status_when_file_changes(
        self, store: MetadataStore
    ) -> None:
        """When a file is re-upserted with a new hash, status resets to pending."""
        store.upsert_file(
            path=Path("/a.txt"),
            content_hash="hash_v1",
            size=100,
            mtime=1000.0,
            file_type=".txt",
        )
        store.mark_processed(Path("/a.txt"), extracted_text="hello")
        store.upsert_file(
            path=Path("/a.txt"),
            content_hash="hash_v2",
            size=200,
            mtime=2000.0,
            file_type=".txt",
        )
        record = store.get_file(Path("/a.txt"))
        assert record is not None
        assert record.status == FileStatus.PENDING
        assert record.extracted_text is None

    def test_upsert_preserves_status_when_hash_unchanged(
        self, store: MetadataStore
    ) -> None:
        """When upserted with the same hash, the existing status is kept."""
        store.upsert_file(
            path=Path("/a.txt"),
            content_hash="same_hash",
            size=100,
            mtime=1000.0,
            file_type=".txt",
        )
        store.mark_processed(Path("/a.txt"), extracted_text="hello")
        # Re-upsert with same hash but different mtime (e.g. file was touched)
        store.upsert_file(
            path=Path("/a.txt"),
            content_hash="same_hash",
            size=100,
            mtime=2000.0,
            file_type=".txt",
        )
        record = store.get_file(Path("/a.txt"))
        assert record is not None
        assert record.status == FileStatus.PROCESSED
        assert record.extracted_text == "hello"

    def test_record_has_timestamps(self, store: MetadataStore) -> None:
        store.upsert_file(
            path=Path("/a.txt"),
            content_hash="abc",
            size=10,
            mtime=1000.0,
            file_type=".txt",
        )
        record = store.get_file(Path("/a.txt"))
        assert record is not None
        assert record.created_at is not None
        assert record.updated_at is not None


# --- Change detection ---


class TestChangeDetection:
    """has_changed returns True if the file is new or its hash differs."""

    def test_new_file_has_changed(self, store: MetadataStore) -> None:
        assert store.has_changed(Path("/new.txt"), "any_hash") is True

    def test_same_hash_has_not_changed(self, store: MetadataStore) -> None:
        store.upsert_file(
            path=Path("/a.txt"),
            content_hash="hash1",
            size=100,
            mtime=1000.0,
            file_type=".txt",
        )
        assert store.has_changed(Path("/a.txt"), "hash1") is False

    def test_different_hash_has_changed(self, store: MetadataStore) -> None:
        store.upsert_file(
            path=Path("/a.txt"),
            content_hash="hash1",
            size=100,
            mtime=1000.0,
            file_type=".txt",
        )
        assert store.has_changed(Path("/a.txt"), "hash2") is True


# --- Querying by status ---


class TestQueryByStatus:
    """get_files_by_status returns all files with the given status."""

    def test_query_pending_files(self, store: MetadataStore) -> None:
        store.upsert_file(Path("/a.txt"), "h1", 10, 1000.0, ".txt")
        store.upsert_file(Path("/b.txt"), "h2", 20, 1000.0, ".txt")
        store.upsert_file(Path("/c.txt"), "h3", 30, 1000.0, ".txt")
        store.mark_processed(Path("/b.txt"), "text b")

        pending = store.get_files_by_status(FileStatus.PENDING)
        paths = {r.path for r in pending}
        assert paths == {Path("/a.txt"), Path("/c.txt")}

    def test_query_processed_files(self, store: MetadataStore) -> None:
        store.upsert_file(Path("/a.txt"), "h1", 10, 1000.0, ".txt")
        store.mark_processed(Path("/a.txt"), "text a")

        processed = store.get_files_by_status(FileStatus.PROCESSED)
        assert len(processed) == 1
        assert processed[0].path == Path("/a.txt")

    def test_query_failed_files(self, store: MetadataStore) -> None:
        store.upsert_file(Path("/a.txt"), "h1", 10, 1000.0, ".txt")
        store.mark_failed(Path("/a.txt"), "corrupt PDF")

        failed = store.get_files_by_status(FileStatus.FAILED)
        assert len(failed) == 1
        assert failed[0].error_message == "corrupt PDF"

    def test_empty_status_returns_empty_list(self, store: MetadataStore) -> None:
        assert store.get_files_by_status(FileStatus.PROCESSED) == []


# --- Status transitions ---


class TestStatusTransitions:
    """mark_processed and mark_failed update status and related fields."""

    def test_mark_processed_stores_text(self, store: MetadataStore) -> None:
        store.upsert_file(Path("/a.txt"), "h1", 10, 1000.0, ".txt")
        store.mark_processed(Path("/a.txt"), "extracted content")

        record = store.get_file(Path("/a.txt"))
        assert record is not None
        assert record.status == FileStatus.PROCESSED
        assert record.extracted_text == "extracted content"
        assert record.processed_at is not None

    def test_mark_failed_stores_error(self, store: MetadataStore) -> None:
        store.upsert_file(Path("/a.txt"), "h1", 10, 1000.0, ".txt")
        store.mark_failed(Path("/a.txt"), "extraction failed: corrupt file")

        record = store.get_file(Path("/a.txt"))
        assert record is not None
        assert record.status == FileStatus.FAILED
        assert record.error_message == "extraction failed: corrupt file"

    def test_mark_processed_nonexistent_raises(self, store: MetadataStore) -> None:
        with pytest.raises(KeyError):
            store.mark_processed(Path("/no.txt"), "text")

    def test_mark_failed_nonexistent_raises(self, store: MetadataStore) -> None:
        with pytest.raises(KeyError):
            store.mark_failed(Path("/no.txt"), "error")


# --- Deletion ---


class TestDeletion:
    """delete_file removes a record entirely."""

    def test_delete_existing_file(self, store: MetadataStore) -> None:
        store.upsert_file(Path("/a.txt"), "h1", 10, 1000.0, ".txt")
        store.delete_file(Path("/a.txt"))
        assert store.get_file(Path("/a.txt")) is None

    def test_delete_nonexistent_is_noop(self, store: MetadataStore) -> None:
        """Deleting a path that doesn't exist should not raise."""
        store.delete_file(Path("/no/such/file.txt"))  # no error


# --- Counting ---


class TestCounting:
    """count_by_status returns a dict of status -> count for reporting."""

    def test_count_with_mixed_statuses(self, store: MetadataStore) -> None:
        store.upsert_file(Path("/a.txt"), "h1", 10, 1000.0, ".txt")
        store.upsert_file(Path("/b.txt"), "h2", 20, 1000.0, ".txt")
        store.upsert_file(Path("/c.txt"), "h3", 30, 1000.0, ".txt")
        store.mark_processed(Path("/a.txt"), "text a")
        store.mark_failed(Path("/c.txt"), "error c")

        counts = store.count_by_status()
        assert counts[FileStatus.PENDING] == 1
        assert counts[FileStatus.PROCESSED] == 1
        assert counts[FileStatus.FAILED] == 1

    def test_count_empty_store(self, store: MetadataStore) -> None:
        counts = store.count_by_status()
        assert counts[FileStatus.PENDING] == 0
        assert counts[FileStatus.PROCESSED] == 0
        assert counts[FileStatus.FAILED] == 0
