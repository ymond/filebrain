"""Tests for the PlainTextExtractor.

Covers: .txt, .md, .log, .csv files, encoding detection, and error cases.
"""

from pathlib import Path

import pytest

from filebrain.extractors.base import ExtractionError, ExtractionResult


class TestPlainTextExtraction:
    """PlainTextExtractor reads text files and returns their content."""

    def test_extracts_txt_file(self, tmp_path: Path):
        f = tmp_path / "readme.txt"
        f.write_text("Hello world")

        from filebrain.extractors.plain_text import PlainTextExtractor

        result = PlainTextExtractor().extract(f)

        assert isinstance(result, ExtractionResult)
        assert result.text == "Hello world"

    def test_extracts_markdown_file(self, tmp_path: Path):
        f = tmp_path / "notes.md"
        f.write_text("# Title\n\nSome content")

        from filebrain.extractors.plain_text import PlainTextExtractor

        result = PlainTextExtractor().extract(f)
        assert result.text == "# Title\n\nSome content"

    def test_extracts_log_file(self, tmp_path: Path):
        f = tmp_path / "app.log"
        f.write_text("2026-01-01 INFO started")

        from filebrain.extractors.plain_text import PlainTextExtractor

        result = PlainTextExtractor().extract(f)
        assert result.text == "2026-01-01 INFO started"

    def test_extracts_csv_file(self, tmp_path: Path):
        f = tmp_path / "data.csv"
        f.write_text("name,age\nAlice,30")

        from filebrain.extractors.plain_text import PlainTextExtractor

        result = PlainTextExtractor().extract(f)
        assert result.text == "name,age\nAlice,30"

    def test_metadata_includes_size_bytes(self, tmp_path: Path):
        f = tmp_path / "sized.txt"
        f.write_text("12345")

        from filebrain.extractors.plain_text import PlainTextExtractor

        result = PlainTextExtractor().extract(f)
        assert result.metadata["size_bytes"] == 5

    def test_metadata_includes_line_count(self, tmp_path: Path):
        f = tmp_path / "lines.txt"
        f.write_text("line1\nline2\nline3")

        from filebrain.extractors.plain_text import PlainTextExtractor

        result = PlainTextExtractor().extract(f)
        assert result.metadata["line_count"] == 3


class TestPlainTextEncodingDetection:
    """PlainTextExtractor handles different file encodings."""

    def test_reads_utf8_file(self, tmp_path: Path):
        f = tmp_path / "utf8.txt"
        f.write_text("café résumé", encoding="utf-8")

        from filebrain.extractors.plain_text import PlainTextExtractor

        result = PlainTextExtractor().extract(f)
        assert "café" in result.text

    def test_reads_latin1_file(self, tmp_path: Path):
        f = tmp_path / "latin1.txt"
        f.write_bytes("caf\xe9".encode("latin-1"))

        from filebrain.extractors.plain_text import PlainTextExtractor

        result = PlainTextExtractor().extract(f)
        assert "caf" in result.text


class TestPlainTextSupportedTypes:
    """PlainTextExtractor declares the file types it handles."""

    def test_supported_extensions(self):
        from filebrain.extractors.plain_text import PlainTextExtractor

        ext = PlainTextExtractor()
        assert ".txt" in ext.supported_extensions
        assert ".md" in ext.supported_extensions
        assert ".log" in ext.supported_extensions
        assert ".csv" in ext.supported_extensions

    def test_supported_mime_types(self):
        from filebrain.extractors.plain_text import PlainTextExtractor

        ext = PlainTextExtractor()
        assert "text/plain" in ext.supported_mime_types


class TestPlainTextErrorHandling:
    """PlainTextExtractor raises ExtractionError on failures."""

    def test_raises_on_missing_file(self, tmp_path: Path):
        from filebrain.extractors.plain_text import PlainTextExtractor

        missing = tmp_path / "nope.txt"
        with pytest.raises(ExtractionError):
            PlainTextExtractor().extract(missing)

    def test_raises_on_binary_file(self, tmp_path: Path):
        """Binary files containing null bytes should raise ExtractionError."""
        from filebrain.extractors.plain_text import PlainTextExtractor

        f = tmp_path / "binary.txt"
        # Null bytes are the standard indicator of binary content
        f.write_bytes(b"\x00\x01\x02\x03" * 100)

        with pytest.raises(ExtractionError):
            PlainTextExtractor().extract(f)
