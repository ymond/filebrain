# ADR-002: Vector Database Selection
**Date:** 2026-02-22
**Status:** Accepted

## Context
Filebrain needs a vector database to store embeddings generated from extracted file
content, and to perform semantic similarity search for the query interface. The
database must run locally (no cloud APIs) and integrate smoothly with Python.

The project uses Python 3.14, which is a hard constraint on library compatibility.

## Options Considered

### Option A: ChromaDB (embedded mode)
- Pros: Pure Python, embedded (no separate server process), simple API, built-in
  support for metadata filtering, good for prototyping and moderate scale, persistent
  storage to disk, well-documented
- Cons: **Incompatible with Python 3.14** — ChromaDB 1.5.1 (latest as of 2026-02-22)
  depends on pydantic v1 which crashes on Python 3.14. This is a hard blocker.

### Option B: Qdrant (local embedded mode)
- Pros: High performance, rich filtering, HNSW indexing, works with Python 3.14
  via qdrant-client, has a local embedded mode (path= parameter — no server needed),
  persistent storage to disk, clean Python API, production-grade quality
- Cons: Slightly heavier dependency than ChromaDB, Rust binary bundled in wheel

### Option C: FAISS (via faiss-cpu or faiss-gpu)
- Pros: Very fast, GPU-accelerated option, battle-tested by Meta
- Cons: No built-in persistence (need to manage save/load), no metadata filtering
  (need to pair with SQLite), lower-level API, more code to write for basic operations

## Decision
**Qdrant in local embedded mode** (`qdrant-client>=1.12,<2`). ChromaDB was the original
plan but is blocked by Python 3.14 incompatibility. Qdrant's local embedded mode
provides the same key benefits — no server process, persistent storage to a directory
on disk — with better performance characteristics and full Python 3.14 support.

Tested and verified: qdrant-client 1.17.0 works with Python 3.14, supports
`QdrantClient(path="./data")` for persistent local storage, and
`QdrantClient(":memory:")` for testing.

## Consequences
- qdrant-client added as a dependency (`qdrant-client>=1.12,<2`)
- Embeddings stored in a Qdrant collection on local disk (no server process)
- VectorStore class abstracts Qdrant details — rest of the pipeline doesn't import
  qdrant_client directly
- Payload filtering can be used for metadata-aware queries
- HNSW indexing provides fast approximate nearest neighbor search out of the box
- If we later need GPU-accelerated search, FAISS is the migration path
- **Reversibility:** Medium — the VectorStore abstraction makes swapping possible,
  but migrating existing embeddings would require re-embedding all files
