"""Tests for the PdfExtractor."""

from pathlib import Path

import pytest

from filebrain.extractors.base import ExtractionError, ExtractionResult


def _create_pdf(path: Path, pages: list[str]) -> None:
    """Helper: create a simple PDF with text pages using pymupdf."""
    import pymupdf

    doc = pymupdf.Document()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()


class TestPdfExtraction:
    """PdfExtractor reads PDF files and returns their text content."""

    def test_extracts_single_page_pdf(self, tmp_path: Path):
        pdf = tmp_path / "single.pdf"
        _create_pdf(pdf, ["Hello from PDF"])

        from filebrain.extractors.pdf import PdfExtractor

        result = PdfExtractor().extract(pdf)

        assert isinstance(result, ExtractionResult)
        assert "Hello from PDF" in result.text

    def test_extracts_multi_page_pdf(self, tmp_path: Path):
        pdf = tmp_path / "multi.pdf"
        _create_pdf(pdf, ["Page one content", "Page two content"])

        from filebrain.extractors.pdf import PdfExtractor

        result = PdfExtractor().extract(pdf)

        assert "Page one content" in result.text
        assert "Page two content" in result.text

    def test_metadata_includes_page_count(self, tmp_path: Path):
        pdf = tmp_path / "pages.pdf"
        _create_pdf(pdf, ["A", "B", "C"])

        from filebrain.extractors.pdf import PdfExtractor

        result = PdfExtractor().extract(pdf)
        assert result.metadata["page_count"] == 3

    def test_metadata_includes_size_bytes(self, tmp_path: Path):
        pdf = tmp_path / "sized.pdf"
        _create_pdf(pdf, ["content"])

        from filebrain.extractors.pdf import PdfExtractor

        result = PdfExtractor().extract(pdf)
        assert result.metadata["size_bytes"] > 0


class TestPdfSupportedTypes:
    def test_supported_extensions(self):
        from filebrain.extractors.pdf import PdfExtractor

        assert ".pdf" in PdfExtractor().supported_extensions

    def test_supported_mime_types(self):
        from filebrain.extractors.pdf import PdfExtractor

        assert "application/pdf" in PdfExtractor().supported_mime_types


class TestPdfErrorHandling:
    def test_raises_on_missing_file(self, tmp_path: Path):
        from filebrain.extractors.pdf import PdfExtractor

        with pytest.raises(ExtractionError):
            PdfExtractor().extract(tmp_path / "missing.pdf")

    def test_raises_on_corrupt_pdf(self, tmp_path: Path):
        from filebrain.extractors.pdf import PdfExtractor

        corrupt = tmp_path / "corrupt.pdf"
        corrupt.write_text("this is not a pdf")

        with pytest.raises(ExtractionError):
            PdfExtractor().extract(corrupt)
