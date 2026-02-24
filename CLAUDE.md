# CLAUDE.md
# CEP v0.2.2 | Project: filebrain
# Last upgraded: 2026-02-24

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

4. **Keep going until the Mikado tree is done.** Do NOT stop after completing one
   section of the tree to ask if you should continue. If there are pending nodes in
   the Mikado tree that you can work on, work on them. The only reasons to stop are:
   - Every node in the tree is either `done` or `blocked`
   - You've hit a decision that is genuinely hard to reverse and would lead to
     significant wasted work if you guess wrong (not just any ADR — most decisions
     are easily reversible and you should just make them, document them, and keep going)
   - You need information that only Raymond can provide and no other nodes are workable
   Making decisions, writing ADRs, and logging them is part of working — not a reason
   to pause. Document the decision, move on, keep building.

5. **Do not invent features beyond the Mikado tree.** Only build what's specified.
   However, at the end of a session, you may add a "Possibilities" section to the
   session log suggesting features that the completed work opens up. These are
   suggestions for Raymond to review, not tasks to implement.

## Startup — Every Time You Begin

When I say "Read CLAUDE.md and follow instructions" or anything similar, this is
your full startup procedure:

1. **Read this entire CLAUDE.md.** You are doing this now.
2. **Initialize the session.** Generate a session ID by running:
   ```bash
   date +%Y%m%d-%H%M
   ```
   Use this as the session ID (e.g., `20260222-2130`). If Claude Code provides its
   own session UUID (visible in "to resume enter `claude resume <uuid>`"), record
   that too. Create or append to `.cep/sessions.yaml`:
   ```yaml
   - id: "20260222-2130"
     claude_session: "claude-code-uuid-if-available"
     status: active  # active | ended | resurrected
     started: "2026-02-22T21:30:00"
     ended: null
     log: "logs/20260222-2130.md"
     blog: "blog/20260222-2130-short-title.md"
     decisions: []  # list of ADR filenames created this session
     commits: []    # list of commit hashes
   ```
3. **Read `.cep/mikado.yaml`.** Find the `active_path` and locate the current
   active node (the deepest node with `status: active`).
4. **Read the most recent session log in `.cep/logs/`.** Check for open questions,
   blocked tasks, and any notes from the previous session or from me.
5. **Read any ADRs in `.cep/decisions/`** that are relevant to your current work.
6. **State what you're about to work on** — the active node, its MHC level, and
   your plan for this session. Then begin.

If the Mikado tree is fully complete, say so and ask me what's next.
If there are open questions from a previous session that block progress, state them
and work on a non-blocked node instead.
If the most recent session in `sessions.yaml` has `status: resurrected`, read that
session's log carefully — Raymond is asking you to continue or fix something from
that session.

## Shutdown — When You've Done All You Can

When you have completed all reachable nodes in the Mikado tree, or you are blocked
on all remaining nodes and need my input, or you've been working for an extended
period and have reached a natural stopping point:

1. **Write the session log** to `.cep/logs/YYYYMMDD-HHMM.md` (using the session ID
   from startup) following the format below.
2. **Write the blog post** to `.cep/blog/YYYYMMDD-HHMM-short-title.md`.
3. **Update the guidebook** — revise any pages in `.cep/guidebook/` affected by
   this session's work. Create new component pages if new components were built.
   Follow the Guidebook Voice and Structure rules below exactly.
   Also check if the project's **README.md** needs updating (see README guidelines
   below) — new CLI commands, changed install steps, or new major features should
   be reflected there.
4. **Update `.cep/mikado.yaml`** — mark completed nodes as `done` with today's date,
   update `active_path` to the next logical starting point, add any new nodes
   discovered during this session.
5. **Update `.cep/sessions.yaml`** — set the current session's status to `ended`,
   fill in `ended` timestamp, populate `decisions` with any ADR filenames created,
   and populate `commits` with commit hashes from this session.
