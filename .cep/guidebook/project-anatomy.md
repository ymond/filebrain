[← Previous: The Storage Layer](storage.md) | [Table of Contents](README.md) | [Next: Vision & Roadmap →](vision.md)

---

# Chapter 5: Python Project Anatomy

> How this Python project is structured and *why*. pyproject.toml, src layout, entry points, virtual environments, testing conventions, and the coding style. The "how do I even start working in this codebase" chapter.

---

## Starting a Python Project

Every time you start a new Python project, there's that moment: "How do I structure this again?" You've done it before, but the conventions have shifted — `setup.py` gave way to `setup.cfg`, which gave way to `pyproject.toml`. The `src/` layout is now recommended over the flat layout. Build backends multiplied (setuptools, flit, hatch, poetry). It's a lot to keep straight.

Here's how Filebrain is set up, and more importantly, *why each piece is there*.

## pyproject.toml: The Single Source of Truth

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "filebrain"
version = "0.1.0"
description = "Local-first file indexing and semantic search powered by local LLMs"
requires-python = ">=3.12"
license = "MIT"
dependencies = [
    "pymupdf>=1.27,<2",
    "qdrant-client>=1.12,<2",
    "watchdog>=6.0,<7",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9",
]

[project.scripts]
filebrain = "filebrain.cli.app:main"

[tool.hatch.build.targets.wheel]
packages = ["src/filebrain"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Let's walk through each section:

**`[build-system]`** — This tells `pip` (and any PEP 517 compliant installer) which build backend to use. The build backend is the tool that takes your source code and produces an installable package (a `.whl` file). Filebrain uses `hatchling` — it's fast, minimal, and understands the `src/` layout out of the box. Alternatives include `setuptools` (the legacy default, more verbose), `flit` (simple but less flexible), and `poetry-core` (if you're using Poetry). The key insight: `pyproject.toml` is the *metadata standard* (PEP 621), but the *build backend* that reads it is pluggable.

**`[project]`** — The PEP 621 project metadata. Name, version, description, Python version constraint, license, and dependencies. This is what was in `setup.py` or `setup.cfg` in older projects. The `requires-python = ">=3.12"` constraint means pip will refuse to install Filebrain on Python 3.11 or earlier. The dependency specs use version ranges (`>=1.27,<2`) — this means "at least 1.27 but less than 2.0," following semantic versioning conventions where a major version bump signals breaking changes.

**`[project.optional-dependencies]`** — Extras groups. `dev` contains pytest and any other development-only dependencies. You install them with `pip install -e ".[dev]"`. The brackets contain the extras group name. In production or CI, you'd install without them: `pip install .`. This keeps the production dependency tree lean. You could have multiple groups — `docs`, `lint`, `gpu` — each installable independently.

**`[project.scripts]`** — This is what creates the `filebrain` command. When you `pip install` the package, pip creates a small executable script (in `.venv/bin/filebrain` for a virtual environment, or `/usr/local/bin/filebrain` for a system install) that imports `filebrain.cli.app` and calls the `main()` function. The format is `command-name = "module.path:function"`. This is how every CLI tool distributed as a Python package works — pip, pytest, black, ruff, they all use this mechanism.

**`[tool.hatch.build.targets.wheel]`** — Tells hatchling that the package code lives in `src/filebrain`. Without this, hatchling would look for a top-level `filebrain/` directory. This is the `src/` layout configuration.

**`[tool.pytest.ini_options]`** — Pytest configuration. `testpaths = ["tests"]` tells pytest where to find tests so you can just run `pytest` without arguments from the project root.

## The src/ Layout

```
filebrain/
├── pyproject.toml
├── src/
│   └── filebrain/
│       ├── __init__.py
│       ├── pipeline.py
│       ├── extractors/
│       ├── embeddings/
│       ├── store/
│       ├── watcher/
│       ├── query/
│       └── cli/
└── tests/
```

The `src/` layout puts your package inside a `src/` directory rather than at the project root. The practical benefit: it prevents accidental imports of your local source code.

Here's the problem with a flat layout (where `filebrain/` is at the project root): if you run `pytest` from the project root, Python adds the current directory to `sys.path`. This means `import filebrain` finds your local source code *even if you haven't installed the package*. This can mask packaging bugs — your code works in development but fails when installed because you forgot to declare a dependency or include a file in the package.

