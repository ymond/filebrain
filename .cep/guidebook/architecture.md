# Filebrain Architecture

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

## Data Flow

### Ingestion Path
1. **FileWatcher** detects a file (batch scan or inotify event)
2. **Pipeline** computes SHA-256 hash, checks if file has changed
3. **ExtractorRegistry** routes to the appropriate extractor by extension
4. **Extractor** (PlainText, PDF, or Code) extracts text and metadata
5. **TextChunker** splits into ~1000-char overlapping chunks
6. **EmbeddingGenerator** calls ollama to produce 768-dim vectors per chunk
7. **VectorStore** stores embeddings with source path metadata
8. **MetadataStore** records file status as "processed" with extracted text

### Query Path
1. **CLI** receives question from user
2. **EmbeddingGenerator** embeds the question
3. **VectorStore** returns top-k most similar chunks (cosine similarity)
4. **QueryEngine** formats chunks as context excerpts with file paths
5. **LLM** (qwen2.5:7b via ollama) generates answer citing source files
6. **CLI** displays answer and lists source file paths

## Key Abstractions

### Extractor (ABC)
All extractors implement: `supported_extensions`, `supported_mime_types`, `extract(path) → ExtractionResult`. Adding a new file type means writing one new extractor class. `[pattern: Strategy]`

### MetadataStore
Repository pattern over SQLite. Tracks file identity (path + hash), status (pending/processed/failed), and extracted text. The pipeline's resumability depends on this: pending files get processed, processed files get skipped.

### VectorStore
Adapter over Qdrant. Stores embeddings with payload (source_path, chunk_index, chunk_text). Supports search by cosine similarity and deletion by source path.

### ProcessingPipeline
Orchestrator that connects all components. Handles errors per-file (never lets one failure stop the batch). Uses content hash for change detection.

## Design Decisions

| Decision | ADR | Key Rationale |
|----------|-----|--------------|
| Qwen 2.5 7B chat model | ADR-001 | Best instruction following at 7B, fits in VRAM |
| Qdrant over ChromaDB | ADR-002 | ChromaDB incompatible with Python 3.14 |
| 1000-char chunks, 200-char overlap | ADR-003 | Good semantic coherence for nomic-embed-text |
| Structured RAG prompt with citations | ADR-004 | Reliable source attribution with qwen2.5:7b |

## Threading Model

- **Main thread:** CLI commands, batch scanning
- **Watchdog observer thread:** Receives inotify events, calls pipeline.process_file()
- **SQLite:** WAL mode + `check_same_thread=False` for cross-thread access
- **Qdrant:** Thread-safe by design (Rust engine handles concurrency)