6. **MANDATORY: Verify all session artifacts exist before committing.** Run through
   this checklist and confirm every item. If any artifact is missing, create it now.
   Do NOT proceed to committing until every item passes.
   ```
   [ ] .cep/logs/YYYYMMDD-HHMM.md exists and has all sections
       (Summary, Decisions Made, Mikado Tree Progress, What I Learned, Open Questions, Possibilities)
   [ ] .cep/blog/YYYYMMDD-HHMM-short-title.md exists and is a narrative teaching
       document (not a reformatted log — if it reads like the log, rewrite it)
   [ ] .cep/guidebook/ has been reviewed — any pages affected by this session's work
       are updated, new component pages created if new components were built
   [ ] .cep/guidebook/README.md table of contents is current (all chapters listed)
   [ ] .cep/mikado.yaml is updated — completed nodes marked done with dates,
       active_path points to next logical starting point
   [ ] .cep/sessions.yaml is updated — status set to ended, ended timestamp filled,
       decisions and commits lists populated
   [ ] README.md reviewed — updated if new commands, features, or setup steps were added
   [ ] Any significant technical decisions have ADRs in .cep/decisions/
   ```
   **This checklist is not optional. Raymond relies on these artifacts for learning
   and project continuity. A session without a blog post or with a stale guidebook
   is an incomplete session, even if all the code works.**

7. **Commit all work** with appropriate atomic commits.
8. **Announce completion audibly.** Play a sound so Raymond knows if he's nearby:
```bash
   espeak "Claude has finished working. The computer will sleep in 3 minutes. To cancel, run: kill all sleep." 2>/dev/null \
     || printf '\a'
```
9. **Put the computer to sleep.** Raymond is likely asleep or away. Do NOT prompt.
   Wait 3 minutes (so Raymond can cancel if nearby), then sleep:
```bash
   sleep 180 && systemctl suspend &
   echo "CEP: Computer will sleep in 3 minutes. To cancel: kill %1"
```

**CRITICAL: Do not ask "should I sleep the computer?" or "would you like to continue?" —
Raymond is not there. Steps 1-9 are all autonomous. No prompting. No waiting.**

## Documentation Requirements

### Session Logs

After every work session, create `.cep/logs/YYYYMMDD-HHMM.md` (matching the session
ID) with this structure:

```markdown
## Session: YYYY-MM-DD HH:MM - HH:MM

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

### Possibilities
Features or improvements that the completed work makes possible or easier.
These are suggestions for Raymond to consider, not tasks to implement.
```

### Blog Posts

After every work session, create `.cep/blog/YYYYMMDD-HHMM-short-title.md` — a narrative,
educational account of the session written for a **generalist programmer** who has
encountered most languages, patterns, and conventions before but may not remember
the specifics of any particular one.

The blog is NOT a reformatted log. It's a teaching document. Write it as if explaining
the session's work to a skilled but busy engineer over coffee. Key requirements:

- **Explain the "why" behind architecture choices** in plain language. Don't just say
  "we used the Strategy pattern" — explain what problem it solves, why it fits here,
  and what the alternative would have looked like.
- **Annotate conventions, idioms, and patterns** inline using labels:
  - `[convention]` — language or ecosystem standard (e.g., `if __name__ == "__main__"`)
  - `[idiom]` — common way of doing things in this language (e.g., list comprehensions)
  - `[pattern: Strategy]` — GoF or well-known design pattern
  - `[pattern: Repository]` — architectural pattern
  - `[XP principle]` — Extreme Programming practice being applied
  - `[best practice]` — widely accepted engineering practice
  - `[DDIA concept]` — concept from Designing Data-Intensive Applications
- **Assume the reader might not remember** how Python packages work, what `__init__.py`
  does, why `src/` layout exists, how pytest discovers tests, etc. Briefly explain
  these when they come up — one or two sentences is enough, just enough to jog memory.
- **Show how this session's work fits into the larger system** being built. Where does
  this piece connect? What depends on it? What does it enable next?
- **Include small code snippets** when they illustrate a point, but the blog is about
  understanding, not about reproducing the source code.

The blog serves as a study resource. Over weeks of reading these, Raymond should
naturally absorb how to architect software, recognize patterns, and think in terms
of system design.

### System Guidebook

Maintain and update `.cep/guidebook/` — a **reference book** that describes how the
system works **right now**. Unlike the blog (which is linear and append-only), the
guidebook is **cumulative and revised** every session. It reads like a book, not like
documentation. It's the kind of thing you keep open on a second monitor while working
in the codebase.

#### Book Structure

The guidebook follows a GitBook-style structure with `README.md` as the entrypoint:

```
.cep/guidebook/
├── README.md              # Table of Contents — the entrypoint. Links to every chapter.
├── overview.md            # Ch 1: What this system is, quick start, tech stack
├── architecture.md        # Ch 2: Component diagram, data flow, abstractions, patterns
├── [component].md         # Ch 3+: Deep dives — one per major subsystem
├── project-anatomy.md     # How the project is structured and WHY (language-specific)
└── vision.md              # The road ahead — what's planned and the design philosophy
```