With the `src/` layout, `import filebrain` only works if the package is actually installed (either normally or in editable mode with `pip install -e .`). This forces you to keep your packaging configuration correct. It's a small inconvenience (`pip install -e .` is one extra command) that prevents a class of bugs that are hard to diagnose.

The `__init__.py` file in each directory marks it as a Python package. Even if the file is empty, it must exist for Python's import system to recognize the directory as a package. Python 3.3+ supports "namespace packages" without `__init__.py`, but explicit `__init__.py` files are still the convention for application code — they're clearer and more compatible with tools.

## Entry Points: How `filebrain` Becomes a Command

When you type `filebrain scan ~/Documents` in your terminal, here's what happens:

1. The shell finds `.venv/bin/filebrain` (an executable script created by pip during installation).

2. That script is a thin wrapper that does roughly:
   ```python
   from filebrain.cli.app import main
   main()
   ```

3. Python's import system resolves `filebrain.cli.app` by looking for the `filebrain` package in `sys.path` (which includes the virtual environment's `site-packages`).

4. The `main()` function in `cli/app.py` parses command-line arguments and dispatches to the appropriate command handler.

There's also `src/filebrain/cli/__main__.py`, which enables `python -m filebrain.cli` as an alternative to the `filebrain` command. The `__main__.py` file is a Python convention: when you run `python -m some.package`, Python looks for `some/package/__main__.py` and executes it. This is the same mechanism that makes `python -m pytest`, `python -m http.server`, and `python -m venv` work.

## Virtual Environments

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Virtual environments are isolated Python installations. When you create `.venv` and activate it, `pip install` puts packages in `.venv/lib/python3.14/site-packages/` instead of your system Python's `site-packages/`. This prevents dependency conflicts between projects (Project A needs `requests==2.28`, Project B needs `requests==2.31`).

The `source .venv/bin/activate` line modifies your shell's `PATH` so that `python` and `pip` point to the virtual environment's copies. When you're done, `deactivate` restores your original PATH. On fish shell, it's `source .venv/bin/activate.fish`. On Windows, `.venv\Scripts\activate`.

The `.venv` directory is in `.gitignore` — you never commit a virtual environment. It's regenerated from `pyproject.toml` on each machine.

**Editable installs** (`pip install -e .`): Instead of copying your source code into `site-packages`, pip creates a link (a `.pth` file or a direct symlink, depending on the build backend) that points to your `src/` directory. When you edit source code, the changes are immediately visible without reinstalling. This is essential during development — without it, you'd have to run `pip install .` after every code change.

## Project Structure Deep Dive

```
src/filebrain/
├── __init__.py              # Package marker (can export top-level names)
├── pipeline.py              # ProcessingPipeline — the orchestrator
├── extractors/
│   ├── __init__.py
│   ├── base.py              # Extractor ABC, ExtractionResult, ExtractionError
│   ├── plain_text.py        # PlainTextExtractor
│   ├── pdf.py               # PdfExtractor (pymupdf)
│   ├── code.py              # CodeExtractor (40+ languages)
│   └── registry.py          # ExtractorRegistry
├── embeddings/
│   ├── __init__.py
│   ├── chunker.py           # TextChunker (sentence-aware splitting)
│   └── generator.py         # EmbeddingGenerator (ollama API)
├── store/
│   ├── __init__.py
│   ├── metadata.py          # MetadataStore (SQLite)
│   └── vector.py            # VectorStore (Qdrant)
├── watcher/
│   └── watcher.py           # FileWatcher (watchdog integration)
├── query/
│   └── engine.py            # SearchOnlyEngine, QueryEngine
└── cli/
    ├── __init__.py
    ├── app.py               # CLI commands and main()
    └── __main__.py           # python -m filebrain.cli entry
```

