# From Storage to Search: Building the Complete Filebrain Pipeline

*Session 2, 2026-02-22*

Yesterday we built the foundation: a Python package with extractors that can pull
text from .txt, .md, .py, .pdf, and dozens of code file types. Today, we built
everything else. The extractors now feed into a complete pipeline that stores,
indexes, watches, and queries your files. By the end of this session, you can point
filebrain at a directory and ask it questions.

## The Storage Layer: Two Databases Working Together

Filebrain needs to store two fundamentally different things: **metadata about files**
(what file, when processed, what status) and **vector embeddings** (the mathematical
representations that make semantic search possible). These serve different purposes
and have different query patterns, so they live in different databases.

### SQLite for Metadata

`[pattern: Repository]` The `MetadataStore` wraps SQLite to track every file the
system knows about. The schema is straightforward:

```python
# Each file gets one row with these fields:
path        TEXT PRIMARY KEY   # absolute path = unique identity
content_hash TEXT              # SHA-256 of contents, for change detection
size, mtime  INTEGER/REAL     # file stats
status       TEXT              # 'pending', 'processed', or 'failed'
extracted_text TEXT            # the full extracted text (after extraction)
error_message  TEXT            # what went wrong (if failed)
created_at, updated_at, processed_at  TEXT  # ISO timestamps
```

The key design choice is using `path` as the primary key rather than an auto-increment
ID. Since every file has exactly one record, the path *is* the natural key. This
makes lookups O(1) and prevents duplicates by construction.

`[idiom]` The `upsert_file` method is the main entry point. "Upsert" means "insert
or update" — if the file is new, insert; if it already exists, update. But the clever
bit is what happens to the `status` field during an upsert:

- **Same content hash?** Keep the existing status. If the file was already processed,
  don't re-process it just because someone touched it.
- **Different content hash?** Reset to `pending`. The content changed, so previous
  extraction results are stale.

This is what makes the pipeline **resumable** — if processing is interrupted, pending
files get picked up on the next scan. If a file hasn't changed, it's skipped.

`[best practice]` SQLite's WAL (Write-Ahead Logging) mode is enabled for safe
concurrent access. More on why this matters below when we discuss the watcher.

### Qdrant for Vectors

The original plan was ChromaDB — a Python-native embedded vector database that's
popular for prototyping. But ChromaDB's latest version depends on pydantic v1
internally, and pydantic v1 crashes on Python 3.14. This is a good reminder that
**checking compatibility before committing to a dependency is worth the five minutes**.

Qdrant turned out to be a better choice anyway. `QdrantClient(path="./vectors")`
gives you a persistent vector database backed by local files — no server process
needed. The Python package bundles the Qdrant engine as a compiled Rust extension.
You get HNSW indexing (a fast approximate nearest-neighbor search algorithm) for free.

`[pattern: Adapter]` The `VectorStore` class wraps Qdrant so the rest of the pipeline
never imports `qdrant_client` directly. This abstraction makes it possible (though
not trivial) to swap vector databases later.

Each embedding is stored with three pieces of payload metadata:
- `source_path`: which file this chunk came from
- `chunk_index`: which chunk within that file (0, 1, 2...)
- `chunk_text`: the original text of the chunk

The `chunk_text` is stored in the payload rather than looked up from SQLite because
we need it for the RAG prompt — when the LLM generates an answer, it needs to see
the actual text, not just a reference.

## The Embedding Pipeline: Text to Vectors

Between extracting text and storing it as vectors, three things happen: chunking,
embedding, and orchestration.

### Chunking: Why and How

Embedding models work best on focused passages. Sending an entire 50-page PDF as
one embedding creates a vague, averaged-out vector that doesn't match specific
questions well. Instead, we split text into overlapping chunks.

`[best practice]` **Overlap** is the key insight. If you split "The quick brown fox"
into "The quick" and "brown fox" with no overlap, a search for "quick brown" matches
neither chunk well. With overlap, the second chunk starts with text from the end of
the first, so boundary information isn't lost.

The `TextChunker` targets 1000-character chunks with 200-character overlap and tries
to split at sentence boundaries (`.`, `?`, `!` followed by whitespace):

```python
# Sentence-aware splitting with overlap
chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk(long_text)
# ["First few sentences...", "...end of first. Next sentences...", ...]
```

`[idiom]` Python's `re.compile(r"(?<=[.!?])(?:\s+)")` uses a *lookbehind assertion*
to split after sentence-ending punctuation without consuming it. This keeps the
period attached to the sentence where it belongs.

