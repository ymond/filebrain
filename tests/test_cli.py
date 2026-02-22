"""Tests for the CLI commands.

TDD Red phase: these tests define the CLI interface.
Tests use subprocess to verify the CLI entry point works, plus
unit tests for the command functions themselves.
"""

import hashlib
import subprocess
import sys
import urllib.request
from pathlib import Path
from unittest.mock import patch

import pytest

from filebrain.cli.app import build_pipeline, scan_command, status_command

DIMS = 768


def _ollama_available() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


ollama = pytest.mark.skipif(
    not _ollama_available(), reason="ollama not running"
)


class TestScanCommand:
    """filebrain scan <directory> indexes all files."""

    @ollama
    def test_scan_processes_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_text("Hello, filebrain!")
        db_dir = tmp_path / ".filebrain"

        pipeline, metadata, vectors = build_pipeline(db_dir)
        scan_command(tmp_path, pipeline)

        record = metadata.get_file(tmp_path / "a.txt")
        assert record is not None


class TestStatusCommand:
    """filebrain status shows index stats."""

    @ollama
    def test_status_shows_counts(self, tmp_path: Path, capsys) -> None:
        db_dir = tmp_path / ".filebrain"
        pipeline, metadata, vectors = build_pipeline(db_dir)

        (tmp_path / "a.txt").write_text("Content.")
        scan_command(tmp_path, pipeline)

        status_command(metadata, vectors)
        captured = capsys.readouterr()
        assert "processed" in captured.out.lower() or "1" in captured.out


class TestEntryPoint:
    """The filebrain CLI is invocable as a module."""

    def test_help_works(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "filebrain.cli", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "scan" in result.stdout
        assert "query" in result.stdout

    def test_status_no_db(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "filebrain.cli",
             "--db-dir", str(tmp_path / ".filebrain"), "status"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
