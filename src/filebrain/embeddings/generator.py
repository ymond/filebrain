"""Embedding generator using ollama's local API.

Calls ollama's /api/embed endpoint to convert text into vectors
using nomic-embed-text (or any other embedding model pulled in ollama).
No external dependencies beyond urllib — ollama runs locally.
"""

import json
import urllib.request
from urllib.error import URLError

_DEFAULT_MODEL = "nomic-embed-text"
_OLLAMA_URL = "http://localhost:11434/api/embed"


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


class EmbeddingGenerator:
    """Generates embeddings by calling ollama's local embedding API."""

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        ollama_url: str = _OLLAMA_URL,
    ) -> None:
        self._model = model
        self._url = ollama_url

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string."""
        result = self._call_api(text)
        return result[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Uses ollama's batch embedding support (passing input as a list).
        Returns an empty list for empty input.
        """
        if not texts:
            return []
        return self._call_api(texts)

    def _call_api(self, input_data: str | list[str]) -> list[list[float]]:
        """Call ollama's /api/embed endpoint."""
        payload = json.dumps({
            "model": self._model,
            "input": input_data,
        }).encode()

        req = urllib.request.Request(
            self._url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except URLError as e:
            raise EmbeddingError(
                f"Failed to connect to ollama at {self._url}: {e}"
            ) from e

        if "embeddings" not in data:
            raise EmbeddingError(f"Unexpected response from ollama: {data}")

        return data["embeddings"]
