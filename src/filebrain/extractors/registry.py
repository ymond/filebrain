"""Registry that maps file extensions to extractors."""

from pathlib import Path

from filebrain.extractors.base import Extractor
from filebrain.extractors.code import CodeExtractor
from filebrain.extractors.pdf import PdfExtractor
from filebrain.extractors.plain_text import PlainTextExtractor


class ExtractorRegistry:
    """Routes file paths to the appropriate extractor based on extension."""

    def __init__(self) -> None:
        self._ext_map: dict[str, Extractor] = {}
        # Register built-in extractors
        for extractor in (PlainTextExtractor(), PdfExtractor(), CodeExtractor()):
            self.register(extractor)

    def register(self, extractor: Extractor) -> None:
        """Register an extractor for all its supported extensions."""
        for ext in extractor.supported_extensions:
            self._ext_map[ext.lower()] = extractor

    def get_extractor(self, path: Path) -> Extractor | None:
        """Return the extractor for this file's extension, or None."""
        suffix = path.suffix.lower()
        return self._ext_map.get(suffix)
