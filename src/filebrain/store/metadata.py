"""SQLite-backed metadata store for tracking file state through the pipeline.

Stores file identity (path + content hash), metadata (size, mtime, type),
extraction results (text), and processing status. Supports change detection
via hash comparison and status-based queries for pipeline resumability.
"""

import enum
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


class FileStatus(enum.Enum):
    """Processing status of a file in the pipeline."""

    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass
class FileRecord:
    """A single file's metadata and processing state."""

    path: Path
    content_hash: str
    size: int
    mtime: float
    file_type: str
    status: FileStatus
    extracted_text: str | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    processed_at: str | None = None


_SCHEMA = """\
CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime REAL NOT NULL,
    file_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    extracted_text TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    processed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
"""


def _now() -> str:
    """UTC timestamp as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _row_to_record(row: sqlite3.Row) -> FileRecord:
    """Convert a database row to a FileRecord."""
    return FileRecord(
        path=Path(row["path"]),
        content_hash=row["content_hash"],
        size=row["size"],
        mtime=row["mtime"],
        file_type=row["file_type"],
        status=FileStatus(row["status"]),
        extracted_text=row["extracted_text"],
        error_message=row["error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        processed_at=row["processed_at"],
    )


class MetadataStore:
    """SQLite store for file metadata and processing state.

    Each file is identified by its absolute path. The store supports
    upsert (insert-or-update), change detection via content hash
    comparison, and queries by processing status.
    """

    def __init__(self, db_path: Path) -> None:
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def upsert_file(
        self,
        path: Path,
        content_hash: str,
        size: int,
        mtime: float,
        file_type: str,
    ) -> None:
        """Insert a new file record or update an existing one.

        If the file already exists and its content_hash has changed,
        the status resets to PENDING and extracted_text is cleared.
        If the hash is unchanged, only mtime/size are updated and
        the existing status and extracted_text are preserved.
        """
        now = _now()
        existing = self.get_file(path)

        if existing is None:
            self._conn.execute(
                """INSERT INTO files
                   (path, content_hash, size, mtime, file_type, status,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(path), content_hash, size, mtime, file_type,
                 FileStatus.PENDING.value, now, now),
            )
        elif existing.content_hash != content_hash:
            # File changed — reset to pending
            self._conn.execute(
                """UPDATE files
                   SET content_hash=?, size=?, mtime=?, file_type=?,
                       status=?, extracted_text=NULL, error_message=NULL,
                       processed_at=NULL, updated_at=?
                   WHERE path=?""",
                (content_hash, size, mtime, file_type,
                 FileStatus.PENDING.value, now, str(path)),
            )
        else:
            # Same hash — update mtime/size but preserve status
            self._conn.execute(
                """UPDATE files
                   SET size=?, mtime=?, updated_at=?
                   WHERE path=?""",
                (size, mtime, now, str(path)),
            )
        self._conn.commit()

    def get_file(self, path: Path) -> FileRecord | None:
        """Retrieve a file record by path, or None if not found."""
        cursor = self._conn.execute(
            "SELECT * FROM files WHERE path=?", (str(path),)
        )
        row = cursor.fetchone()
        return _row_to_record(row) if row else None

    def has_changed(self, path: Path, content_hash: str) -> bool:
        """Return True if the file is new or its content hash differs."""
        existing = self.get_file(path)
        if existing is None:
            return True
        return existing.content_hash != content_hash

    def get_files_by_status(self, status: FileStatus) -> list[FileRecord]:
        """Return all file records with the given status."""
        cursor = self._conn.execute(
            "SELECT * FROM files WHERE status=?", (status.value,)
        )
        return [_row_to_record(row) for row in cursor.fetchall()]

    def mark_processed(self, path: Path, extracted_text: str) -> None:
        """Mark a file as successfully processed with its extracted text."""
        now = _now()
        cursor = self._conn.execute(
            """UPDATE files
               SET status=?, extracted_text=?, error_message=NULL,
                   processed_at=?, updated_at=?
               WHERE path=?""",
            (FileStatus.PROCESSED.value, extracted_text, now, now, str(path)),
        )
        if cursor.rowcount == 0:
            raise KeyError(f"No file record for path: {path}")
        self._conn.commit()

    def mark_failed(self, path: Path, error_message: str) -> None:
        """Mark a file as failed with an error message."""
        now = _now()
        cursor = self._conn.execute(
            """UPDATE files
               SET status=?, error_message=?, updated_at=?
               WHERE path=?""",
            (FileStatus.FAILED.value, error_message, now, str(path)),
        )
        if cursor.rowcount == 0:
            raise KeyError(f"No file record for path: {path}")
        self._conn.commit()

    def delete_file(self, path: Path) -> None:
        """Remove a file record. No-op if the path doesn't exist."""
        self._conn.execute("DELETE FROM files WHERE path=?", (str(path),))
        self._conn.commit()

    def count_by_status(self) -> dict[FileStatus, int]:
        """Return a count of files for each status."""
        cursor = self._conn.execute(
            "SELECT status, COUNT(*) as cnt FROM files GROUP BY status"
        )
        counts = {s: 0 for s in FileStatus}
        for row in cursor.fetchall():
            counts[FileStatus(row["status"])] = row["cnt"]
        return counts
