[← Table of Contents](README.md) | [Next: Architecture →](architecture.md)

---

# Chapter 1: Overview

> The "I have 5 minutes, orient me" chapter. What Filebrain is, how it works at a high level, and how to get it running.

---

## What Filebrain Is

Filebrain is a local-first system that indexes your filesystem, generates semantic embeddings, and lets you ask questions about your files using a local LLM. Nothing leaves your machine — all models run locally via ollama.

If you've worked with Elasticsearch or Solr, you already know the concept: ingest documents, index them, search them. Filebrain does the same thing, but instead of keyword-based indexing, it uses *semantic embeddings* — vector representations of meaning. This means you can search by *concept*, not just by word. "What do I have about machine learning?" will find your PDFs about neural networks even if they never use the phrase "machine learning."

The other key difference from traditional search: Filebrain doesn't just return documents. It uses RAG (Retrieval-Augmented Generation) to *answer your question* in natural language, citing the source files it drew from. You'll see this called the "query path" throughout the guidebook — it's the pipeline from your question through embedding, similarity search, context assembly, LLM generation, and citation formatting.

## How It Works

```
Your files → Extract text → Split into chunks → Generate embeddings → Store in vector DB
                                                                           ↓
  Your question → Embed question → Search similar chunks → LLM answers with citations
```

This diagram is the entire system in two lines. The top line is the **ingestion path** — it runs when you scan or watch a directory. The bottom line is the **query path** — it runs when you ask a question. Both paths share the embedding step (same model, same vector space), which is what makes the similarity search work. If the question and a chunk are semantically similar, their vectors will be close together in 768-dimensional space.

You'll hear "768-dimensional" a lot. That's the output size of `nomic-embed-text`, the embedding model. Every piece of text — whether a file chunk or a query — gets converted to a vector of 768 floating-point numbers. Cosine similarity between these vectors is how Filebrain decides which chunks are relevant to your question.

## Core Components

These are the building blocks. Each one has a dedicated section later in the guidebook, but here's the map so you know what you're looking at:

| Component | What It Does | Where in the Codebase |
|-----------|-------------|----------------------|
| **Extractors** | Pull raw text from files (.txt, .md, .py, .pdf, 40+ code types) | `src/filebrain/extractors/` |
| **MetadataStore** | SQLite database tracking every file's state and processing status | `src/filebrain/store/metadata.py` |
| **VectorStore** | Qdrant database storing embeddings for similarity search | `src/filebrain/store/vector.py` |
| **TextChunker** | Splits extracted text into overlapping, sentence-aware chunks | `src/filebrain/embeddings/chunker.py` |
| **EmbeddingGenerator** | Calls ollama to convert text chunks into 768-dim vectors | `src/filebrain/embeddings/generator.py` |
| **ProcessingPipeline** | Orchestrator: wires extraction → chunking → embedding → storage | `src/filebrain/pipeline.py` |
| **FileWatcher** | Detects filesystem changes via batch scan + live inotify events | `src/filebrain/watcher/watcher.py` |
| **QueryEngine** | Semantic search + RAG-powered Q&A with source citations | `src/filebrain/query/engine.py` |
| **CLI** | The command-line interface: `scan`, `watch`, `query`, `status` | `src/filebrain/cli/app.py` |

If you're coming from an MVC or layered-architecture background, you can think of it roughly as: Extractors and FileWatcher are the input layer, MetadataStore and VectorStore are the persistence layer, ProcessingPipeline is the service/orchestration layer, QueryEngine is the domain logic for retrieval, and CLI is the presentation layer.

## Quick Start

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in dev mode (editable install — changes to src/ are reflected immediately)
pip install -e ".[dev]"

# Make sure ollama is running with both models pulled
ollama pull nomic-embed-text
ollama pull qwen2.5:7b

# Scan a directory
filebrain scan ~/Documents

# Watch for changes (includes initial scan, then monitors via inotify)
filebrain watch ~/Documents

# Ask a question (uses RAG: embed → search → LLM → cited answer)
filebrain query "What PDFs do I have about machine learning?"

# Search without the LLM step (embedding similarity only, faster)
filebrain query --search-only "python tutorial"

# Check how many files are indexed and their statuses
filebrain status
```

If you're wondering what `pip install -e ".[dev]"` does — that's an *editable install* with the `dev` extras group. The `-e` flag means Python creates a link to your source directory rather than copying files into `site-packages`. When you edit code in `src/`, the changes are live immediately without reinstalling. The `[dev]` part pulls in development dependencies like pytest. See [Chapter 5: Python Project Anatomy](project-anatomy.md) for the full explanation.

## Tech Stack

| Technology | Role | Why This One |
|-----------|------|-------------|
| **Python 3.14** | Language | Type hints, pattern matching, modern stdlib. Filebrain uses `X \| None` union syntax throughout. |
| **ollama** | Local LLM runtime | Runs both models locally. No API keys, no cloud, no data leaving the machine. |
| **nomic-embed-text** | Embedding model | 768-dim vectors, 8192 token context window. Open-source, good quality for its size (~274MB). |
| **qwen2.5:7b** | Chat model (RAG) | Best instruction-following at 7B scale. Fits in 8GB VRAM alongside the embedding model. See [ADR-001](../decisions/001-chat-model.md). |
| **Qdrant** | Vector database | Local embedded mode (no server process). HNSW indexing for fast similarity search. See [ADR-002](../decisions/002-vector-database.md). |
| **SQLite** | Metadata database | WAL mode for concurrent access. Tracks file state, hashes, extracted text. |
| **watchdog** | Filesystem monitoring | Cross-platform inotify wrapper. Detects create, modify, delete events. |
| **pymupdf** | PDF extraction | Fast, reliable text extraction from PDF pages. Pure Python with C bindings. |
| **pytest** | Testing | 130 tests covering all components. Tests run in under 15 seconds. |

## Hardware Target

Filebrain is built for the Framework 16 laptop: NVIDIA RTX 5070 Laptop GPU with 8GB VRAM, Ryzen AI 9 HX 370, running Arch Linux. Both models (embedding + chat) fit in VRAM simultaneously (~274MB + ~4.7GB = ~5GB of 8GB). The remaining headroom matters — it means you can have the system running while doing other GPU work.

---

[← Table of Contents](README.md) | [Next: Architecture →](architecture.md)
