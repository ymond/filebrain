[← Previous: The Extraction Layer](extractors.md) | [Table of Contents](README.md) | [Next: Python Project Anatomy →](project-anatomy.md)

---

# Chapter 4: The Storage Layer

> SQLite for metadata, Qdrant for vectors. Schema design, threading considerations, HNSW indexing, and why two databases are better than one.

---

## Why Two Databases?

This is the first question anyone asks, so let's address it directly: why not store everything in one database?

The answer is that metadata and embeddings have fundamentally different access patterns. Metadata is relational — you query it by exact match (`WHERE path = ?`), by status (`WHERE status = 'pending'`), by range (`WHERE mtime > ?`). This is what relational databases like SQLite are built for: B-tree indexes, SQL queries, ACID transactions.

Embeddings are spatial — you query them by proximity ("which vectors are closest to this query vector in 768-dimensional space?"). This requires specialized data structures like HNSW graphs, product quantization, and distance functions (cosine, euclidean, dot product). A relational database can technically store vectors in a BLOB column, but it can't *search* them efficiently.

So Filebrain uses each database for what it does best: SQLite for structured metadata with exact-match and range queries, Qdrant for high-dimensional vectors with approximate nearest-neighbor search. If you've worked with polyglot persistence in microservices (e.g., PostgreSQL for transactions, Redis for caching, Elasticsearch for search), this is the same principle applied within a single application.

The two databases reference each other through the file path — it's the shared key. When you delete a file, both databases need to be updated: remove the metadata row from SQLite and remove all embedding vectors for that path from Qdrant.

## MetadataStore (SQLite)

**Source:** `src/filebrain/store/metadata.py`
**Tests:** `tests/test_store/test_metadata.py` (23 tests)

### The Schema

The MetadataStore tracks every file the system knows about. Here's the table:

| Column | Type | Purpose |
|--------|------|---------|
| `path` | TEXT PK | Absolute file path — the unique identity of a file |
| `content_hash` | TEXT | SHA-256 of the file's contents, for change detection |
| `size` | INTEGER | File size in bytes |
| `mtime` | REAL | Modification time (seconds since epoch, from `os.stat`) |
| `file_type` | TEXT | Extension (e.g. `.pdf`), for filtering and stats |
| `status` | TEXT | `'pending'`, `'processed'`, or `'failed'` — the file's lifecycle state |
| `extracted_text` | TEXT | Full extracted text (nullable — only populated after processing) |
| `error_message` | TEXT | Failure reason (nullable — only populated on failure) |
| `created_at` | TEXT | ISO 8601 timestamp of when the record was first created |
| `updated_at` | TEXT | ISO 8601 timestamp of the most recent update |
| `processed_at` | TEXT | ISO 8601 timestamp of successful processing (nullable) |

A few design choices worth noting:

**`path` as the primary key.** This means each file can only have one record. If you scan the same directory twice, the second scan updates existing records rather than creating duplicates. The tradeoff: if a file moves (same content, different path), it looks like a delete + create. Tracking file identity across renames would require something like inode tracking, which is significantly more complex and was deferred.

**`content_hash` for change detection.** SHA-256 of the entire file contents. When the pipeline encounters a file, it computes the hash and compares it to what's stored. If they match, the file hasn't changed and processing is skipped. This is more reliable than comparing `mtime` (modification time) because mtime can change without content changing (`touch` does this) and content can change without mtime updating (restoring a file from backup to the same path). The cost is that you have to read the entire file to compute the hash, but for the file sizes Filebrain deals with (text documents, code, PDFs), this is negligible.

**`status` as a state machine.** Files move through a lifecycle: `pending` → `processed` or `pending` → `failed`. When a file's hash changes, it goes back to `pending` for reprocessing. This three-state machine is what makes the pipeline resumable — after a crash, you can restart and it picks up where it left off by processing all `pending` files.

**`extracted_text` stored in SQLite.** You might wonder why we store the full extracted text when we also store it as chunks in Qdrant. Two reasons: (1) it makes it easy to re-chunk and re-embed if chunking parameters change, without re-extracting from the source file; (2) it supports future features like full-text search as a complement to semantic search.

### Key Methods

The MetadataStore exposes a clean API that hides all SQL behind Python methods:

- `upsert_file(path, hash, size, mtime, type)` — Insert or update. Uses SQLite's `INSERT OR REPLACE`. If the hash changed, resets status to `pending` so the file gets reprocessed.
- `get_file(path) → FileRecord | None` — Fetch by primary key.
- `has_changed(path, hash) → bool` — Returns `True` if the file is new or its hash differs from what's stored. This is the pipeline's main check.
- `get_files_by_status(status) → list[FileRecord]` — For batch operations: "give me everything that's pending."
- `mark_processed(path, extracted_text)` — Sets status to `processed`, stores the text, sets `processed_at` timestamp.
- `mark_failed(path, error_message)` — Sets status to `failed`, stores the error message.
- `delete_file(path)` — Removes the record entirely (used when a file is deleted from disk).
- `count_by_status() → dict[FileStatus, int]` — For the `status` CLI command: "how many files are pending, processed, failed?"

