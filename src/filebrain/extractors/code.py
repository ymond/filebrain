"""Code file extractor for source code files."""

from pathlib import Path

from filebrain.extractors.base import ExtractionError, ExtractionResult, Extractor

# Maps file extension to language name
_EXT_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".java": "java",
    ".rb": "ruby",
    ".lisp": "lisp",
    ".cl": "lisp",
    ".el": "elisp",
    ".lua": "lua",
    ".r": "r",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".json": "json",
    ".xml": "xml",
    ".zig": "zig",
    ".nim": "nim",
    ".ex": "elixir",
    ".exs": "elixir",
    ".hs": "haskell",
    ".ml": "ocaml",
    ".scala": "scala",
    ".kt": "kotlin",
    ".swift": "swift",
    ".pl": "perl",
    ".php": "php",
}

_MIME_TYPES: set[str] = {
    "text/x-python",
    "text/javascript",
    "text/x-shellscript",
    "text/x-c",
    "text/x-java",
    "text/x-go",
    "text/x-rust",
}


class CodeExtractor(Extractor):
    """Extracts text from source code files with language detection."""

    @property
    def supported_extensions(self) -> set[str]:
        return set(_EXT_TO_LANGUAGE.keys())

    @property
    def supported_mime_types(self) -> set[str]:
        return _MIME_TYPES

    def extract(self, path: Path) -> ExtractionResult:
        if not path.exists():
            raise ExtractionError(f"File not found: {path}")

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ExtractionError(f"Cannot decode as text: {path}: {e}") from e

        language = _EXT_TO_LANGUAGE.get(path.suffix.lower(), "unknown")

        return ExtractionResult(
            text=text,
            metadata={
                "language": language,
                "line_count": len(text.splitlines()) if text else 0,
                "size_bytes": path.stat().st_size,
            },
        )
