# Storage Layer

Filebrain uses two databases: SQLite for file metadata and Qdrant for vector embeddings.

## MetadataStore (SQLite)

**File:** `src/filebrain/store/metadata.py`
**Tests:** `tests/test_store/test_metadata.py` (23 tests)

Tracks every file the system knows about. The schema:

| Column | Type | Purpose |
|--------|------|---------|
| path | TEXT PK | Absolute file path (unique identity) |
| content_hash | TEXT | SHA-256 of contents for change detection |
| size | INTEGER | File size in bytes |
| mtime | REAL | Modification time (seconds since epoch) |
| file_type | TEXT | Extension (e.g. '.pdf') |
| status | TEXT | 'pending', 'processed', or 'failed' |
| extracted_text | TEXT | Full extracted text (nullable) |
| error_message | TEXT | Failure reason (nullable) |
| created_at | TEXT | ISO timestamp |
| updated_at | TEXT | ISO timestamp |
| processed_at | TEXT | ISO timestamp (nullable) |

### Key Methods

- `upsert_file(path, hash, size, mtime, type)` — insert or update; resets status to pending if hash changed
- `get_file(path) → FileRecord | None`
- `has_changed(path, hash) → bool` — True if file is new or hash differs
- `get_files_by_status(status) → list[FileRecord]`
- `mark_processed(path, extracted_text)` — sets status + text + processed_at
- `mark_failed(path, error_message)` — sets status + error
- `delete_file(path)` — removes record (for deleted files)
- `count_by_status() → dict[FileStatus, int]` — for status reporting

### Threading

Uses `check_same_thread=False` and WAL journal mode for safe cross-thread access
(needed by the watchdog observer thread).

## VectorStore (Qdrant)

**File:** `src/filebrain/store/vector.py`
**Tests:** `tests/test_store/test_vector.py` (12 tests)

Stores 768-dimensional embeddings (from nomic-embed-text) with source file metadata.
Uses Qdrant in local embedded mode — no server process.

### Key Methods

- `add_embedding(source_path, chunk_index, chunk_text, embedding)` — stores one chunk's vector
- `search(query_embedding, limit) → list[SearchResult]` — cosine similarity search
- `delete_by_source_path(path)` — removes all chunks for a file
- `count() → int` — total embedding count
- `close()` — cleanup

### Storage

- In-memory mode: `VectorStore(dimensions=768)` — for testing
- Persistent mode: `VectorStore(dimensions=768, path=Path("./vectors"))` — for production

Embeddings are indexed with HNSW (Hierarchical Navigable Small World) for fast
approximate nearest-neighbor search.
