# Filebrain Overview

Filebrain is a local-first system that indexes your filesystem, generates semantic
embeddings, and lets you ask questions about your files using a local LLM. Nothing
leaves your machine — all models run locally via ollama.

## How It Works

```
Your files → Extract text → Split into chunks → Generate embeddings → Store in vector DB
                                                                           ↓
                  Your question → Embed question → Search similar chunks → LLM answers with citations
```

## Core Components

| Component | What it does | Where |
|-----------|-------------|-------|
| **Extractors** | Pull text from files (.txt, .md, .py, .pdf, 40+ code types) | `src/filebrain/extractors/` |
| **MetadataStore** | SQLite database tracking file state and processing status | `src/filebrain/store/metadata.py` |
| **VectorStore** | Qdrant database storing embeddings for similarity search | `src/filebrain/store/vector.py` |
| **TextChunker** | Splits text into overlapping, sentence-aware chunks | `src/filebrain/embeddings/chunker.py` |
| **EmbeddingGenerator** | Calls ollama to convert text to 768-dim vectors | `src/filebrain/embeddings/generator.py` |
| **ProcessingPipeline** | Wires extraction → chunking → embedding → storage | `src/filebrain/pipeline.py` |
| **FileWatcher** | Detects filesystem changes (batch scan + live inotify) | `src/filebrain/watcher/watcher.py` |
| **QueryEngine** | Semantic search + RAG-powered Q&A with citations | `src/filebrain/query/engine.py` |
| **CLI** | Command-line interface: scan, watch, query, status | `src/filebrain/cli/app.py` |

## Quick Start

```bash
# Scan a directory
filebrain scan ~/Documents

# Watch for changes (includes initial scan)
filebrain watch ~/Documents

# Ask a question
filebrain query "What PDFs do I have about machine learning?"

# Search without LLM
filebrain query --search-only "python tutorial"

# Check index status
filebrain status
```

## Tech Stack

- **Python 3.14** with type hints
- **ollama** for local LLM inference (nomic-embed-text + qwen2.5:7b)
- **Qdrant** (local embedded mode) for vector storage
- **SQLite** (with WAL) for metadata
- **watchdog** for filesystem monitoring
- **pymupdf** for PDF extraction
- **pytest** with 130 tests
