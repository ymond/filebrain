"""CLI application for filebrain.

Provides commands: scan, watch, query, status.
Uses argparse from stdlib — no extra dependencies.
"""

import argparse
import logging
import signal
import sys
from pathlib import Path

from filebrain.embeddings.chunker import TextChunker
from filebrain.embeddings.generator import EmbeddingGenerator
from filebrain.extractors.registry import ExtractorRegistry
from filebrain.pipeline import ProcessingPipeline
from filebrain.query.engine import QueryEngine, SearchOnlyEngine
from filebrain.store.metadata import FileStatus, MetadataStore
from filebrain.store.vector import VectorStore
from filebrain.watcher.watcher import FileWatcher

_DIMS = 768  # nomic-embed-text dimensionality
_DEFAULT_DB_DIR = Path.home() / ".filebrain"


def build_pipeline(
    db_dir: Path,
) -> tuple[ProcessingPipeline, MetadataStore, VectorStore]:
    """Wire up all pipeline components using the given database directory."""
    db_dir.mkdir(parents=True, exist_ok=True)

    metadata = MetadataStore(db_dir / "metadata.db")
    vectors = VectorStore(dimensions=_DIMS, path=db_dir / "vectors")
    registry = ExtractorRegistry()
    chunker = TextChunker()
    embedder = EmbeddingGenerator()

    pipeline = ProcessingPipeline(
        metadata_store=metadata,
        vector_store=vectors,
        extractor_registry=registry,
        chunker=chunker,
        embedding_generator=embedder,
    )
    return pipeline, metadata, vectors


def scan_command(directory: Path, pipeline: ProcessingPipeline) -> None:
    """Run batch scan on a directory tree."""
    print(f"Scanning {directory}...")
    stats = pipeline.process_directory(directory)
    print(f"Done. Processed: {stats['processed']}, "
          f"Failed: {stats['failed']}, Skipped: {stats['skipped']}")


def watch_command(
    directory: Path,
    pipeline: ProcessingPipeline,
    metadata: MetadataStore,
    vectors: VectorStore,
) -> None:
    """Start watching a directory for changes."""
    watcher = FileWatcher(pipeline=pipeline, metadata_store=metadata, vector_store=vectors)

    # Initial scan
    print(f"Initial scan of {directory}...")
    stats = watcher.scan(directory)
    print(f"Scan complete. Processed: {stats['processed']}, "
          f"Failed: {stats['failed']}, Skipped: {stats['skipped']}")

    # Start live watching
    print(f"Watching {directory} for changes (Ctrl+C to stop)...")
    watcher.start(directory)

    def handle_signal(sig, frame):
        print("\nStopping watcher...")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Block until signal
    signal.pause()


def query_command(
    question: str, vectors: VectorStore, use_llm: bool = True
) -> None:
    """Answer a question using indexed files."""
    embedder = EmbeddingGenerator()

    if use_llm:
        engine = QueryEngine(vector_store=vectors, embedding_generator=embedder)
        answer = engine.query(question)
        print(answer.text)
        if answer.sources:
            print("\nSources:")
            seen = set()
            for s in answer.sources:
                if s.source_path not in seen:
                    print(f"  - {s.source_path}")
                    seen.add(s.source_path)
    else:
        engine = SearchOnlyEngine(vector_store=vectors, embedding_generator=embedder)
        results = engine.search(question)
        if not results:
            print("No matching files found.")
            return
        for r in results:
            print(f"  [{r.score:.3f}] {r.source_path}")
            print(f"    {r.chunk_text[:100]}...")


def status_command(metadata: MetadataStore, vectors: VectorStore) -> None:
    """Show index statistics."""
    counts = metadata.count_by_status()
    total_embeddings = vectors.count()

    print("Filebrain Index Status")
    print("=" * 30)
    print(f"  Pending:    {counts[FileStatus.PENDING]}")
    print(f"  Processed:  {counts[FileStatus.PROCESSED]}")
    print(f"  Failed:     {counts[FileStatus.FAILED]}")
    print(f"  Embeddings: {total_embeddings}")


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="filebrain",
        description="Local-first file indexing and semantic search",
    )
    parser.add_argument(
        "--db-dir", type=Path, default=_DEFAULT_DB_DIR,
        help=f"Database directory (default: {_DEFAULT_DB_DIR})",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose logging",
    )

    subparsers = parser.add_subparsers(dest="command")

    # scan
    scan_parser = subparsers.add_parser("scan", help="Scan and index a directory")
    scan_parser.add_argument("directory", type=Path, help="Directory to scan")

    # watch
    watch_parser = subparsers.add_parser("watch", help="Watch a directory for changes")
    watch_parser.add_argument("directory", type=Path, help="Directory to watch")

    # query
    query_parser = subparsers.add_parser("query", help="Ask a question about your files")
    query_parser.add_argument("question", nargs="+", help="Your question")
    query_parser.add_argument(
        "--search-only", action="store_true",
        help="Show matching files without LLM answer",
    )

    # status
    subparsers.add_parser("status", help="Show index statistics")

    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    if args.command is None:
        parser.print_help()
        return

    if args.command == "status":
        db_dir = args.db_dir
        db_dir.mkdir(parents=True, exist_ok=True)
        metadata = MetadataStore(db_dir / "metadata.db")
        vectors = VectorStore(dimensions=_DIMS, path=db_dir / "vectors")
        status_command(metadata, vectors)
        return

    pipeline, metadata, vectors = build_pipeline(args.db_dir)

    if args.command == "scan":
        scan_command(args.directory, pipeline)
    elif args.command == "watch":
        watch_command(args.directory, pipeline, metadata, vectors)
    elif args.command == "query":
        question = " ".join(args.question)
        query_command(question, vectors, use_llm=not args.search_only)