If you've used Django's ORM or SQLAlchemy, this should feel familiar — it's the **Repository pattern**. The rest of the system never writes SQL. If we ever needed to migrate from SQLite to PostgreSQL (unlikely for a local-first tool, but architecturally possible), only this one file would change.

### Threading: WAL Mode

SQLite's default journal mode uses a rollback journal that locks the entire database for writes. If the watchdog thread tries to write while the main thread is reading, one of them blocks. In the worst case, you get the infamous `database is locked` error.

WAL (Write-Ahead Logging) mode solves this. Instead of modifying the database file directly, writes go to a separate WAL file. Readers continue reading from the main database file, unaware of pending writes. Periodically, the WAL is "checkpointed" — its contents are merged back into the main database.

The practical result: readers never block writers, and writers never block readers. Multiple readers can operate simultaneously. Only concurrent *writers* still serialize (but Filebrain only has one writer at a time in practice).

Enabled via:
```python
conn.execute("PRAGMA journal_mode=WAL")
```

Combined with `check_same_thread=False` on the connection (which disables Python's sqlite3 module's thread affinity check), this makes the MetadataStore safe for cross-thread access from the watchdog observer thread.

## VectorStore (Qdrant)

**Source:** `src/filebrain/store/vector.py`
**Tests:** `tests/test_store/test_vector.py` (12 tests)

### What It Stores

The VectorStore holds 768-dimensional embedding vectors (from `nomic-embed-text`) alongside payload data for each chunk:

- **Vector:** 768 floats representing the semantic meaning of a text chunk
- **Payload:** `source_path` (which file), `chunk_index` (position in file), `chunk_text` (the actual text)

Each chunk from a file becomes one point in the vector store. A 10-page PDF might produce 15-20 chunks, meaning 15-20 vectors stored in Qdrant. When you delete a file, all its vectors are removed via `delete_by_source_path(path)`, which filters by the `source_path` payload field.

### Key Methods

- `add_embedding(source_path, chunk_index, chunk_text, embedding)` — Stores one chunk's vector with its metadata payload.
- `search(query_embedding, limit) → list[SearchResult]` — Cosine similarity search. Returns the top-k most similar chunks.
- `delete_by_source_path(path)` — Removes all vectors associated with a file. Uses Qdrant's payload filtering.
- `count() → int` — Total number of stored vectors.
- `close()` — Cleanup (flushes data to disk in persistent mode).

### Modes of Operation

**In-memory mode** for testing:
```python
store = VectorStore(dimensions=768)  # no path — data lives in RAM
```

**Persistent mode** for production:
```python
store = VectorStore(dimensions=768, path=Path("~/.filebrain/vectors"))
```

In persistent mode, Qdrant writes its index and data to the specified directory. The data survives process restarts — you don't need to re-embed everything on each run. The `FakeEmbeddingGenerator` in tests produces deterministic vectors so that test assertions on search results are reproducible.

### HNSW: How Similarity Search Stays Fast

If you have 100,000 vectors and you need to find the 10 most similar to a query, the naive approach is to compute cosine similarity against all 100,000 and sort. This is O(n) per query — linear in the number of vectors. Fine for hundreds, slow for millions.

HNSW (Hierarchical Navigable Small World) is the standard algorithm for approximate nearest-neighbor search. It builds a multi-layer graph where each node is a vector and edges connect nearby vectors. The top layers are sparse (long-range connections for fast traversal), the bottom layers are dense (short-range connections for precision). A query starts at the top layer, greedily hops to the closest neighbor, drops to the next layer, and repeats until it reaches the bottom.

The result is O(log n) query time. The tradeoff: it's approximate — it might miss the true nearest neighbor in favor of a very close one. In practice, the recall is typically >95%, and the speed difference is dramatic. If you've used `annoy` (Spotify), `faiss` (Meta), or Elasticsearch's dense vector search, they all use variations of this approach.

Qdrant builds the HNSW index automatically as you insert vectors. You don't configure it manually — the defaults work well for Filebrain's scale (thousands to low millions of vectors).

### Why Qdrant Over ChromaDB

The original plan was ChromaDB — it's the most popular embedded vector database in the Python ecosystem, and its API is excellent. But ChromaDB 1.5.1 (the latest version at the time of implementation) depends on pydantic v1, which crashes on Python 3.14. This was a hard blocker.

Qdrant's local embedded mode provides the same key benefits — no server process, persistent storage to a directory on disk — with a more production-grade engine (Rust core, HNSW indexing, payload filtering). The full rationale is in [ADR-002](../decisions/002-vector-database.md).

The `VectorStore` abstraction means that if ChromaDB fixes its Python 3.14 compatibility (or a better option appears), the migration would be isolated to `src/filebrain/store/vector.py`. No other file imports Qdrant directly.

## Data Storage Locations

By default, both databases live in `~/.filebrain/`:

- `~/.filebrain/metadata.db` — the SQLite database
- `~/.filebrain/vectors/` — the Qdrant persistent storage directory

This can be overridden:
```bash
filebrain --db-dir /path/to/custom scan ~/Documents
```

The `--db-dir` flag points both databases to a different location. Useful for testing, for keeping indexes on a fast SSD, or for maintaining separate indexes for different directory trees.

---

[← Previous: The Extraction Layer](extractors.md) | [Table of Contents](README.md) | [Next: Python Project Anatomy →](project-anatomy.md)
