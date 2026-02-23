[← Previous: Python Project Anatomy](project-anatomy.md) | [Table of Contents](README.md)

---

# Chapter 6: Vision & Roadmap

> The four-layer architecture, from file indexing to physical-world awareness. What's built, what's planned, and the design philosophy that connects it all.

---

## The Core Insight

You have files, knowledge, and resources scattered across machines and formats. You want to organize your digital life but can never get around to it — there's always something more immediate. Filebrain solves this by letting AI do the tedious work: watching directories, extracting content, generating embeddings, and making everything semantically searchable.

The key realization: instead of organizing files into a perfect folder hierarchy, you ask questions and get answers with citations back to source files. The organization *is* the index. The structure *is* the embedding space. You don't need to decide where a file should live — you need to be able to find it when you need it.

## The Four Layers

Filebrain is designed as a layered system where each layer is independently useful but feeds the next. You don't need Layer 2 to get value from Layer 1. But when you build Layer 2, it plugs into the same pipeline that Layer 1 already established.

### Layer 1 — File Brain (current focus)

This is what exists today and what this entire guidebook has documented:

- File watcher daemon that detects new and changed files
- Extractors for text, PDF, and 40+ programming languages
- Sentence-aware text chunking with configurable overlap
- Embedding generation via ollama (nomic-embed-text, 768 dimensions)
- Dual storage: SQLite for metadata, Qdrant for vectors
- Semantic search via cosine similarity on HNSW-indexed vectors
- RAG-powered Q&A with source citations via local LLM (qwen2.5:7b)
- CLI interface: `scan`, `watch`, `query`, `status`

**Current status:**

- [x] Project scaffolding, ollama setup
- [x] Extractor interface + PlainText, PDF, Code extractors
- [x] SQLite metadata store
- [x] Qdrant vector store
- [x] Text chunking + embedding pipeline
- [x] File watcher daemon
- [x] Query interface (semantic search + RAG with citations)
- [x] CLI (`filebrain scan`, `watch`, `query`, `status`)
- [ ] Audio/video transcription extractor (stretch goal)

The audio/video transcription stretch goal is about adding a `WhisperExtractor` that uses a local Whisper model to transcribe `.mp3`, `.wav`, `.m4a`, `.mp4`, etc. The extracted text feeds into the same chunking → embedding → storage pipeline as every other extractor. This is why the Strategy pattern matters — the pipeline doesn't care where the text came from.

### Layer 2 — Life Logger

Layer 2 expands what gets indexed beyond files on disk. The vision:

- **Terminal session capture.** Record and index terminal sessions — commands run, output produced. This creates a searchable history of everything you've done in the terminal, far richer than `~/.bash_history`.
- **Browser extension.** Capture browsing history, bookmarks, and optionally page content. Index it into the same embedding pipeline.
- **Screen recording + storage.** Periodic screenshots or continuous recording with OCR to extract visible text.
- **Audio capture.** Continuous or on-demand audio recording with local transcription (contributing to [Owl](https://github.com/OwlAIProject/Owl) rather than building a proprietary replacement for Limitless). This is a core motivation — the frustration that sparked this entire project was Limitless being acquired and gutted by Meta.

The architectural insight: all Layer 2 inputs feed into the same extraction → embedding pipeline from Layer 1. A browser bookmark becomes extracted text + embedding + metadata in the same stores. A terminal session becomes chunks in the same Qdrant collection. The pipeline is the unifying abstraction. You write new *extractors* (or adapters that produce text for existing extractors), not new pipelines.

### Layer 3 — Active Assistant

Layer 3 transforms Filebrain from a search tool into a proactive assistant:

- **Chime-in capability.** Voice responses to overheard requests — Filebrain listens (via Layer 2's audio capture) and speaks when relevant. Think of it as a conversational interface layered on top of the search and RAG capabilities from Layers 1 and 2.
- **Calendar integration.** Awareness of upcoming events, travel, deadlines. Combined with the file and conversation context from earlier layers, this enables reminders like "you have a meeting about the Q3 report in 30 minutes — here are the relevant files."
- **Grocery list / task management from voice.** "Add milk to the grocery list" captured from ambient audio, parsed, and stored.
- **Zigbee smart home control.** Voice and context-driven control of lights, thermostats, switches. The query engine expands from searching files to executing actions.
- **Contextual reminders.** Based on the full life-awareness from Layers 1 and 2 — not just calendar events, but patterns detected from your activity.

The key technical challenge in Layer 3 is the transition from pull (you ask Filebrain) to push (Filebrain tells you). This requires a persistent daemon with event triggers, which is architecturally different from the batch-oriented Layer 1 pipeline.

### Layer 4 — Physical World

Layer 4 extends awareness from the digital world to the physical:

- **Photogrammetry / 3D house model.** Build a 3D model of your living space from photos. Useful for planning, for spatial queries ("where did I put the toolbox?"), and as a foundation for robotics.
- **CCTV integration + object tracking.** Computer vision on camera feeds — person detection, package delivery alerts, pet monitoring. The frames become inputs to the extraction pipeline (via image captioning or OCR).
- **Physics modeling engine.** Simulate physical systems — structural loads, airflow, thermal behavior. Combined with the 3D model for practical applications like "where should I put the space heater?"
- **Garden monitoring.** Cameras, soil sensors, weather data. Recommendations for watering, planting, harvesting. A domain-specific application of the same sensing + indexing + querying pattern.
- **Drone fleet integration.** Aerial photography, property inspection, mapping. Drones as mobile sensors feeding the same pipeline.
- **Robotics attachments.** Physical actuators controlled by the AI — opening doors, moving objects, tending the garden.

Layer 4 is ambitious and long-term. It's documented here not as a promise but as a direction — the architecture of Layers 1-3 is designed so that Layer 4's inputs (camera frames, sensor data, 3D models) can eventually feed into the same pipeline.

## Key Design Philosophy

### RAG Over Fine-Tuning

The original idea was nightly fine-tuning of a local LLM on personal data. The correct approach turned out to be RAG — Retrieval-Augmented Generation.

Here's the distinction: fine-tuning changes *how* a model talks (its style, tone, and associations). RAG changes *what* it knows (the context it draws from when answering). For a personal knowledge system, you want to change what it knows, not how it talks.

RAG has several practical advantages over fine-tuning for this use case. It's *verifiable* — every answer cites its sources, so you can check whether the model is pulling from the right files or hallucinating. It's *incremental* — new files are indexed and immediately searchable without retraining anything. It's *model-agnostic* — when a better LLM comes out, you swap the model and keep your entire embedding index. And it runs comfortably on consumer hardware — embedding generation is fast, and the LLM only needs to do inference (not training), which is dramatically cheaper.

Fine-tuning has its place. If you wanted a model that writes emails in your personal style, or that knows your organizational jargon without needing it in the context window, fine-tuning would be the right tool. But for "what do I know about X?" and "where did I put Y?" — RAG is the answer.

### Local-First, Open-Source

This project was born from a specific frustration: Limitless, a life-logging tool, was acquired and gutted by Meta. A tool you depend on for personal data, controlled by a corporation that doesn't share your interests, is a liability.

Filebrain's response: everything runs on your hardware, all code is open-source, and there are zero dependencies on cloud services, API keys, or corporate goodwill. The models (nomic-embed-text, qwen2.5:7b) are open-weight and run locally via ollama. The databases (SQLite, Qdrant) store data on your disk. Nothing is transmitted anywhere.

This is not an ideology — it's a risk management strategy. When your personal knowledge system contains your entire digital life (Layers 1-2) and eventually your physical environment (Layer 4), the threat model demands local control.

### Nightly Batch Processing

Layer 1 mimics human sleep cycles — new data from the day gets processed overnight, not in real-time. This is a deliberate scoping decision: real-time processing adds complexity (streaming architectures, backpressure, priority queues) that doesn't pay for itself at Layer 1's scale. The FileWatcher does support live inotify events, but the mental model is still "scan → process → search later."

Real-time elements get added in later layers where they're essential (Layer 3's chime-in capability requires low-latency processing of audio input).

## Relationship to CEP

Filebrain is the first project managed by CEP (Context Engineering Package). CEP provides the structural scaffolding that keeps the project on track:

- **CLAUDE.md** — the project context that Claude Code reads on every session
- **Mikado trees** — dependency graphs for feature implementation
- **Session logs** — chronological records of what was done in each coding session
- **ADRs** — Architecture Decision Records for significant technical choices
- **This guidebook** — the reference book you're reading now

CEP's roadmap includes filebrain integration — using filebrain's semantic search to provide project context to the AI agent. The vision: when Claude Code starts a session on a CEP-managed project, it could query filebrain for relevant files, past session logs, and ADRs, rather than relying solely on the static CLAUDE.md.

## Why This Project, Why Now

Filebrain exists at the intersection of two goals: building something immediately useful (organizing a messy digital life) and learning how AI actually works (not just using APIs, but understanding embeddings, vector databases, RAG, extraction pipelines, and the engineering that makes them production-grade).

Every component teaches something: extractors teach the Strategy pattern and ABC mechanics. The MetadataStore teaches SQLite, WAL mode, and the Repository pattern. The VectorStore teaches HNSW, cosine similarity, and high-dimensional search. The chunker teaches NLP tokenization tradeoffs. The RAG pipeline teaches prompt engineering and hallucination mitigation. The CLI teaches entry points and Python packaging.

The four-layer vision provides a roadmap that keeps the project interesting long after Layer 1 is complete, while the layered architecture ensures each layer delivers standalone value. You never need Layer 4 to benefit from Layer 1. But if you get there, the foundation is designed for it.

---

[← Previous: Python Project Anatomy](project-anatomy.md) | [Table of Contents](README.md)