**README.md** is the table of contents. It has a brief "About This Book" intro, then
a table linking to every chapter with a one-line description of what the reader will
find there. Group chapters into logical parts ("The System," "Deep Dives," "Working
Here," "The Road Ahead"). Include a quick-reference section at the bottom with the
most common commands and the tech stack summary. Also include a section listing all
ADRs with links.

**Navigation links** appear at the top and bottom of every chapter page:
```markdown
[← Previous: Chapter Name](previous.md) | [Table of Contents](README.md) | [Next: Chapter Name →](next.md)
```
The first chapter omits the "Previous" link (starts with `[← Table of Contents]`).
The last chapter omits the "Next" link. This creates a linear reading path through
the book while allowing random access via the README.

**Chapter ordering** should flow naturally: start with orientation (overview), then
architecture, then deep dives into individual components, then practical working
conventions, then vision/roadmap. Each chapter should be self-contained enough to
read alone, but they should build on each other when read in order.

#### The Voice

The guidebook is written for **a generalist engineer who has seen everything before
but needs explicit reminders.** This is the core voice principle. The reader:

- Has probably initialized a project in this language before, but doesn't remember
  the exact conventions for how the main function is defined, detected, and executed
- Has encountered the Strategy pattern in their career, but needs a reminder of what
  it is and why it fits *here specifically*
- Knows what a database is, but needs the explicit walkthrough of why *this* schema
  was designed this way and what the tradeoffs are
- Has worked with threads before, but needs the concrete explanation of which threads
  exist in *this* system and why the concurrency model is safe

The voice is warm, confident, and peer-to-peer. Not condescending ("as you probably
know..."), not academic ("one might consider..."), not terse (raw API docs). Write
like you're explaining the system to a skilled colleague who just joined the project.

Specific voice requirements:

1. **Explain the "why" before the "what."** Don't just show the schema — explain why
   these columns exist, why this one is the primary key, why that one is nullable.
   The reader can see the code; the guidebook tells them what the code can't.

2. **Name design patterns when they appear.** When the code uses the Strategy pattern,
   say so: "This is the **Strategy pattern** — the algorithm varies by file type, but
   the pipeline treats all extractors identically." Don't just label it — explain what
   problem it solves here and what the alternative would look like.

3. **Connect to the reader's experience.** Reference analogous systems: "If you've
   worked with Django's ORM, this is the same idea: the Repository pattern separating
   domain logic from persistence." "This is the same principle behind Git's
   content-addressable storage." These anchors help the reader map new concepts onto
   existing knowledge.

4. **Write in prose, not lists.** The guidebook reads like a book, not a README.
   Use paragraphs to explain concepts. Tables are fine for structured reference data
   (schemas, component maps, dependency lists), but the explanations around them
   should be flowing prose. Avoid bullet-point-driven documentation.

5. **Each chapter opens with a blockquote summary.** One or two sentences that tell
   the reader what they'll find and why they'd read this chapter:
   ```markdown
   > How Filebrain pulls text out of files. The Extractor interface, the registry
   > that routes files, and how to add new ones. A study in the Strategy pattern.
   ```

6. **Include the "you've probably seen this" bridge.** When explaining a concept,
   briefly acknowledge that the reader has encountered it before, then give the
   concrete, specific version for this project:
   - "If you've worked with Elasticsearch, you already know the concept: ingest
     documents, index them, search them. This system does the same thing, but instead
     of keyword-based indexing, it uses semantic embeddings."
   - "You've seen this before if you've worked with serializer classes, codec
     registries, or plugin systems."

7. **Don't shy away from depth.** If understanding HNSW indexing matters for working
   in this codebase, explain HNSW. If WAL mode is critical to the threading model,
   explain WAL mode. The guidebook is a reference book — depth is the point. But
   keep the depth *relevant* to this system, not a general CS textbook.

8. **Cross-reference ADRs inline.** When a design decision is mentioned, link to
   the ADR: "See [ADR-002](../decisions/002-title.md) for the full rationale."
   The guidebook summarizes the decision in context; the ADR has the full
   options-considered analysis.

9. **Trace execution paths step by step.** When explaining a data flow or a command,
   walk through each step with numbered paragraphs. At each step, explain what
   happens AND why. For example, when explaining what happens when a user runs a
   CLI command, trace from the shell finding the entry point script, through the
   import system, to the main function, through each component that gets called.
   This "follow the thread" approach teaches the reader to reason about systems.

10. **Ground abstract concepts in this codebase.** When explaining a pattern or
    principle, immediately show how it manifests in the actual code. Don't say "the
    system uses dependency injection" — say "the ProcessingPipeline takes its stores,
    chunker, and embedding generator as constructor arguments rather than creating
    them internally. This means tests can pass in fakes, and the pipeline doesn't
    know or care whether it's writing to Qdrant or an in-memory stub."

#### Chapter Guidelines

- **`overview.md`** is the "I have 5 minutes, orient me" chapter. What the system
  is, how it works at a high level (a two-line diagram showing the main data flow if
  applicable), core components as a reference table with what each does and where it
  lives in the codebase, quick start commands, and the tech stack with brief rationale
  for each choice. Update every session.

- **`architecture.md`** is the system design chapter. Component diagram (ASCII art),
  data flow for each major path (ingestion, query, etc.) explained step by step with
  the "why" at each stage, key abstractions with the design patterns they embody
  (name the pattern, explain why it fits, describe what the alternative would look
  like), threading/concurrency model with practical implications, and a table of ADRs.
  This is the chapter a new contributor reads after the overview to understand *how
  the system thinks*.

- **Component deep-dive pages** (e.g., `extractors.md`, `storage.md`) go deep on
  one subsystem. Start with the problem it solves ("why does this component exist?"),
  then the interface/abstraction, then each concrete implementation with what makes
  it interesting, then how to extend it (with a concrete example — write a new
  extractor, add a new storage backend), then error handling, then file locations.
  Each component page should feel like a self-contained mini-chapter that teaches
  the reader about this domain *through the lens of this specific codebase.*

- **`project-anatomy.md`** explains the project structure for someone who might not
  remember language-specific conventions. Walk through the build configuration file
  field by field — explain what each section does, why it's there, and what
  alternatives exist. Explain the directory layout and why it's organized this way
  (e.g., why `src/` layout over flat layout in Python). Trace the entry point from
  the command line through the runtime to the main function. Cover virtual
  environments / dependency management, editable installs, testing setup (how tests
  are discovered, how fakes work, why isolation matters), and coding style with
  rationale. This is the "how do I even start working here" chapter. When a concept
  is language-specific (e.g., `__init__.py` in Python, `Cargo.toml` in Rust), give
  the one-sentence explanation of what it is and why it exists.

- **`vision.md`** is the forward-looking chapter. What's built, what's planned,
  what's the design philosophy, and how the current architecture supports the future
  roadmap. This chapter helps the reader understand *why* certain abstractions exist
  that might seem over-engineered for the current scope — they're designed for where
  the system is going. Include the key technical decisions (e.g., RAG over fine-tuning)
  with explanations that teach the reader about the tradeoffs in general, not just
  for this project.

#### Maintenance Rules

- **Every session, review and update** any guidebook pages affected by the work done.
  If a new component was built, create its chapter page and add it to the README.md
  table of contents with navigation links. If an existing component changed, update
  its page. If the architecture shifted, update `architecture.md`.
- **The guidebook must always reflect the current state of the system.** It is the
  canonical reference for "how does this work right now." Stale guidebook pages are
  worse than no guidebook — they teach the wrong things.
- **When adding a new chapter,** insert it into the reading order, update the
  README.md table of contents, and fix the prev/next navigation links on the
  adjacent chapters.
- **ADRs are referenced, not duplicated.** The guidebook summarizes decisions in
  context ("we chose Qdrant because..."); the ADR has the full options-considered
  analysis. Link to the ADR; don't copy its contents into the guidebook.
- **Maintain the voice consistently.** Every page should read like it was written by
  the same author — the warm, peer-to-peer, "you've seen this before" voice. If a
  page reads like a raw API doc or a bullet-point checklist, rewrite it in prose.

### README.md

The project's `README.md` is the front door. It serves three audiences in order:

1. **What is this?** A brief introduction — what the project does, what problem it
   solves, who it's for. Someone landing on the repo should understand the project
   in 30 seconds.

2. **How do I use it?** Install instructions (or the equivalent for non-CLI projects),
   a few usage examples that show the most common workflows, and a pointer to
   `--help` or other self-service documentation. Keep this practical — the reader
   wants to get running, not read a manual. For projects that aren't installable CLIs
   (libraries, APIs, services), this section covers: how to add it as a dependency,
   basic API usage examples, and a link to full API/usage documentation if it exists.

3. **How do I contribute?** How to set up a development environment, and a link to
   the `.cep/guidebook/` for understanding the system internals. Keep this section
   short — the guidebook is the deep reference, not the README.

The README should be updated whenever:
- A new user-facing command, API endpoint, or feature is added
- Install or setup steps change
- The project's scope or purpose evolves
- A section references something that no longer exists

The README is NOT the place for detailed architecture, internal design decisions, or
contributor conventions — those belong in the guidebook. The README points people
*toward* the guidebook; it doesn't duplicate it.

### Mikado Tree

Maintain a file at `.cep/mikado.yaml` that represents the current goal decomposition.
The tree uses YAML for arbitrary nesting depth, machine parseability, and future
tooling (a collapsible tree browser, like DOM inspection in browser dev tools).

Format:

```yaml
project: "filebrain"
updated: "YYYY-MM-DD"
active_path: "goal > v0.2 > First task > Current step"  # breadcrumb to current focus

goal:
  title: "Top-level objective"
  status: active
  mhc: 12          # Model of Hierarchical Complexity level
  children:
    - title: "v0.1 — First milestone"
      status: done
      mhc: 11
      completed: "YYYY-MM-DD"
      children:
        - title: "Completed subtask"
          status: done
          mhc: 9
          completed: "YYYY-MM-DD"
    - title: "v0.2 — Current milestone"
      status: active
      mhc: 11
      children:
        - title: "First task (do this before second task)"
          status: active
          mhc: 10
          children:
            - title: "Atomic step"
              status: done
              mhc: 9
              completed: "YYYY-MM-DD"
            - title: "Current step"
              status: active  # <-- deepest pending/active leaf = work here
              mhc: 9
            - title: "Next step"
              status: pending
              mhc: 8
        - title: "Second task (depends on first being done)"
          status: pending
          mhc: 9
        - title: "Blocked task"
          status: blocked
          mhc: 10
          reason: "Waiting on upstream API docs"
        - title: "Deferred task"
          status: deferred
          mhc: 10
          reason: "Deferring past v0.2 — want feedback from playtesting first"
```

#### Node Status Values

- **`done`** — Completed. Include `completed: "YYYY-MM-DD"` date.
- **`active`** — Currently being worked on. Only one leaf node should be active at a time.
- **`pending`** — Ready to work on, not yet started.
- **`blocked`** — Attempted but cannot proceed. Include `reason:` explaining why.
- **`deferred`** — Deliberately postponed. Include `reason:` explaining why.

`blocked` means "I *can't* do this without external input." `deferred` means
"we *chose* not to do this yet." Both require a `reason` field. The distinction
helps Raymond prioritize: blocked items may need his input, deferred items are
parked by design.

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

#### Traversal Algorithm

This is how you decide what to work on. Follow this algorithm exactly.

**Children within any node are ordered top-to-bottom by intended execution order.**
Position encodes priority and implicit dependencies. The first child should be done
before the second. If you reorder children, you are changing the execution plan.

1. **Scan** the top-level children of `goal` from top to bottom.
2. **Find** the first child whose status is `active` or `pending`. Skip `done`,
   `blocked`, and `deferred` nodes.
3. **Descend** into that child. At each level, pick the first child whose status
   is `active` or `pending` (depth-first, always picking the first eligible child).
4. **Work** when you reach the deepest `active` or `pending` leaf — that is your
   current task. If it needs further decomposition, add children, then recurse.
5. **After completing a leaf** (mark it `done`), check if its parent is now
   completable (all children `done`). If so, mark the parent `done` too. Then
   return to step 3 within the same branch to find the next eligible leaf.
6. **If blocked**, mark the node `blocked` with a `reason`, then return to step 3
   to find the next eligible leaf in the same branch. If the entire branch is
   blocked or done, return to step 2 to try the next top-level branch.
7. **Stop** when every reachable node is `done`, `blocked`, or `deferred`.

`active_path` is a convenience bookmark — update it whenever focus changes so that
resume is fast. But the algorithm above is the source of truth, not `active_path`.

#### Additional Rules

- When you discover a new dependency, add it as a child before proceeding
- Never delete completed nodes — they are part of the learning record
- When starting a session, state which node you're working on, its MHC level,
  and what kind of thinking that implies
- If a `blocked` or `deferred` node is a dependency of a later node (the later
  node cannot proceed without it), mark the later node `blocked` as well with a
  `reason` referencing the dependency

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
