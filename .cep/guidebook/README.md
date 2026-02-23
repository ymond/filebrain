# The Filebrain Guidebook

> A reference book for understanding how Filebrain works — its architecture, its design decisions, and the engineering principles that hold it together. Written for someone who's seen all of this before but wants the explicit walkthrough.

---

## About This Book

Filebrain is a local-first, privacy-respecting AI system that indexes your filesystem, generates semantic embeddings, and lets you ask questions about your files using a local LLM. Nothing leaves your machine.

This guidebook is not a tutorial. It's a reference — the kind of book you keep open on a second monitor while you're working in the codebase. Every chapter assumes you've encountered these concepts before in your career, but gives you the explicit, concrete reminders you need to work confidently in this specific system. When a design pattern shows up, we name it. When a convention exists, we explain *why* it's there, not just *that* it's there.

The guidebook also covers planned features and the broader vision. Even layers that don't exist yet are documented here conceptually, because understanding where the system is going informs how to build what's in front of you today.

---

## Table of Contents

### Part I — The System

| # | Chapter | What You'll Find |
|---|---------|-----------------|
| 1 | [Overview](overview.md) | What Filebrain is, how it works at a glance, the tech stack, and getting it running. The "I have 5 minutes, orient me" chapter. |
| 2 | [Architecture](architecture.md) | Component diagram, data flow for ingestion and query, key abstractions and the design patterns behind them, threading model, and links to every Architecture Decision Record. |

### Part II — Deep Dives

| # | Chapter | What You'll Find |
|---|---------|-----------------|
| 3 | [The Extraction Layer](extractors.md) | The Extractor interface, how the registry routes files, available extractors, and how to add new ones. A study in the Strategy pattern. |
| 4 | [The Storage Layer](storage.md) | SQLite for metadata, Qdrant for vectors. Schema design, threading considerations, HNSW indexing, and why two databases are better than one. |

### Part III — Working Here

| # | Chapter | What You'll Find |
|---|---------|-----------------|
| 5 | [Python Project Anatomy](project-anatomy.md) | How this Python project is structured and *why* — pyproject.toml, src layout, entry points, virtual environments, testing conventions, and the coding style. The "how do I even start working in this" chapter. |

### Part IV — The Road Ahead

| # | Chapter | What You'll Find |
|---|---------|-----------------|
| 6 | [Vision & Roadmap](vision.md) | The four-layer architecture, from file indexing to physical-world awareness. What's built, what's planned, and the design philosophy that connects it all. |

---

## Architecture Decision Records

Design decisions are recorded in `.cep/decisions/` and referenced throughout the guidebook:

- [ADR-001: Local Chat Model Selection](../decisions/001-chat-model.md) — Why Qwen 2.5 7B
- [ADR-002: Vector Database Selection](../decisions/002-vector-database.md) — Why Qdrant over ChromaDB
- [ADR-003: Text Chunking Strategy](../decisions/003-chunking-strategy.md) — Why sentence-aware chunks at 1000/200
- [ADR-004: RAG Prompt Strategy](../decisions/004-rag-prompt-strategy.md) — Why structured prompts with citation rules

---

## Quick Reference

```bash
# Scan a directory
filebrain scan ~/Documents

# Watch for changes (includes initial scan)
filebrain watch ~/Documents

# Ask a question
filebrain query "What PDFs do I have about machine learning?"

# Search without LLM (embedding similarity only)
filebrain query --search-only "python tutorial"

# Check index status
filebrain status
```

**Tech stack:** Python 3.14 · ollama (nomic-embed-text + qwen2.5:7b) · Qdrant (local embedded) · SQLite (WAL mode) · watchdog · pymupdf · 130 tests

**Hardware target:** NVIDIA RTX 5070 Laptop GPU (8GB VRAM) · Ryzen AI 9 HX 370 · Arch Linux
