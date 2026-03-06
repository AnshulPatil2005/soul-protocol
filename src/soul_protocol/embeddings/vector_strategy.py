# embeddings/vector_strategy.py — VectorSearchStrategy for semantic similarity search.
# Created: 2026-03-06 — Provides a search strategy that uses embedding vectors and
# cosine similarity to find relevant memory entries. Compatible with the existing
# memory search interface (works with MemoryEntry objects).

from __future__ import annotations

from typing import Any

from soul_protocol.embeddings.protocol import EmbeddingProvider
from soul_protocol.embeddings.similarity import cosine_similarity


class VectorSearchStrategy:
    """Search strategy using vector embeddings for semantic similarity.

    Embeds queries and candidate content on-the-fly, computing cosine
    similarity to rank results. Supports an optional pre-built index
    for performance, but can also embed candidates directly.

    Args:
        embedder: An EmbeddingProvider implementation for creating vectors.
        threshold: Minimum cosine similarity score to include a result.
            Default 0.3.
    """

    def __init__(self, embedder: EmbeddingProvider, threshold: float = 0.3) -> None:
        self._embedder = embedder
        self._threshold = threshold
        self._index: list[tuple[str, list[float]]] = []  # (content, vector) pairs

    @property
    def embedder(self) -> EmbeddingProvider:
        """The embedding provider used by this strategy."""
        return self._embedder

    @property
    def threshold(self) -> float:
        """Minimum similarity threshold for results."""
        return self._threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        """Set the minimum similarity threshold."""
        self._threshold = value

    def index(self, content: str) -> None:
        """Add content to the pre-built search index.

        Pre-computing embeddings via index() avoids re-embedding content
        on every search call. However, search() works without indexing
        by embedding candidates on-the-fly.

        Args:
            content: Text content to add to the index.
        """
        vec = self._embedder.embed(content)
        self._index.append((content, vec))

    def index_batch(self, contents: list[str]) -> None:
        """Add multiple content strings to the index.

        More efficient than calling index() repeatedly when the embedder
        supports batch operations.

        Args:
            contents: List of text contents to add to the index.
        """
        vectors = self._embedder.embed_batch(contents)
        for content, vec in zip(contents, vectors):
            self._index.append((content, vec))

    def clear_index(self) -> None:
        """Remove all entries from the search index."""
        self._index.clear()

    def search(self, query: str, candidates: list[Any], limit: int = 10) -> list[Any]:
        """Search using vector similarity over candidate objects.

        Each candidate must have a `.content` attribute (like MemoryEntry).
        Candidates are embedded on-the-fly and scored against the query.

        Args:
            query: The search query string.
            candidates: Objects with a `.content` attribute to search through.
            limit: Maximum number of results to return.

        Returns:
            List of candidates sorted by similarity (highest first),
            filtered by the threshold.
        """
        if not candidates:
            return []

        query_vec = self._embedder.embed(query)
        scored: list[tuple[float, Any]] = []

        for candidate in candidates:
            content = candidate.content if hasattr(candidate, "content") else str(candidate)
            candidate_vec = self._embedder.embed(content)
            sim = cosine_similarity(query_vec, candidate_vec)
            if sim >= self._threshold:
                scored.append((sim, candidate))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def search_indexed(self, query: str, limit: int = 10) -> list[tuple[str, float]]:
        """Search the pre-built index for similar content.

        Unlike search(), this uses the pre-built index and returns
        (content, similarity) tuples rather than candidate objects.

        Args:
            query: The search query string.
            limit: Maximum number of results to return.

        Returns:
            List of (content, similarity_score) tuples, sorted by
            similarity descending, filtered by threshold.
        """
        if not self._index:
            return []

        query_vec = self._embedder.embed(query)
        scored: list[tuple[float, str]] = []

        for content, vec in self._index:
            sim = cosine_similarity(query_vec, vec)
            if sim >= self._threshold:
                scored.append((sim, content))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [(content, sim) for sim, content in scored[:limit]]
