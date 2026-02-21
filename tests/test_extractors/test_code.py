"""Tests for the CodeExtractor."""

from pathlib import Path

import pytest

from filebrain.extractors.base import ExtractionError, ExtractionResult


class TestCodeExtraction:
    """CodeExtractor reads source code files and returns their content."""

    def test_extracts_python_file(self, tmp_path: Path):
        f = tmp_path / "hello.py"
        f.write_text('def greet():\n    """Say hello."""\n    print("hello")\n')

        from filebrain.extractors.code import CodeExtractor

        result = CodeExtractor().extract(f)

        assert isinstance(result, ExtractionResult)
        assert "def greet():" in result.text

    def test_extracts_javascript_file(self, tmp_path: Path):
        f = tmp_path / "app.js"
        f.write_text("function main() { return 42; }\n")

        from filebrain.extractors.code import CodeExtractor

        result = CodeExtractor().extract(f)
        assert "function main()" in result.text

    def test_extracts_shell_script(self, tmp_path: Path):
        f = tmp_path / "build.sh"
        f.write_text("#!/bin/bash\necho 'building'\n")

        from filebrain.extractors.code import CodeExtractor

        result = CodeExtractor().extract(f)
        assert "echo 'building'" in result.text

    def test_metadata_includes_language(self, tmp_path: Path):
        f = tmp_path / "lib.py"
        f.write_text("x = 1\n")

        from filebrain.extractors.code import CodeExtractor

        result = CodeExtractor().extract(f)
        assert result.metadata["language"] == "python"

    def test_metadata_includes_line_count(self, tmp_path: Path):
        f = tmp_path / "small.go"
        f.write_text("package main\n\nfunc main() {}\n")

        from filebrain.extractors.code import CodeExtractor

        result = CodeExtractor().extract(f)
        assert result.metadata["line_count"] == 3

    def test_metadata_includes_size_bytes(self, tmp_path: Path):
        f = tmp_path / "tiny.py"
        f.write_text("pass\n")

        from filebrain.extractors.code import CodeExtractor

        result = CodeExtractor().extract(f)
        assert result.metadata["size_bytes"] == 5


class TestCodeSupportedTypes:
    def test_supported_extensions_include_common_languages(self):
        from filebrain.extractors.code import CodeExtractor

        ext = CodeExtractor()
        for expected in [".py", ".js", ".sh", ".go", ".rs", ".ts", ".c", ".cpp", ".java", ".rb", ".lisp"]:
            assert expected in ext.supported_extensions, f"{expected} not in supported_extensions"

    def test_supported_mime_types(self):
        from filebrain.extractors.code import CodeExtractor

        ext = CodeExtractor()
        assert "text/x-python" in ext.supported_mime_types


class TestCodeErrorHandling:
    def test_raises_on_missing_file(self, tmp_path: Path):
        from filebrain.extractors.code import CodeExtractor

        with pytest.raises(ExtractionError):
            CodeExtractor().extract(tmp_path / "missing.py")
