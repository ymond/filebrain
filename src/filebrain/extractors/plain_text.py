"""Plain text extractor for .txt, .md, .log, and .csv files."""

from pathlib import Path

from filebrain.extractors.base import ExtractionError, ExtractionResult, Extractor

# Encodings to try in order when reading files
_ENCODINGS = ("utf-8", "latin-1")


class PlainTextExtractor(Extractor):
    """Extracts text from plain text files with encoding detection."""

    @property
    def supported_extensions(self) -> set[str]:
        return {".txt", ".md", ".log", ".csv"}

    @property
    def supported_mime_types(self) -> set[str]:
        return {"text/plain", "text/markdown", "text/csv"}

    def extract(self, path: Path) -> ExtractionResult:
        if not path.exists():
            raise ExtractionError(f"File not found: {path}")

        raw = path.read_bytes()
        if b"\x00" in raw:
            raise ExtractionError(f"File appears to be binary: {path}")
        text = self._decode(raw, path)

        return ExtractionResult(
            text=text,
            metadata={
                "size_bytes": len(raw),
                "line_count": len(text.splitlines()) if text else 0,
            },
        )

    def _decode(self, raw: bytes, path: Path) -> str:
        """Try common encodings in order. Raise ExtractionError if all fail."""
        for enc in _ENCODINGS:
            try:
                return raw.decode(enc)
            except (UnicodeDecodeError, ValueError):
                continue
        raise ExtractionError(f"Cannot decode file as text: {path}")
