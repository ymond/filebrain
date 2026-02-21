# Project-Specific Context for filebrain

## What This Project Is

Filebrain is a local-first, privacy-respecting system that watches your filesystem,
extracts content and metadata from every file it finds, generates embeddings, stores
them in a vector database, and lets you query your entire digital life through a
local LLM.

Think of it as giving your computer a memory of everything you have on it. You can
ask questions like "show me all my PDFs about Lisp programming" or "do I have enough
resources to learn Morse Code" or "what videos do I have where we practice passing
hand technique" — and get real answers grounded in actual files on your machine.

This is Layer 1 of a larger personal AI system. Later layers will add audio capture,
screen recording, browser history, terminal logging, and more — all feeding into the
same pipeline. Filebrain's architecture must support new input sources being added
without redesigning the core.

## Design Principles

- **Local only.** Nothing leaves this machine. No cloud APIs, no telemetry, no
  external services. All models run locally via ollama.
- **Incremental.** Process new and changed files. Never require a full re-scan to
  stay current. Nightly batch processing for heavy work (video transcription, large
  PDFs), but lightweight files should be processed promptly.
- **Modular extractors.** Each file type gets its own extractor. Adding support for
  a new file type means writing one new extractor that conforms to the interface.
  The pipeline doesn't care what produced the extracted text.
- **Verifiable answers.** When the LLM answers a question, it must cite which files
  the answer came from. The user can verify. No hallucinated file references.
- **Resumable.** If processing is interrupted (laptop closed, power loss), it picks
  up where it left off. No corrupt state, no lost work.

## Tech Stack

- **Language:** Python 3 (fastest path to working prototype; rewrite candidates later)
- **Local LLM runtime:** ollama
- **Embedding model:** nomic-embed-text (via ollama) — good quality, runs fast locally
- **Chat/query model:** Start with whatever fits well on an RTX 5070 with good
  quality. Suggest in an ADR. Models in the 7B-14B range are likely the sweet spot.
- **Vector database:** ChromaDB (embedded, no server process, Python-native, good
  for prototyping). Document in an ADR if you recommend Qdrant or something else.
- **Audio/video transcription:** whisper.cpp or faster-whisper (GPU accelerated)
- **PDF extraction:** pymupdf (fitz) — fast, handles most PDFs well
- **Filesystem watching:** inotify via watchdog library
- **Metadata storage:** SQLite for file metadata, processing status, and extracted
  text (the vector DB stores embeddings, SQLite stores everything else)
- **CLI interface to start:** A simple CLI for querying. TUI or web UI comes later.

## Hardware

- Framework 16 laptop
- NVIDIA GeForce RTX 5070 Laptop GPU
- AMD Ryzen AI 9 HX 370
- Arch Linux

The RTX 5070 is the primary compute for inference and transcription. Design for
GPU acceleration where available, CPU fallback where necessary.

## What This Project Is NOT (yet)

These are future layers, not part of the current scope:
- Browser history capture
- Terminal session logging
- Screen recording / eye tracking
- Audio capture (Owl/Limitless replacement)
- Calendar / smart home integration
- Photogrammetry / 3D modeling
- Robotics

Do not build toward these yet. Build a solid, tested, working file brain first.
The architecture should not *prevent* these additions, but do not over-engineer
for them either.

## Project-Specific Conventions

- Use `pyproject.toml` for project configuration (not setup.py)
- Use `pytest` for testing
- Use type hints throughout — this codebase will grow and type safety matters early
- Structure the project as a proper Python package from day one:
  ```
  filebrain/
  ├── pyproject.toml
  ├── src/
  │   └── filebrain/
  │       ├── __init__.py
  │       ├── watcher/        # filesystem watching
  │       ├── extractors/     # one module per file type
  │       ├── embeddings/     # embedding generation
  │       ├── store/          # vector DB + SQLite
  │       ├── query/          # query interface + LLM integration
  │       └── cli/            # command-line interface
  └── tests/
      ├── test_extractors/
      ├── test_store/
      └── test_query/
  ```
- Each extractor must implement a common interface (define this interface first via TDD)
- Log verbosely to a file, minimally to stdout
