[← Previous: Architecture](architecture.md) | [Table of Contents](README.md) | [Next: The Storage Layer →](storage.md)

---

# Chapter 3: The Extraction Layer

> How Filebrain pulls text out of files. The Extractor interface, the registry that routes files to the right extractor, the available extractors, and how to add new ones. A study in the Strategy pattern.

---

## The Problem

Filebrain needs to turn files into text. A `.txt` file is already text — just read it. A `.pdf` is a binary format that encodes text alongside layout information, fonts, and images — you need a library to pull the text out. A `.py` file is text, but you might want to detect the programming language and count lines. A `.docx` is a ZIP archive containing XML.

Every file type has a different extraction strategy, but the rest of the pipeline doesn't care about those differences. It just wants text and some metadata. This is the classic setup for the **Strategy pattern**: define a common interface, implement it differently for each variant, and let the caller pick the right implementation at runtime.

## The Interface

```python
class Extractor(ABC):
    supported_extensions: set[str]   # e.g. {'.txt', '.md'}
    supported_mime_types: set[str]   # e.g. {'text/plain'}

    def extract(path: Path) -> ExtractionResult
```

`ExtractionResult` is a simple data class with two fields:

- `text` — the extracted content as a string
- `metadata` — a dict with type-specific info (line count, page count, detected language, etc.)

The `supported_extensions` and `supported_mime_types` class attributes serve double duty: they're how the registry knows which extractor handles which files, and they're documentation. Glance at any extractor class and you immediately see what it supports.

You've seen this before if you've worked with serializer classes, codec registries, or plugin systems. The ABC (Abstract Base Class) here is Python's way of defining an interface — it's similar to Java's `interface` keyword or Go's implicit interfaces, except Python's version uses metaclass machinery under the hood. `ABC` is from the `abc` module in the standard library, and decorating methods with `@abstractmethod` forces subclasses to implement them or they can't be instantiated.

If you're used to duck typing and wondering why bother with the ABC: it catches missing method implementations at instantiation time rather than at call time. Without the ABC, you'd only discover that your extractor forgot to implement `extract()` when the pipeline tries to call it. With the ABC, you get a `TypeError` the moment you try to create an instance of the incomplete class. It's a compile-time-like check in a runtime language.

## The Registry

```python
registry = ExtractorRegistry()
extractor = registry.get_extractor(Path("file.py"))  # → CodeExtractor
```

The `ExtractorRegistry` maps file extensions to extractor instances. On construction, it auto-registers all built-in extractors by iterating over their `supported_extensions` and building an internal `dict[str, Extractor]` mapping. When the pipeline needs to process a file, it asks the registry: "what extractor handles `.pdf`?" and gets back the PdfExtractor instance.

This is the **Registry pattern** — a centralized lookup table that decouples the caller (the pipeline) from the implementations (individual extractors). The pipeline never imports `PdfExtractor` directly. It imports `ExtractorRegistry` and asks for what it needs. If you add a new extractor, the pipeline doesn't change.

Custom extractors can be registered at runtime:

```python
registry.register(MyCustomExtractor())
```

This calls the same internal logic: iterate over the new extractor's `supported_extensions`, add each mapping to the internal dict. If an extension is already registered, the new extractor replaces the old one — last-write-wins.

## Available Extractors

### PlainTextExtractor

**Extensions:** `.txt`, `.md`, `.log`, `.csv`, `.json`, `.xml`, `.yaml`, `.toml`, `.ini`, `.cfg`, `.conf`

**What it does:** Reads the file as text. Sounds trivial, but there are two things that make it non-trivial:

**Encoding detection.** Files aren't always UTF-8. The PlainTextExtractor tries UTF-8 first (the most common encoding), then falls back to Latin-1 (ISO 8859-1). Latin-1 is the fallback because it can decode any byte sequence without errors — every byte maps to a valid character. This isn't always *correct* (a Shift-JIS file will produce garbage), but it's a pragmatic choice that prevents the extractor from ever crashing on encoding issues. You've likely seen this pattern in web scrapers and log parsers where "best effort" decoding beats "crash on bad input."

**Binary file rejection.** Before attempting to decode, the extractor checks for null bytes (`\x00`) in the raw content. Null bytes almost never appear in legitimate text files but are common in binary formats (executables, images, compressed archives). This is the same heuristic that `file(1)` and Git use to distinguish text from binary. If null bytes are found, the extractor raises an `ExtractionError` rather than producing garbage text.

**Metadata returned:** `line_count`.

### PdfExtractor

**Extensions:** `.pdf`

