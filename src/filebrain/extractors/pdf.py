"""PDF extractor using pymupdf (fitz)."""

from pathlib import Path

import pymupdf

from filebrain.extractors.base import ExtractionError, ExtractionResult, Extractor


class PdfExtractor(Extractor):
    """Extracts text from PDF files using pymupdf."""

    @property
    def supported_extensions(self) -> set[str]:
        return {".pdf"}

    @property
    def supported_mime_types(self) -> set[str]:
        return {"application/pdf"}

    def extract(self, path: Path) -> ExtractionResult:
        if not path.exists():
            raise ExtractionError(f"File not found: {path}")

        try:
            doc = pymupdf.Document(str(path))
        except Exception as e:
            raise ExtractionError(f"Cannot open PDF: {path}: {e}") from e

        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())

        text = "\n".join(pages_text)
        page_count = len(doc)
        doc.close()

        return ExtractionResult(
            text=text,
            metadata={
                "page_count": page_count,
                "size_bytes": path.stat().st_size,
            },
        )
