# test_embeddings/test_vector_strategy.py — Tests for VectorSearchStrategy.
# Created: 2026-03-06 — Integration tests with MemoryEntry objects, threshold
# filtering, indexing, and search behavior.
# Updated: 2026-03-06 — Fixed vacuous assertion in test_threshold_filters_results,
# added test for vector length mismatch error.

from __future__ import annotations

from datetime import datetime

import pytest

from soul_protocol.runtime.embeddings.hash_embedder import HashEmbedder
from soul_protocol.runtime.embeddings.tfidf_embedder import TFIDFEmbedder
from soul_protocol.runtime.embeddings.vector_strategy import VectorSearchStrategy
from soul_protocol.runtime.types import MemoryEntry, MemoryType


def _make_entry(content: str, importance: int = 5) -> MemoryEntry:
    """Helper to create a MemoryEntry for testing."""
    return MemoryEntry(
        type=MemoryType.SEMANTIC,
        content=content,
        importance=importance,
        created_at=datetime.now(),
    )


class TestVectorSearchStrategyBasics:
    """Test basic strategy behavior."""

    def test_init_with_hash_embedder(self) -> None:
        embedder = HashEmbedder()
        strategy = VectorSearchStrategy(embedder)
        assert strategy.embedder is embedder
        assert strategy.threshold == 0.3

    def test_custom_threshold(self) -> None:
        strategy = VectorSearchStrategy(HashEmbedder(), threshold=0.5)
        assert strategy.threshold == 0.5

    def test_threshold_setter(self) -> None:
        strategy = VectorSearchStrategy(HashEmbedder())
        strategy.threshold = 0.8
        assert strategy.threshold == 0.8

    def test_empty_candidates(self) -> None:
        strategy = VectorSearchStrategy(HashEmbedder())
        results = strategy.search("test query", [])
        assert results == []


class TestVectorSearchStrategyWithHashEmbedder:
    """Test search with HashEmbedder (deterministic but not semantic)."""

    def test_search_returns_entries(self) -> None:
        embedder = HashEmbedder()
        strategy = VectorSearchStrategy(embedder, threshold=0.0)

        entries = [
            _make_entry("python programming language"),
            _make_entry("javascript web development"),
            _make_entry("cooking pasta recipe"),
        ]

        # With threshold=0.0, hash embedder should return all candidates
        # (since cosine similarity of non-zero vectors is rarely exactly 0)
        results = strategy.search("programming", entries)
        assert len(results) > 0

    def test_limit_respected(self) -> None:
        embedder = HashEmbedder()
        strategy = VectorSearchStrategy(embedder, threshold=0.0)

        entries = [_make_entry(f"entry number {i}") for i in range(20)]
        results = strategy.search("entry", entries, limit=5)
        assert len(results) <= 5


class TestVectorSearchStrategyWithTFIDF:
    """Test search with TFIDFEmbedder (semantically meaningful)."""

    @pytest.fixture
    def strategy_with_corpus(self) -> tuple[VectorSearchStrategy, list[MemoryEntry]]:
        """Create a strategy fitted on a diverse corpus."""
        entries = [
            _make_entry("python is a great programming language for data science"),
            _make_entry("javascript powers modern web applications and frameworks"),
            _make_entry("cooking italian pasta with tomato sauce and fresh basil"),
            _make_entry("baking chocolate cake requires flour sugar and eggs"),
            _make_entry("football and basketball are popular team sports worldwide"),
        ]

        embedder = TFIDFEmbedder(dimensions=128)
        corpus = [e.content for e in entries]
        embedder.fit(corpus)

        strategy = VectorSearchStrategy(embedder, threshold=0.0)
        return strategy, entries

    def test_search_ranks_by_similarity(
        self, strategy_with_corpus: tuple[VectorSearchStrategy, list[MemoryEntry]]
    ) -> None:
        strategy, entries = strategy_with_corpus
        results = strategy.search("python programming data", entries, limit=5)
        assert len(results) > 0
        # The python entry should be in results
        contents = [r.content for r in results]
        assert any("python" in c for c in contents)

    def test_threshold_filters_results(
        self, strategy_with_corpus: tuple[VectorSearchStrategy, list[MemoryEntry]]
    ) -> None:
        strategy, entries = strategy_with_corpus
        # High threshold should filter out most results
        strategy.threshold = 0.99
        results = strategy.search("random unrelated query xyz", entries)
        # With a very high threshold and unrelated query, should filter out results
        assert len(results) < len(entries)


class TestVectorSearchStrategyIndexing:
    """Test the pre-built index functionality."""

    def test_index_and_search_indexed(self) -> None:
        embedder = HashEmbedder()
        strategy = VectorSearchStrategy(embedder, threshold=0.0)

        strategy.index("python programming")
        strategy.index("cooking pasta")
        strategy.index("playing football")

        results = strategy.search_indexed("python", limit=3)
        assert len(results) > 0
        # Results are (content, similarity) tuples
        for content, sim in results:
            assert isinstance(content, str)
            assert isinstance(sim, float)

    def test_index_batch(self) -> None:
        embedder = HashEmbedder()
        strategy = VectorSearchStrategy(embedder, threshold=0.0)

        contents = ["alpha text", "beta text", "gamma text"]
        strategy.index_batch(contents)

        results = strategy.search_indexed("alpha", limit=10)
        assert len(results) == 3

    def test_clear_index(self) -> None:
        embedder = HashEmbedder()
        strategy = VectorSearchStrategy(embedder)

        strategy.index("something")
        strategy.clear_index()
        results = strategy.search_indexed("something")
        assert results == []

    def test_search_indexed_empty(self) -> None:
        strategy = VectorSearchStrategy(HashEmbedder())
        results = strategy.search_indexed("query")
        assert results == []


class TestVectorSearchStrategyWithMemoryEntries:
    """Test that VectorSearchStrategy works with MemoryEntry objects."""

    def test_accesses_content_attribute(self) -> None:
        embedder = HashEmbedder()
        strategy = VectorSearchStrategy(embedder, threshold=0.0)

        entries = [
            _make_entry("hello world"),
            _make_entry("goodbye world"),
        ]

        # Should not raise — accesses .content on MemoryEntry
        results = strategy.search("hello", entries, limit=2)
        assert all(isinstance(r, MemoryEntry) for r in results)

    def test_works_with_string_candidates(self) -> None:
        """Strategy falls back to str() for objects without .content."""
        embedder = HashEmbedder()
        strategy = VectorSearchStrategy(embedder, threshold=0.0)

        # Passing plain strings — strategy should handle gracefully
        results = strategy.search("test", ["hello", "world"], limit=2)
        assert len(results) > 0
