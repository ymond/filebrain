"""Qdrant-backed vector store for embedding storage and semantic search.

Wraps qdrant-client in local embedded mode (no server process needed).
Stores embeddings with source file metadata (path, chunk index, text)
and supports cosine similarity search and per-file deletion.
"""

import uuid
from dataclasses import dataclass
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

_COLLECTION = "filebrain"


@dataclass
class SearchResult:
    """A single search result with source file reference and similarity score."""

    source_path: Path
    chunk_index: int
    chunk_text: str
    score: float


class VectorStore:
    """Qdrant-backed store for file content embeddings.

    Uses local embedded mode: no server needed, data persists to a directory.
    Pass path=None for in-memory (testing), or path=Path("./data") for persistence.
    """

    def __init__(self, dimensions: int, path: Path | None = None) -> None:
        if path is not None:
            self._client = QdrantClient(path=str(path))
        else:
            self._client = QdrantClient(":memory:")

        # Create collection if it doesn't already exist
        collections = {c.name for c in self._client.get_collections().collections}
        if _COLLECTION not in collections:
            self._client.create_collection(
                _COLLECTION,
                vectors_config=VectorParams(
                    size=dimensions, distance=Distance.COSINE
                ),
            )

    def add_embedding(
        self,
        source_path: Path,
        chunk_index: int,
        chunk_text: str,
        embedding: list[float],
    ) -> None:
        """Store an embedding vector with its source file metadata."""
        self._client.upsert(
            _COLLECTION,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "source_path": str(source_path),
                        "chunk_index": chunk_index,
                        "chunk_text": chunk_text,
                    },
                )
            ],
        )

    def search(
        self, query_embedding: list[float], limit: int = 5
    ) -> list[SearchResult]:
        """Find the most similar embeddings by cosine similarity."""
        results = self._client.query_points(
            _COLLECTION,
            query=query_embedding,
            limit=limit,
            with_payload=True,
        )
        return [
            SearchResult(
                source_path=Path(point.payload["source_path"]),
                chunk_index=int(point.payload["chunk_index"]),
                chunk_text=str(point.payload["chunk_text"]),
                score=point.score,
            )
            for point in results.points
        ]

    def delete_by_source_path(self, source_path: Path) -> None:
        """Remove all embeddings associated with a source file."""
        self._client.delete(
            _COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="source_path",
                        match=MatchValue(value=str(source_path)),
                    )
                ]
            ),
        )

    def count(self) -> int:
        """Return the total number of stored embeddings."""
        info = self._client.get_collection(_COLLECTION)
        return info.points_count

    def close(self) -> None:
        """Close the underlying Qdrant client."""
        self._client.close()
