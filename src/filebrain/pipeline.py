"""Processing pipeline: file → extract → chunk → embed → store.

Coordinates the full flow from a file path to stored embeddings.
Each step is a separate component; the pipeline wires them together.
"""

import hashlib
import logging
from pathlib import Path

from filebrain.embeddings.chunker import TextChunker
from filebrain.extractors.base import ExtractionError
from filebrain.extractors.registry import ExtractorRegistry
from filebrain.store.metadata import FileStatus, MetadataStore
from filebrain.store.vector import VectorStore

logger = logging.getLogger(__name__)


def _file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


class ProcessingPipeline:
    """Orchestrates extraction, chunking, embedding, and storage for files."""

    def __init__(
        self,
        metadata_store: MetadataStore,
        vector_store: VectorStore,
        extractor_registry: ExtractorRegistry,
        chunker: TextChunker,
        embedding_generator,  # EmbeddingGenerator or any duck-typed equivalent
    ) -> None:
        self._metadata = metadata_store
        self._vectors = vector_store
        self._registry = extractor_registry
        self._chunker = chunker
        self._embedder = embedding_generator

    def process_file(self, path: Path) -> None:
        """Process a single file through the full pipeline.

        Steps:
        1. Compute content hash
        2. Check if file has changed since last processing
        3. Extract text using the appropriate extractor
        4. Chunk the extracted text
        5. Generate embeddings for each chunk
        6. Store embeddings in the vector store
        7. Update metadata store with status

        If any step fails, the file is marked as failed with the error.
        """
        try:
            self._do_process(path)
        except Exception as e:
            logger.warning("Failed to process %s: %s", path, e)
            # Ensure file record exists so we can mark it failed
            self._ensure_record(path)
            self._metadata.mark_failed(path, str(e))

    def _do_process(self, path: Path) -> None:
        """Inner processing logic — raises on failure."""
        # Step 1: Compute hash (also verifies file exists)
        content_hash = _file_hash(path)
        stat = path.stat()

        # Step 2: Upsert file record
        self._metadata.upsert_file(
            path=path,
            content_hash=content_hash,
            size=stat.st_size,
            mtime=stat.st_mtime,
            file_type=path.suffix.lower(),
        )

        # Step 3: Check if already processed with same hash
        record = self._metadata.get_file(path)
        if record and record.status == FileStatus.PROCESSED:
            logger.debug("Skipping %s — already processed with same hash", path)
            return

        # Step 4: Find extractor
        extractor = self._registry.get_extractor(path)
        if extractor is None:
            raise ExtractionError(f"No extractor for file type: {path.suffix}")

        # Step 5: Extract text
        result = extractor.extract(path)

        # Step 6: Chunk the text
        chunks = self._chunker.chunk(result.text)
        if not chunks:
            # File extracted but no text content
            self._metadata.mark_processed(path, "")
            return

        # Step 7: Generate embeddings
        embeddings = self._embedder.embed_batch(chunks)

        # Step 8: Remove old embeddings for this file (in case of reprocessing)
        self._vectors.delete_by_source_path(path)

        # Step 9: Store new embeddings
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            self._vectors.add_embedding(
                source_path=path,
                chunk_index=i,
                chunk_text=chunk_text,
                embedding=embedding,
            )

        # Step 10: Mark as processed
        self._metadata.mark_processed(path, result.text)

    def _ensure_record(self, path: Path) -> None:
        """Ensure a file record exists in the metadata store for error tracking."""
        if self._metadata.get_file(path) is not None:
            return
        # Create a minimal record — we may not have hash/stat if the file is missing
        try:
            content_hash = _file_hash(path)
            stat = path.stat()
            self._metadata.upsert_file(
                path=path,
                content_hash=content_hash,
                size=stat.st_size,
                mtime=stat.st_mtime,
                file_type=path.suffix.lower(),
            )
        except OSError:
            # File doesn't exist — store with placeholder values
            self._metadata.upsert_file(
                path=path,
                content_hash="",
                size=0,
                mtime=0.0,
                file_type=path.suffix.lower(),
            )

    def process_directory(self, directory: Path) -> dict[str, int]:
        """Process all files in a directory tree.

        Returns a dict with counts: processed, failed, skipped.
        """
        stats = {"processed": 0, "failed": 0, "skipped": 0}

        for file_path in sorted(directory.rglob("*")):
            if not file_path.is_file():
                continue

            record_before = self._metadata.get_file(file_path)
            self.process_file(file_path)
            record_after = self._metadata.get_file(file_path)

            if record_after is None:
                continue

            if record_after.status == FileStatus.FAILED:
                stats["failed"] += 1
            elif (
                record_before
                and record_before.status == FileStatus.PROCESSED
                and record_before.content_hash == record_after.content_hash
            ):
                stats["skipped"] += 1
            else:
                stats["processed"] += 1

        return stats