The structure groups code by *domain concern*, not by *technical layer*. Everything related to extraction lives in `extractors/`, everything related to storage lives in `store/`, etc. This is sometimes called "package by feature" as opposed to "package by layer" (where you'd have `models/`, `services/`, `controllers/`). The advantage: when you need to understand or modify extraction, everything you need is in one directory.

Each subpackage has a focused responsibility and a small public API. The `extractors/` package exports the `Extractor` ABC, `ExtractionResult`, and `ExtractorRegistry`. Internal implementation details (how PlainTextExtractor detects encoding) stay inside the package.

## Testing

```bash
pytest                          # Run all tests
pytest tests/test_extractors/   # Run one test directory
pytest -k "test_pdf"            # Run tests matching a name pattern
pytest -x                       # Stop on first failure
```

The test structure mirrors the source structure:

```
tests/
├── test_smoke.py           # Basic sanity checks
├── test_pipeline.py        # Integration tests for the pipeline
├── test_watcher.py         # FileWatcher tests
├── test_cli.py             # CLI command tests
├── test_extractors/        # 48 tests
├── test_store/             # 35 tests (23 metadata, 12 vector)
├── test_embeddings/        # 20 tests
└── test_query/             # 6 tests
```

**130 tests total.** They should complete in under 15 seconds. If tests are slow, something is wrong — likely an unintended dependency on ollama or a missing mock.

**Tests requiring ollama are skipped** if ollama is not running. This means you can run the full test suite without a GPU, without ollama installed, without models downloaded. The tests that exercise actual embedding generation or LLM queries are guarded with `pytest.mark.skipif` checks. This is a pragmatic choice — you want the test suite to be fast and runnable in CI, where GPU access may not be available.

**`FakeEmbeddingGenerator`** provides deterministic vectors for unit tests. Instead of calling ollama, it generates consistent vectors from a hash of the input text. This means test assertions on search results are reproducible — the same input always produces the same vector. You've seen this pattern in test doubles: fakes (simplified implementations), mocks (recorded expectations), and stubs (canned responses). The fake here is a full implementation of the embedding interface, just without the neural network.

**Pipeline tests use separate directories** for database files and scan targets. Each test gets its own temporary directory (via `tmp_path` fixture) so tests can't interfere with each other. Isolation is critical — a test that leaves behind a database file could cause the next test to find unexpected data.

## Coding Style

**Type hints on all function signatures.** Filebrain uses Python 3.14's type hint syntax, including `X | None` for optional types (the modern equivalent of `Optional[X]`). Type hints serve as documentation and enable IDE autocompletion and error detection. They don't affect runtime behavior — Python doesn't enforce types unless you use a checker like mypy or pyright.

**Docstrings explaining *why*, not just *what*.** A method named `upsert_file` doesn't need a docstring saying "upserts a file." It benefits from a docstring explaining *why* upsert (not separate insert/update), *when* it resets status to pending, and what happens if the hash matches.

**Each module under 200 lines.** This is a soft guideline that encourages decomposition. When a module grows past 200 lines, it's a signal to look for natural seams where it could be split. It's not a hard rule — a 210-line module is fine if it's cohesive.

**Strict TDD: test first, implement, refactor.** New features start with a failing test. The test defines the contract. Implementation makes it pass. Refactoring cleans up without changing behavior (the test acts as a safety net). This is the Red-Green-Refactor cycle.

**Atomic commits:** `type: description` format. Examples: `feat: add PDF extraction`, `fix: handle empty files in chunker`, `test: add CodeExtractor language detection tests`, `refactor: extract registry from pipeline`. This is Conventional Commits — it makes the git log readable and enables automated changelog generation if needed later.

## Dependencies

| Package | Purpose | Version Constraint | ADR |
|---------|---------|-------------------|-----|
| pymupdf | PDF text extraction | `>=1.27,<2` | — |
| qdrant-client | Vector database (local embedded) | `>=1.12,<2` | [ADR-002](../decisions/002-vector-database.md) |
| watchdog | Filesystem event monitoring | `>=6.0,<7` | — |

Dev dependencies: `pytest>=8.0,<9`

The dependency list is intentionally small. Three runtime dependencies. One dev dependency. This is a conscious choice — fewer dependencies mean fewer things that can break, fewer security vulnerabilities to track, fewer version conflicts to resolve, and faster installation. Every dependency should earn its place.

---

[← Previous: The Storage Layer](storage.md) | [Table of Contents](README.md) | [Next: Vision & Roadmap →](vision.md)
