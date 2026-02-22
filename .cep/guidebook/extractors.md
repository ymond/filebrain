# Extractors

Extractors pull text content from files. Each extractor handles specific file types
and produces an `ExtractionResult` containing the extracted text and metadata.

## Interface

```python
class Extractor(ABC):
    supported_extensions: set[str]   # e.g. {'.txt', '.md'}
    supported_mime_types: set[str]   # e.g. {'text/plain'}
    def extract(path: Path) -> ExtractionResult  # text + metadata dict
```

`ExtractionResult` has two fields: `text` (the extracted content) and `metadata`
(a dict with type-specific info like line count, page count, language).

## Available Extractors

| Extractor | Extensions | Key Features |
|-----------|-----------|-------------|
| **PlainTextExtractor** | .txt, .md, .log, .csv, .json, .xml, .yaml, .toml, .ini, .cfg, .conf | Encoding detection (UTF-8, Latin-1), binary file rejection via null byte check |
| **PdfExtractor** | .pdf | Uses pymupdf, extracts from all pages, reports page count in metadata |
| **CodeExtractor** | .py, .js, .ts, .go, .rs, .java, .c, .cpp, .sh, .rb, .lisp, + 30 more | Language detection from extension, reports language and line count |

## ExtractorRegistry

The registry maps file extensions to extractors. It auto-registers all built-in
extractors on construction. Custom extractors can be added:

```python
registry = ExtractorRegistry()
extractor = registry.get_extractor(Path("file.py"))  # → CodeExtractor
registry.register(MyCustomExtractor())                # add new type
```

## Adding a New Extractor

1. Create a class that inherits from `Extractor`
2. Implement `supported_extensions`, `supported_mime_types`, and `extract()`
3. Register it with `ExtractorRegistry.register()`
4. Write tests first (TDD)

Located in: `src/filebrain/extractors/`
Tests in: `tests/test_extractors/`
