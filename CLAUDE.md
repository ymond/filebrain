# CLAUDE.md
# CEP v0.1.0 | Project: filebrain
# Last upgraded: 2026-02-21

## Who I Am

I'm Raymond. I work a full-time day job and build projects in the evenings and weekends.
I'm an ambitious learner who wants deep understanding of everything being built — not
just working code, but *why* it works, what alternatives existed, and what tradeoffs
were made. I have strong starting energy and need systems that deliver visible progress
in short sessions. I run Arch Linux on a Framework 16 laptop with an NVIDIA RTX 5070
and Ryzen AI 9 HX 370.

## How I Work With You

I review your work in the evenings. You may run for extended periods without my input.
This means:

1. **Never make irreversible decisions silently.** If you're choosing between
   architectures, databases, protocols, or anything that would be painful to undo —
   stop and document the decision in the session log with your recommendation, then
   proceed with your best judgment. I'll review it.

2. **Prefer small, working increments over large incomplete features.** Every commit
   should leave the project in a runnable state. I'd rather see three small things
   that work than one big thing that's half done.

3. **When you're blocked, say so and move to something else.** Don't spin on a
   problem. Log it clearly in the session log with what you tried, then pick up
   a different task from the Mikado tree.

## Startup — Every Time You Begin

When I say "Read CLAUDE.md and follow instructions" or anything similar, this is
your full startup procedure:

1. **Read this entire CLAUDE.md.** You are doing this now.
2. **Read `.cep/mikado.yaml`.** Find the `active_path` and locate the current
   active node (the deepest node with `status: active`).
3. **Read the most recent session log in `.cep/logs/`.** Check for open questions,
   blocked tasks, and any notes from the previous session or from me.
4. **Read any ADRs in `.cep/decisions/`** that are relevant to your current work.
5. **State what you're about to work on** — the active node, its MHC level, and
   your plan for this session. Then begin.

If the Mikado tree is fully complete, say so and ask me what's next.
If there are open questions from a previous session that block progress, state them
and work on a non-blocked node instead.

## Shutdown — When You've Done All You Can

When you have completed all reachable nodes in the Mikado tree, or you are blocked
on all remaining nodes and need my input, or you've been working for an extended
period and have reached a natural stopping point:

1. **Write the session log** to `.cep/logs/YYYY-MM-DD.md` following the format below.
2. **Update `.cep/mikado.yaml`** — mark completed nodes as `done` with today's date,
   update `active_path` to the next logical starting point, add any new nodes
   discovered during this session.
3. **Commit all work** with appropriate atomic commits.
4. **Hibernate the machine** by running: `systemctl hibernate`
   If hibernate is not available, run: `systemctl suspend`
   This saves energy while I'm away. I'll wake the machine when I'm ready to review.

## Documentation Requirements

### Session Logs

After every work session, create or append to `.cep/logs/YYYY-MM-DD.md` with this
structure:

```markdown
## Session: HH:MM - HH:MM

### Summary
One paragraph of what was accomplished in plain language.

### Decisions Made
- **Decision:** [What was decided]
  - **Alternatives considered:** [What else could have been done]
  - **Why this choice:** [Reasoning]
  - **Reversibility:** [Easy / Medium / Hard to change later]

### Mikado Tree Progress
- Active path: [breadcrumb from mikado.yaml active_path]
- Active node MHC level: [N] — [what kind of thinking this required]
- [x] Completed node (MHC N) — link to commit if applicable
- [~] Partially completed node (MHC N) — what remains
- [ ] Blocked node (MHC N) — why and what was tried
- New nodes discovered and added: [list any new children added during this session]

### What I Learned (for Raymond)
Things that are interesting, educational, or that Raymond would want to
understand about what happened. Explain concepts and patterns as if
teaching someone who is skilled but encountering this specific thing
for the first time.

### Open Questions
Things I want Raymond's input on when he reviews this log.
```

### Mikado Tree

Maintain a file at `.cep/mikado.yaml` that represents the current goal decomposition.
The tree uses YAML for arbitrary nesting depth, machine parseability, and future
tooling (a collapsible tree browser, like DOM inspection in browser dev tools).

Format:

```yaml
project: "filebrain"
updated: "YYYY-MM-DD"
active_path: "goal > component > subtask > step"  # breadcrumb to current focus

goal:
  title: "Top-level objective"
  status: pending  # pending | active | done | blocked
  mhc: 12          # Model of Hierarchical Complexity level
  children:
    - title: "Major component or milestone"
      status: active
      mhc: 11
      children:
        - title: "Subtask"
          status: done
          mhc: 9
          completed: "YYYY-MM-DD"
          children:
            - title: "Atomic step"
              status: done
              mhc: 9
              completed: "YYYY-MM-DD"
            - title: "Another atomic step"
              status: done
              mhc: 10
              completed: "YYYY-MM-DD"
        - title: "Another subtask"
          status: active
          mhc: 10
          children:
            - title: "Current step"
              status: active  # <-- ACTIVE
              mhc: 9
            - title: "Next step"
              status: pending
              mhc: 8
    - title: "Blocked component"
      status: blocked
      mhc: 11
      blocked_reason: "Waiting on upstream API docs"
```

#### Model of Hierarchical Complexity (MHC) Levels

