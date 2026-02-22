"""Filesystem watcher that feeds changed files into the processing pipeline.

Uses watchdog for live event monitoring and provides a batch scan mode
for initial indexing and nightly catch-up.
"""

import logging
import threading
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from filebrain.pipeline import ProcessingPipeline
from filebrain.store.metadata import MetadataStore
from filebrain.store.vector import VectorStore

logger = logging.getLogger(__name__)


class _PipelineHandler(FileSystemEventHandler):
    """Watchdog event handler that routes events to the pipeline."""

    def __init__(
        self,
        pipeline: ProcessingPipeline,
        metadata_store: MetadataStore,
        vector_store: VectorStore,
    ) -> None:
        self._pipeline = pipeline
        self._metadata = metadata_store
        self._vectors = vector_store

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        logger.info("File created: %s", path)
        self._pipeline.process_file(path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        logger.info("File modified: %s", path)
        self._pipeline.process_file(path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        logger.info("File deleted: %s", path)
        self._vectors.delete_by_source_path(path)
        self._metadata.delete_file(path)


class FileWatcher:
    """Watches directories for file changes and processes them.

    Two modes:
    - scan(directory): One-shot batch scan of all files in a tree.
    - start(directory) / stop(): Live monitoring using inotify via watchdog.
    """

    def __init__(
        self,
        pipeline: ProcessingPipeline,
        metadata_store: MetadataStore,
        vector_store: VectorStore,
    ) -> None:
        self._pipeline = pipeline
        self._metadata = metadata_store
        self._vectors = vector_store
        self._observer: Observer | None = None

    def scan(self, directory: Path) -> dict[str, int]:
        """Batch scan: process all files in the directory tree.

        Returns stats dict with processed/failed/skipped counts.
        """
        return self._pipeline.process_directory(directory)

    def start(self, directory: Path) -> None:
        """Start watching directory for live filesystem events."""
        handler = _PipelineHandler(
            self._pipeline, self._metadata, self._vectors
        )
        self._observer = Observer()
        self._observer.schedule(handler, str(directory), recursive=True)
        self._observer.start()
        logger.info("Watching %s for changes", directory)

    def stop(self) -> None:
        """Stop watching for filesystem events."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None
            logger.info("Watcher stopped")
