"""Base extractor interface and common types.

Every file-type extractor implements the Extractor ABC. The pipeline uses
supported_extensions and supported_mime_types to route files to the right
extractor, then calls extract() to get text and metadata.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


class ExtractionError(Exception):
    """Raised when extraction fails (missing file, corrupt data, unsupported format)."""


@dataclass
class ExtractionResult:
    """The output of an extractor: extracted text and optional metadata."""

    text: str
    metadata: dict = field(default_factory=dict)


class Extractor(ABC):
    """Abstract base class that all file extractors must implement."""

    @property
    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """File extensions this extractor handles (e.g. {'.txt', '.md'})."""
        ...

    @property
    @abstractmethod
    def supported_mime_types(self) -> set[str]:
        """MIME types this extractor handles (e.g. {'text/plain'})."""
        ...

    @abstractmethod
    def extract(self, path: Path) -> ExtractionResult:
        """Extract text and metadata from the file at the given path.

        Raises ExtractionError if the file cannot be processed.
        """
        ...
