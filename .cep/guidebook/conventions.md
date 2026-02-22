# Conventions

## Running the Project

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest

# Run the CLI
filebrain --help
filebrain scan ~/Documents
filebrain query "what files do I have about Python?"
filebrain status
```

## Prerequisites

- **Python 3.14+** (uses modern type hints like `X | None`)
- **ollama** running locally with:
  - `nomic-embed-text` — embedding model (768 dimensions)
  - `qwen2.5:7b` — chat model for RAG queries

## Project Structure

```
filebrain/
├── pyproject.toml              # Package config, dependencies, entry points
├── src/filebrain/
│   ├── __init__.py
│   ├── pipeline.py             # ProcessingPipeline (orchestrator)
│   ├── extractors/
│   │   ├── base.py             # Extractor ABC, ExtractionResult, ExtractionError
│   │   ├── plain_text.py       # PlainTextExtractor
│   │   ├── pdf.py              # PdfExtractor (pymupdf)
│   │   ├── code.py             # CodeExtractor (40+ languages)
│   │   └── registry.py         # ExtractorRegistry
│   ├── embeddings/
│   │   ├── chunker.py          # TextChunker (sentence-aware)
│   │   └── generator.py        # EmbeddingGenerator (ollama API)
│   ├── store/
│   │   ├── metadata.py         # MetadataStore (SQLite)
│   │   └── vector.py           # VectorStore (Qdrant)
│   ├── watcher/
│   │   └── watcher.py          # FileWatcher (watchdog)
│   ├── query/
│   │   └── engine.py           # SearchOnlyEngine, QueryEngine
│   └── cli/
│       ├── app.py              # CLI commands and main()
│       └── __main__.py         # python -m filebrain.cli entry
└── tests/
    ├── test_smoke.py
    ├── test_pipeline.py
    ├── test_watcher.py
    ├── test_cli.py
    ├── test_extractors/        # 48 tests
    ├── test_store/             # 35 tests
    ├── test_embeddings/        # 20 tests
    └── test_query/             # 6 tests
```

## Testing

- **130 tests** covering all components
- Tests requiring ollama are skipped if ollama is not running
- `FakeEmbeddingGenerator` provides deterministic vectors for unit tests
- Pipeline tests use separate directories for DB and scan target
- Run with `pytest` or `python -m pytest`
- All tests should complete in under 15 seconds

## Coding Style

- Type hints on all function signatures
- Docstrings explaining *why*, not just *what*
- Each module under 200 lines
- Strict TDD: test first, implement, refactor
- Atomic commits: `type: description`

## Dependencies

| Package | Purpose | ADR |
|---------|---------|-----|
| pymupdf | PDF text extraction | — |
| qdrant-client | Vector database (local embedded) | ADR-002 |
| watchdog | Filesystem event monitoring | — |

Dev dependencies: pytest

## Data Storage

Default location: `~/.filebrain/`
- `metadata.db` — SQLite database
- `vectors/` — Qdrant persistent storage

Override with: `filebrain --db-dir /path/to/custom scan ~/Documents`
