"""Tests for the Extractor interface contract.

These tests define what every extractor must do:
1. Accept a file path, return extracted text and metadata
2. Declare which file extensions and MIME types it handles
3. Raise ExtractionError on unsupported or corrupt files
"""

from pathlib import Path

import pytest


class TestExtractorReturnsTextAndMetadata:
    """An extractor receives a file path and returns extracted text + metadata dict."""

    def test_extract_returns_result_with_text(self, tmp_path: Path):
        """Calling extract() on a valid file returns an ExtractionResult with text."""
        from filebrain.extractors.base import ExtractionResult

        # Create a concrete test extractor (minimal implementation for testing)
        from filebrain.extractors.base import Extractor

        class StubExtractor(Extractor):
            @property
            def supported_extensions(self) -> set[str]:
                return {".txt"}

            @property
            def supported_mime_types(self) -> set[str]:
                return {"text/plain"}

            def extract(self, path: Path) -> ExtractionResult:
                text = path.read_text()
                return ExtractionResult(text=text, metadata={"encoding": "utf-8"})

        extractor = StubExtractor()
        test_file = tmp_path / "hello.txt"
        test_file.write_text("Hello, filebrain!")

        result = extractor.extract(test_file)

        assert isinstance(result, ExtractionResult)
        assert result.text == "Hello, filebrain!"

    def test_extract_result_has_metadata_dict(self, tmp_path: Path):
        """ExtractionResult includes a metadata dictionary."""
        from filebrain.extractors.base import ExtractionResult, Extractor

        class StubExtractor(Extractor):
            @property
            def supported_extensions(self) -> set[str]:
                return {".txt"}

            @property
            def supported_mime_types(self) -> set[str]:
                return {"text/plain"}

            def extract(self, path: Path) -> ExtractionResult:
                return ExtractionResult(
                    text=path.read_text(),
                    metadata={"encoding": "utf-8", "size_bytes": path.stat().st_size},
                )

        extractor = StubExtractor()
        test_file = tmp_path / "meta.txt"
        test_file.write_text("metadata test")

        result = extractor.extract(test_file)

        assert isinstance(result.metadata, dict)
        assert "encoding" in result.metadata
        assert result.metadata["size_bytes"] == 13

    def test_extraction_result_text_is_string(self):
        """ExtractionResult.text must be a string."""
        from filebrain.extractors.base import ExtractionResult

        result = ExtractionResult(text="some content", metadata={})
        assert isinstance(result.text, str)

    def test_extraction_result_metadata_defaults_to_empty_dict(self):
        """ExtractionResult.metadata defaults to an empty dict if not provided."""
        from filebrain.extractors.base import ExtractionResult

        result = ExtractionResult(text="content")
        assert result.metadata == {}


class TestExtractorDeclaresFileTypes:
    """An extractor declares which file extensions and MIME types it handles."""

    def test_supported_extensions_returns_set_of_strings(self):
        """supported_extensions returns a set of dotted extension strings."""
        from filebrain.extractors.base import Extractor

        class StubExtractor(Extractor):
            @property
            def supported_extensions(self) -> set[str]:
                return {".txt", ".md", ".log"}

            @property
            def supported_mime_types(self) -> set[str]:
                return {"text/plain"}

            def extract(self, path: Path) -> "ExtractionResult":
                raise NotImplementedError

        extractor = StubExtractor()
        extensions = extractor.supported_extensions

        assert isinstance(extensions, set)
        assert all(ext.startswith(".") for ext in extensions)
        assert ".txt" in extensions

    def test_supported_mime_types_returns_set_of_strings(self):
        """supported_mime_types returns a set of MIME type strings."""
        from filebrain.extractors.base import Extractor

        class StubExtractor(Extractor):
            @property
            def supported_extensions(self) -> set[str]:
                return {".txt"}

            @property
            def supported_mime_types(self) -> set[str]:
                return {"text/plain", "text/markdown"}

            def extract(self, path: Path) -> "ExtractionResult":
                raise NotImplementedError

        extractor = StubExtractor()
        mime_types = extractor.supported_mime_types

        assert isinstance(mime_types, set)
        assert "text/plain" in mime_types


class TestExtractorErrorHandling:
    """An extractor raises a clear error on unsupported or corrupt files."""

    def test_raises_extraction_error_on_missing_file(self, tmp_path: Path):
        """Extracting a nonexistent file raises ExtractionError."""
        from filebrain.extractors.base import ExtractionError, Extractor, ExtractionResult

        class StubExtractor(Extractor):
            @property
            def supported_extensions(self) -> set[str]:
                return {".txt"}

            @property
            def supported_mime_types(self) -> set[str]:
                return {"text/plain"}

            def extract(self, path: Path) -> ExtractionResult:
                if not path.exists():
                    raise ExtractionError(f"File not found: {path}")
                return ExtractionResult(text=path.read_text())

        extractor = StubExtractor()
        missing = tmp_path / "nonexistent.txt"

        with pytest.raises(ExtractionError, match="File not found"):
            extractor.extract(missing)

    def test_extraction_error_is_an_exception(self):
        """ExtractionError is a proper Exception subclass."""
        from filebrain.extractors.base import ExtractionError

        assert issubclass(ExtractionError, Exception)

    def test_extraction_error_stores_message(self):
        """ExtractionError stores the error message."""
        from filebrain.extractors.base import ExtractionError

        error = ExtractionError("corrupt file")
        assert str(error) == "corrupt file"
