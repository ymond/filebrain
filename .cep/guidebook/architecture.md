[← Previous: Overview](overview.md) | [Table of Contents](README.md) | [Next: The Extraction Layer →](extractors.md)

---

# Chapter 2: Architecture

> How all the pieces connect. Component diagram, data flow for ingestion and query, the key abstractions and the design patterns behind them, threading model, and the decisions that shaped the system.

---

## Component Diagram

```
┌──────────────┐     ┌────────────────┐     ┌─────────────┐
│  FileWatcher │────→│   Processing   │────→│   Stores    │
│  (watchdog)  │     │   Pipeline     │     │             │
└──────────────┘     │                │     │ MetadataStore│
                     │ ┌────────────┐ │     │ (SQLite)    │
   File events ─────→│ │ Extractor  │ │     │             │
   (create/mod/del)  │ │ Registry   │ │     │ VectorStore │
                     │ └────────────┘ │     │ (Qdrant)    │
                     │ ┌────────────┐ │     └──────┬──────┘
                     │ │ TextChunker│ │            │
                     │ └────────────┘ │            ↓
                     │ ┌────────────┐ │     ┌─────────────┐
                     │ │ Embedding  │ │     │ QueryEngine │
                     │ │ Generator  │ │     │ (search +   │
                     │ └────────────┘ │     │  RAG + LLM) │
                     └────────────────┘     └──────┬──────┘
                                                   │
                                                   ↓
                                            ┌─────────────┐
                                            │     CLI     │
                                            └─────────────┘
```

Read this diagram from top-left to bottom-right. The FileWatcher feeds file events into the ProcessingPipeline. The pipeline orchestrates three internal steps (extract → chunk → embed) and writes results to two stores. The QueryEngine reads from those same stores to answer questions. The CLI sits at the bottom as the user-facing interface for both ingestion (`scan`, `watch`) and retrieval (`query`, `status`).

The critical thing to notice: the stores are the meeting point between the two halves of the system. Ingestion writes to them; querying reads from them. They're decoupled — you could index files today and query them next week. The pipeline doesn't know about the QueryEngine, and the QueryEngine doesn't know about the pipeline. They share data through the stores.

## Data Flow

### The Ingestion Path

This is what happens when you run `filebrain scan ~/Documents` or when the watcher detects a file change:

1. **FileWatcher** detects a file (batch directory walk or inotify event). It hands the file path to the pipeline.

2. **ProcessingPipeline** computes a SHA-256 hash of the file contents and asks the MetadataStore: "Have I seen this exact content before?" This is change detection — if the hash matches what's stored, the file hasn't changed and we skip it. This is the same principle behind Git's content-addressable storage, rsync's delta detection, and build tools like Make. Content hashing is more reliable than modification time (mtime) because mtime can change without content changing (e.g., `touch`), and content can change without mtime updating (e.g., restoring from backup).

3. **ExtractorRegistry** looks up the file extension and routes to the appropriate extractor. This is the **Strategy pattern** — the pipeline doesn't know how to extract text from a PDF vs. a Python file; it delegates to the right strategy object. See [Chapter 3: The Extraction Layer](extractors.md) for the deep dive.

4. **The Extractor** (PlainText, PDF, or Code) extracts raw text and metadata (line count, page count, detected language, etc.) and returns an `ExtractionResult`.

5. **TextChunker** splits the extracted text into overlapping chunks of ~1000 characters, breaking at sentence boundaries when possible. The overlap (200 characters) ensures that information near chunk boundaries isn't lost — a concept that appears in the same place in sliding-window algorithms. See [ADR-003](../decisions/003-chunking-strategy.md) for why these specific numbers.

6. **EmbeddingGenerator** sends each chunk to ollama's `nomic-embed-text` model and gets back a 768-dimensional vector. This is the most computationally expensive step — it's a forward pass through a transformer model for each chunk. The RTX 5070 makes this fast, but it's still the bottleneck on large scans.

7. **VectorStore** (Qdrant) stores each embedding alongside its payload: the source file path, chunk index, and chunk text. HNSW indexing (Hierarchical Navigable Small World) builds a graph structure that makes approximate nearest-neighbor search fast — O(log n) instead of O(n).

8. **MetadataStore** (SQLite) updates the file's record to `status: processed` and stores the full extracted text. If any step failed, it records `status: failed` with the error message.

One thing to notice: errors are handled per-file. If a PDF is corrupted and extraction fails, the pipeline marks that one file as failed and moves on. It never lets a single bad file stop an entire batch scan. This is the **Bulkhead pattern** — isolating failures so they don't cascade.

### The Query Path

This is what happens when you run `filebrain query "What files do I have about machine learning?"`:

1. **CLI** receives your question as a string.

2. **EmbeddingGenerator** embeds the question using the same `nomic-embed-text` model. This is crucial — the question vector must live in the same vector space as the chunk vectors for similarity search to work. If you used a different model to embed the query than you used for the chunks, the vectors would be incomparable. Same principle as using the same tokenizer for encoding and decoding.

3. **VectorStore** performs a cosine similarity search: "which stored vectors are closest to this query vector?" It returns the top-k most similar chunks. Cosine similarity measures the angle between vectors — identical meaning gives a cosine of 1.0, orthogonal (unrelated) meaning gives 0.0. The HNSW index makes this fast even with millions of vectors.

4. **QueryEngine** takes those chunks and formats them into a structured prompt. Each chunk is labeled with its source file path so the LLM can cite sources. The prompt explicitly instructs the model: only use the provided excerpts, cite every claim, admit when you don't have enough information. See [ADR-004](../decisions/004-rag-prompt-strategy.md) for the prompt engineering.