**What it does:** Uses `pymupdf` (the Python binding for MuPDF) to open the PDF and extract text from every page, concatenated with newlines between pages. MuPDF is a C library that understands the PDF specification — text extraction, font handling, page layout — and pymupdf exposes it to Python.

Why pymupdf over alternatives like `pdfplumber`, `PyPDF2`, or `pdfminer`? Speed and reliability. pymupdf is significantly faster than pure-Python PDF libraries because the heavy lifting happens in C. It handles the widest range of PDF variants, including scanned PDFs with embedded text layers. For PDFs that are purely scanned images (no text layer), extraction will return empty or near-empty text — OCR support would be a Layer 2 enhancement.

**Metadata returned:** `page_count`.

### CodeExtractor

**Extensions:** `.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, `.c`, `.cpp`, `.h`, `.hpp`, `.cs`, `.rb`, `.php`, `.sh`, `.bash`, `.zsh`, `.fish`, `.ps1`, `.r`, `.jl`, `.m`, `.swift`, `.kt`, `.scala`, `.clj`, `.ex`, `.erl`, `.hs`, `.ml`, `.lisp`, `.scm`, `.rkt`, `.lua`, `.pl`, `.pm`, `.tcl`, `.vim`, `.el` — and more (40+ in total).

**What it does:** Reads the file as text (same as PlainTextExtractor — source code is just text) but adds language-specific metadata. The language is detected from the file extension via an internal mapping, not from content analysis. This is pragmatic — extension-based detection is fast and almost always correct for source code, unlike the more complex heuristics that tools like GitHub's Linguist use.

You might wonder why a separate extractor exists for code when PlainTextExtractor could handle it. The answer is metadata. When you query "show me my Python files," the language metadata lets Filebrain filter by `language: python` without relying on file path patterns. As the system matures, the CodeExtractor could also be enhanced to extract function/class names, docstrings, or dependency information — all of which would be valuable for semantic search.

**Metadata returned:** `language`, `line_count`.

## Adding a New Extractor

Say you want to add DOCX support. Here's the process:

1. **Write the test first.** Create `tests/test_extractors/test_docx.py` with a test fixture (a small `.docx` file) and tests that verify extraction produces the expected text and metadata. This is TDD — the test defines the contract before the implementation exists.

2. **Create the extractor class.** In `src/filebrain/extractors/docx.py`:

```python
from pathlib import Path
from filebrain.extractors.base import Extractor, ExtractionResult

class DocxExtractor(Extractor):
    supported_extensions = {'.docx'}
    supported_mime_types = {'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}

    def extract(self, path: Path) -> ExtractionResult:
        # Use python-docx to extract text from paragraphs
        import docx
        doc = docx.Document(str(path))
        text = '\n'.join(para.text for para in doc.paragraphs)
        return ExtractionResult(
            text=text,
            metadata={'paragraph_count': len(doc.paragraphs)}
        )
```

3. **Register it.** The `ExtractorRegistry` auto-registers built-in extractors in its `__init__`. For a new built-in extractor, you'd add an import and instantiation there. For a custom/plugin extractor, call `registry.register(DocxExtractor())` at runtime.

4. **Run the tests.** `pytest tests/test_extractors/test_docx.py` — make sure they pass.

That's it. The pipeline, the stores, the chunker, the embedder — nothing else changes. The new extractor slots into the system because it implements the same interface. This is what the Strategy pattern buys you: a clean extension point.

## Error Handling

Extractors raise `ExtractionError` (a custom exception from `base.py`) when extraction fails — corrupt files, unsupported encoding, empty content, etc. The `ProcessingPipeline` catches `ExtractionError` per-file, marks the file as `failed` in the MetadataStore with the error message, and moves on to the next file.

This means a single bad file never stops a scan. If you scan 10,000 files and one PDF is corrupt, you get 9,999 processed files and one failure recorded with a diagnostic message. You've seen this pattern in batch job frameworks (Spring Batch, Apache Spark) — it's the **Bulkhead pattern** applied at the file level.

## File Locations

**Source code:** `src/filebrain/extractors/`
- `base.py` — `Extractor` ABC, `ExtractionResult`, `ExtractionError`
- `plain_text.py` — `PlainTextExtractor`
- `pdf.py` — `PdfExtractor`
- `code.py` — `CodeExtractor`
- `registry.py` — `ExtractorRegistry`

**Tests:** `tests/test_extractors/` — 48 tests

---

[← Previous: Architecture](architecture.md) | [Table of Contents](README.md) | [Next: The Storage Layer →](storage.md)
