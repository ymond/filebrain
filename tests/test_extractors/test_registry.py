"""Tests for the ExtractorRegistry."""

from pathlib import Path

from filebrain.extractors.base import Extractor


class TestRegistryReturnsCorrectExtractor:
    """The registry maps file paths to the right extractor based on extension."""

    def test_returns_plain_text_extractor_for_txt(self):
        from filebrain.extractors.plain_text import PlainTextExtractor
        from filebrain.extractors.registry import ExtractorRegistry

        registry = ExtractorRegistry()
        extractor = registry.get_extractor(Path("notes.txt"))

        assert isinstance(extractor, PlainTextExtractor)

    def test_returns_plain_text_extractor_for_md(self):
        from filebrain.extractors.plain_text import PlainTextExtractor
        from filebrain.extractors.registry import ExtractorRegistry

        registry = ExtractorRegistry()
        extractor = registry.get_extractor(Path("README.md"))

        assert isinstance(extractor, PlainTextExtractor)

    def test_returns_pdf_extractor_for_pdf(self):
        from filebrain.extractors.pdf import PdfExtractor
        from filebrain.extractors.registry import ExtractorRegistry

        registry = ExtractorRegistry()
        extractor = registry.get_extractor(Path("report.pdf"))

        assert isinstance(extractor, PdfExtractor)

    def test_returns_code_extractor_for_py(self):
        from filebrain.extractors.code import CodeExtractor
        from filebrain.extractors.registry import ExtractorRegistry

        registry = ExtractorRegistry()
        extractor = registry.get_extractor(Path("main.py"))

        assert isinstance(extractor, CodeExtractor)

    def test_returns_code_extractor_for_js(self):
        from filebrain.extractors.code import CodeExtractor
        from filebrain.extractors.registry import ExtractorRegistry

        registry = ExtractorRegistry()
        extractor = registry.get_extractor(Path("app.js"))

        assert isinstance(extractor, CodeExtractor)


class TestRegistryReturnsNoneForUnrecognized:
    """The registry returns None for file types it doesn't know about."""

    def test_returns_none_for_unknown_extension(self):
        from filebrain.extractors.registry import ExtractorRegistry

        registry = ExtractorRegistry()
        result = registry.get_extractor(Path("photo.xyz123"))

        assert result is None

    def test_returns_none_for_no_extension(self):
        from filebrain.extractors.registry import ExtractorRegistry

        registry = ExtractorRegistry()
        result = registry.get_extractor(Path("Makefile"))

        assert result is None


class TestRegistryCustomExtractors:
    """The registry supports registering custom extractors."""

    def test_register_custom_extractor(self):
        from filebrain.extractors.base import ExtractionResult
        from filebrain.extractors.registry import ExtractorRegistry

        class CustomExtractor(Extractor):
            @property
            def supported_extensions(self) -> set[str]:
                return {".custom"}

            @property
            def supported_mime_types(self) -> set[str]:
                return {"application/x-custom"}

            def extract(self, path: Path) -> ExtractionResult:
                return ExtractionResult(text="custom")

        registry = ExtractorRegistry()
        registry.register(CustomExtractor())

        extractor = registry.get_extractor(Path("file.custom"))
        assert isinstance(extractor, CustomExtractor)