5. **The LLM** (qwen2.5:7b via ollama) generates a natural-language answer with inline citations like `[/home/user/Documents/paper.pdf]`.

6. **CLI** displays the answer and lists the source files.

The `--search-only` flag skips steps 4-5 and just returns the raw search results with their similarity scores. This is useful when you want to find files, not have a conversation about them. It's also much faster since it doesn't require an LLM inference pass.

## Key Abstractions

Each major component is wrapped in an abstraction that hides its implementation details from the rest of the system. This is where the design patterns live.

### Extractor (Abstract Base Class) — Strategy Pattern

```python
class Extractor(ABC):
    supported_extensions: set[str]   # e.g. {'.txt', '.md'}
    supported_mime_types: set[str]   # e.g. {'text/plain'}
    def extract(path: Path) -> ExtractionResult  # text + metadata dict
```

All extractors implement the same interface. The ExtractorRegistry maps file extensions to extractor instances, and the pipeline asks the registry: "give me the extractor for `.pdf`." This is the **Strategy pattern** — the algorithm (how to extract text) varies by file type, but the pipeline treats all extractors identically.

Adding a new file type means writing one new class and registering it. The pipeline, the stores, the chunker, the embedder — none of them change. This is the **Open-Closed Principle** in practice: open for extension (new extractors), closed for modification (existing pipeline code).

### MetadataStore — Repository Pattern

The MetadataStore wraps SQLite behind a clean Python API. The rest of the system never writes SQL directly — it calls methods like `upsert_file()`, `mark_processed()`, `get_files_by_status()`. If you've worked with Django's ORM, SQLAlchemy, or any data-access layer, this is the same idea: the **Repository pattern** separates domain logic from persistence details.

The pipeline's resumability depends entirely on the MetadataStore. When you scan a directory, the pipeline checks `has_changed(path, hash)` for each file. Files already processed with the same hash get skipped. Files that are new, changed, or previously failed get (re)processed. This makes batch scanning idempotent — you can run `filebrain scan` ten times and it only does real work when files have actually changed.

### VectorStore — Adapter Pattern

The VectorStore wraps Qdrant behind a simplified interface: `add_embedding()`, `search()`, `delete_by_source_path()`, `count()`. The rest of the system imports `VectorStore`, never `qdrant_client`. This is the **Adapter pattern** — the VectorStore translates between Filebrain's domain language and Qdrant's API.

This was validated when the project had to switch from ChromaDB to Qdrant (see [ADR-002](../decisions/002-vector-database.md)). Because the abstraction existed, the migration was isolated to one file. Nothing else in the system knew or cared that the underlying database changed.

### ProcessingPipeline — Orchestrator/Mediator

The pipeline is the central coordinator. It wires the extractor registry, chunker, embedding generator, metadata store, and vector store together. It doesn't contain business logic itself — it just calls each component in order and handles the error boundaries.

This is sometimes called the **Mediator pattern** — the pipeline is the only component that knows about all the others. The extractor doesn't know about the chunker. The chunker doesn't know about the embedding generator. Each component does one thing, and the pipeline connects them.

## Design Decisions

Every significant technical decision has been captured in an Architecture Decision Record. These are the canonical source of "why was this choice made" and "what alternatives were considered":

| Decision | ADR | Key Rationale |
|----------|-----|--------------|
| Qwen 2.5 7B as the chat model | [ADR-001](../decisions/001-chat-model.md) | Best instruction following at 7B, fits in VRAM alongside the embedding model |
| Qdrant over ChromaDB | [ADR-002](../decisions/002-vector-database.md) | ChromaDB incompatible with Python 3.14; Qdrant has local embedded mode |
| 1000-char chunks, 200-char overlap | [ADR-003](../decisions/003-chunking-strategy.md) | Good semantic coherence for nomic-embed-text's optimal input range |
| Structured RAG prompt with citations | [ADR-004](../decisions/004-rag-prompt-strategy.md) | Reliable source attribution with explicit citation instructions |

If you're wondering "why didn't they use X instead?" — the ADR probably has the answer. Each records the context, the options considered, the decision, and the consequences. The format is borrowed from Michael Nygard's original ADR proposal, which itself drew from the RFC process.

## Threading Model

Filebrain's threading model is minimal by design. There are two threads:

**Main thread** handles CLI commands and batch scanning. When you run `filebrain scan`, the main thread walks the directory, calls `pipeline.process_file()` for each file, and blocks until done. Straightforward, sequential, easy to reason about.

**Watchdog observer thread** is spawned by the `watchdog` library when you run `filebrain watch`. It listens for inotify events from the kernel and calls `pipeline.process_file()` on its own thread. This means the pipeline's dependencies — SQLite and Qdrant — must handle concurrent access.

**SQLite** uses WAL (Write-Ahead Logging) mode and `check_same_thread=False`. WAL mode allows concurrent readers and a single writer without blocking, which is a major improvement over SQLite's default journal mode where readers and writers block each other. `check_same_thread=False` disables Python's sqlite3 module's thread-safety check, which is necessary because the watchdog thread needs to use the same connection. This is safe *because* WAL mode handles the actual concurrency at the database level.

If you've worked with SQLite in web applications (Django, Flask), you've probably hit the "database is locked" error. WAL mode is the standard fix. It writes changes to a separate WAL file instead of modifying the database directly, and readers can continue reading the main database while the writer appends to the WAL file. Checkpointing merges the WAL back periodically.

**Qdrant** is thread-safe by design — it's a Rust engine that handles concurrency internally. No special configuration needed on the Python side.

---

[← Previous: Overview](overview.md) | [Table of Contents](README.md) | [Next: The Extraction Layer →](extractors.md)