Every node in the Mikado tree must be annotated with its MHC level. This is not
correlated with tree depth — a deep leaf node may require higher-order thinking
than its parent. The purpose is to make visible *what kind of thinking* each task
demands, so that when working on a node, you bring the right cognitive frame rather
than over-simplifying a complex decision or over-complicating a concrete one.

Reference levels most relevant to software work:

- **8  — Concrete operational:** Direct, tangible actions with clear outcomes.
  "Run this command." "Rename this variable." "Copy this file."
- **9  — Abstract:** Working with concepts that aren't directly visible.
  "Implement this interface." "Write a function that handles X."
  Single abstractions, one organizing principle at a time.
- **10 — Formal operational:** Reasoning about relationships between abstractions.
  "Design a module where components X and Y interact through Z."
  Requires holding multiple abstractions and their relationships simultaneously.
- **11 — Systematic:** Constructing whole systems from interrelated formal operations.
  "Architect the data pipeline so ingestion, embedding, storage, and query work
  together." Requires understanding how changing one part affects the whole.
- **12 — Metasystematic:** Comparing, evaluating, or integrating entire systems.
  "Choose between a RAG architecture and a fine-tuning approach by evaluating
  their systemic tradeoffs." Requires reasoning *about* systems, not just within them.
- **13 — Paradigmatic:** Creating new frameworks that integrate metasystematic insights.
  Rare in day-to-day work but relevant when inventing novel approaches.

When annotating a node:
- Ask: "What kind of thinking does this task *actually* require to do well?"
- A task that *sounds* simple might be high-MHC if the decision has systemic impact
- A task that *sounds* grand might be low-MHC if the action itself is concrete
- When you find yourself operating at the wrong level (e.g., debating architecture
  when the task is MHC 8), note this in the session log — it's a valuable
  self-awareness signal

Rules for the Mikado tree:
- Always work on the deepest incomplete leaf node
- When a leaf is done, check if its parent is now completable
- When you discover a new dependency, add it as a child before proceeding
- Never delete completed nodes — they're part of the learning record
- Update `active_path` whenever focus changes
- When starting a session, state which node you're working on, its MHC level,
  and what kind of thinking that implies

### Architecture Decision Records

For any significant technical choice, create a file in `.cep/decisions/NNN-title.md`:

```markdown
# ADR-NNN: [Title]
**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX

## Context
What situation or requirement led to this decision?

## Options Considered
### Option A: [Name]
- Pros: ...
- Cons: ...

### Option B: [Name]
- Pros: ...
- Cons: ...

## Decision
What was chosen and why.

## Consequences
What changes as a result. What becomes easier. What becomes harder.
```

## Coding Standards

### General
- Write clear, readable code over clever code
- Every function gets a docstring or comment explaining *why* it exists, not just what it does
- Error handling is not optional — handle errors explicitly, never silently swallow them
- If a file exceeds 200 lines, consider whether it should be split

### Commits
- Each commit should be atomic — one logical change
- Commit messages follow: `type: short description`
  - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
- Never commit broken code to the main branch

### Testing — Strict XP (Kent Beck style, no exceptions)

This project follows Test-Driven Development exactly as described in Kent Beck's
"Test Driven Development: By Example" and "Extreme Programming Explained." This is
non-negotiable. Claude does not skip steps, take shortcuts, or write production code
without a failing test. The cycle is:

1. **Red.** Design the interface first — what does this function/class/module look
   like from the outside? What does calling code expect? Write a test that expresses
   the desired behavior. Run it. Watch it fail. If it passes, your test is wrong or
   the behavior already exists. Do not proceed until you have a clear, failing test.

2. **Green.** Write the *minimum* code to make the test pass. Not elegant code. Not
   complete code. The simplest thing that could possibly work. Run the test. It must
   pass. If it doesn't, fix the code — do not modify the test unless the test itself
   was wrong (and if so, go back to Red).

3. **Refactor.** Now clean up. Remove duplication. Improve naming. Extract functions.
   Run the tests after every change. They must stay green. If a refactor breaks a
   test, undo and try a smaller refactor.

Additional XP testing rules:
- **When fixing a bug:** Write a test that reproduces the bug first. Watch it fail.
  Then fix the bug. Watch the test pass. This is not optional.
- **When adding a feature:** Decompose it into the smallest testable behavior first.
  One test at a time.
- **Tests are runnable with a single command** documented in the README.
- **Tests are fast.** If a test takes more than a second, something is wrong with
  the test or the design.
- **Never comment out or delete a failing test to make the suite pass.**
- **Log the TDD cycle in session logs.** When documenting work, note the sequence:
  what test was written, what it asserted, what minimal code made it pass, and what
  was refactored. This is part of the learning record.

### Dependencies
- Prefer standard library over third-party when the difference is small
- Every dependency must be justified in a comment or ADR
- Pin versions explicitly

## Notifications

Notifications are not yet configured. See CEP docs for Gotify setup.

## Project-Specific Context

<!-- CEP:PROJECT_SPECIFIC_START -->
<!-- Everything below this line is preserved during CEP upgrades -->
<!-- Edit .cep/CLAUDE.local.md or add project context below -->

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

<!-- CEP:PROJECT_SPECIFIC_END -->
