"""Query engine: semantic search and LLM-powered Q&A with citations.

Two levels of query:
- SearchOnlyEngine: returns ranked file chunks (no LLM)
- QueryEngine: retrieves context, sends to LLM, returns answer with citations
"""

import json
import logging
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import URLError

from filebrain.store.vector import SearchResult, VectorStore

logger = logging.getLogger(__name__)

_DEFAULT_CHAT_MODEL = "qwen2.5:7b"
_OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

_RAG_SYSTEM_PROMPT = """\
You are a file search assistant. Answer questions based ONLY on the provided \
file excerpts below. Follow these rules strictly:

1. For every claim you make, cite the source file path in square brackets like \
[/path/to/file.ext].
2. If the excerpts don't contain enough information to answer the question, say \
"I don't have enough information in the indexed files to answer this."
3. Never invent or guess file paths. Only cite paths that appear in the excerpts.
4. Keep your answer concise and relevant to the question."""

_RAG_USER_TEMPLATE = """\
FILE EXCERPTS:
{excerpts}

QUESTION: {question}"""


@dataclass
class SourceReference:
    """A cited source file from a query answer."""

    source_path: Path
    chunk_text: str
    score: float


@dataclass
class QueryAnswer:
    """The result of an LLM-powered query: answer text and cited sources."""

    text: str
    sources: list[SourceReference] = field(default_factory=list)


class SearchOnlyEngine:
    """Semantic search engine — returns ranked file chunks without LLM."""

    def __init__(self, vector_store: VectorStore, embedding_generator) -> None:
        self._vectors = vector_store
        self._embedder = embedding_generator

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Embed the query and search the vector store."""
        embedding = self._embedder.embed(query)
        return self._vectors.search(embedding, limit=limit)


class QueryEngine:
    """RAG-powered query engine: retrieves context and asks the LLM.

    Uses semantic search to find relevant file chunks, then sends them
    as context to the local LLM with instructions to cite sources.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_generator,
        chat_model: str = _DEFAULT_CHAT_MODEL,
        ollama_url: str = _OLLAMA_CHAT_URL,
        context_limit: int = 5,
    ) -> None:
        self._search = SearchOnlyEngine(vector_store, embedding_generator)
        self._chat_model = chat_model
        self._ollama_url = ollama_url
        self._context_limit = context_limit

    def query(self, question: str) -> QueryAnswer:
        """Answer a question using RAG: retrieve context, ask LLM, return answer."""
        # Step 1: Retrieve relevant chunks
        results = self._search.search(question, limit=self._context_limit)

        if not results:
            return QueryAnswer(
                text="No indexed files found. Try scanning a directory first.",
                sources=[],
            )

        # Step 2: Format excerpts for the prompt
        excerpts = self._format_excerpts(results)

        # Step 3: Ask the LLM
        user_message = _RAG_USER_TEMPLATE.format(
            excerpts=excerpts, question=question
        )
        answer_text = self._chat(user_message)

        # Step 4: Build source references from the retrieved chunks
        sources = [
            SourceReference(
                source_path=r.source_path,
                chunk_text=r.chunk_text,
                score=r.score,
            )
            for r in results
        ]

        return QueryAnswer(text=answer_text, sources=sources)

    def _format_excerpts(self, results: list[SearchResult]) -> str:
        """Format search results as numbered excerpts with file paths."""
        lines = []
        for r in results:
            lines.append(f"[{r.source_path}]:\n{r.chunk_text}\n")
        return "\n".join(lines)

    def _chat(self, user_message: str) -> str:
        """Send a message to ollama's chat API and return the response."""
        payload = json.dumps({
            "model": self._chat_model,
            "messages": [
                {"role": "system", "content": _RAG_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
        }).encode()

        req = urllib.request.Request(
            self._ollama_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
        except URLError as e:
            logger.error("Failed to reach ollama chat: %s", e)
            return f"Error: Could not connect to local LLM ({e})"

        return data.get("message", {}).get("content", "No response from model.")