### Embedding: Text to Numbers

The `EmbeddingGenerator` calls ollama's `/api/embed` endpoint — a local REST API.
No network calls, no API keys, no cloud. Notably, we use `urllib` from Python's
standard library rather than `requests` or `httpx`:

```python
# No external HTTP library needed — ollama's API is simple
payload = json.dumps({"model": "nomic-embed-text", "input": texts})
req = urllib.request.Request(url, data=payload.encode())
```

`[convention]` Using stdlib `urllib` instead of third-party HTTP libraries when the
use case is simple (no auth, no streaming, no complex headers) keeps the dependency
tree lighter. This is especially relevant for a project like filebrain that's meant
to run locally with minimal setup.

`nomic-embed-text` produces 768-dimensional vectors. The batch API (`"input": [list]`)
generates all embeddings in a single GPU pass, which is much faster than calling
embed() in a loop.

### The Pipeline: Wiring It All Together

`[pattern: Pipeline]` The `ProcessingPipeline` orchestrates the full flow:

```
file path → hash → extract → chunk → embed → store (both SQLite and Qdrant)
```

Each step can fail, and the pipeline handles failures gracefully:
- If no extractor exists for the file type, mark as failed
- If the extractor throws, mark as failed
- If embedding fails, mark as failed
- **Never let one file's failure stop the pipeline.** Process the next file.

`[XP principle]` The pipeline is designed around **fake replaceability** — the
`embedding_generator` parameter accepts any object with `embed()` and `embed_batch()`
methods. Tests use a `FakeEmbeddingGenerator` that produces deterministic vectors
from MD5 hashes, making them fast and predictable without needing ollama running.
This is the same principle behind dependency injection: program to interfaces, not
implementations.

## The Watcher: Detecting Changes

The `FileWatcher` has two modes:

1. **Batch scan:** Walk the entire directory tree, process any file that's new or
   changed. This is for initial indexing and nightly catch-up.
2. **Live watch:** Use the `watchdog` library to monitor for filesystem events
   (create, modify, delete) and process them in real-time.

`[convention]` The `watchdog` library uses Python's `Observer` pattern: you register
an event handler, start the observer, and it calls your handler from a background
thread when files change. On Linux, this uses `inotify` under the hood — kernel-level
filesystem event notification, which is efficient even for large directory trees.

The threading interaction created an interesting bug: SQLite's default is to enforce
that connections are only used from the creating thread. The watchdog observer thread
tried to write to the database and got `ProgrammingError: SQLite objects created in
a thread can only be used in that same thread`. The fix is
`check_same_thread=False` plus WAL journal mode, which together provide safe
concurrent access for our use case (one writer at a time, serialized by event delivery).

## The Query Engine: Asking Questions

The query interface has two levels:

**`SearchOnlyEngine`** — pure semantic search. Embeds the query, searches the vector
store, returns ranked results with scores. No LLM needed.

**`QueryEngine`** — RAG (Retrieval-Augmented Generation). Retrieves the top relevant
chunks, formats them as "file excerpts" with their source paths, and sends them to
`qwen2.5:7b` with a carefully structured system prompt:

```
You are a file search assistant. Answer based ONLY on the provided
file excerpts. For every claim, cite the source file path in [brackets].
If the excerpts don't contain enough information, say so.
Never invent file paths.
```

`[pattern: RAG]` The term "RAG" (Retrieval-Augmented Generation) describes this
pattern: instead of asking the LLM to recall facts from its training data, you
*retrieve* relevant documents from your own data and provide them as context. The
model generates answers grounded in your actual files. The key advantage is
**verifiable answers** — every claim cites a file path you can check.

## Where This Fits

After two sessions, filebrain has a complete data pipeline:

```
Files on disk
    → ExtractorRegistry routes to the right extractor
    → Extractor pulls text from .txt/.md/.py/.pdf/etc.
    → TextChunker splits into overlapping passages
    → EmbeddingGenerator converts to 768-dim vectors via ollama
    → VectorStore (Qdrant) indexes for similarity search
    → MetadataStore (SQLite) tracks status and extracted text
    → FileWatcher detects changes (batch scan or live inotify)
    → QueryEngine retrieves context and asks qwen2.5:7b
    → CLI provides scan/watch/query/status commands
```

130 tests verify every component. The only remaining Mikado tree node is the
audio/video transcription stretch goal (faster-whisper integration).

The system is ready for real-world testing on Raymond's actual files.
