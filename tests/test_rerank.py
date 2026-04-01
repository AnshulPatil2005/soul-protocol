# test_rerank.py — Tests for smart memory reranking via LLM.
# Created: 2026-04-01 — Covers rerank_memories(), _parse_indices(), and
#   Soul.smart_recall() with mocked CognitiveEngine.

from __future__ import annotations

import pytest

from soul_protocol.runtime.memory.rerank import _parse_indices, rerank_memories
from soul_protocol.spec.memory import MemoryEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class MockEngine:
    """Minimal CognitiveEngine mock that returns a canned response."""

    def __init__(self, response: str):
        self._response = response

    async def think(self, prompt: str) -> str:
        return self._response


class FailingEngine:
    """CognitiveEngine mock that always raises."""

    async def think(self, prompt: str) -> str:
        raise RuntimeError("LLM unavailable")


def _make_memories(n: int) -> list[MemoryEntry]:
    """Create N distinct MemoryEntry instances for testing."""
    return [
        MemoryEntry(
            id=f"mem-{i}",
            content=f"Memory number {i} about topic {chr(64 + i)}",
            layer="episodic",
        )
        for i in range(1, n + 1)
    ]


# ---------------------------------------------------------------------------
# rerank_memories tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rerank_returns_subset():
    """10 candidates, limit 3 -> exactly 3 returned."""
    candidates = _make_memories(10)
    engine = MockEngine("3,1,5")
    result = await rerank_memories(candidates, "test query", engine, limit=3)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_rerank_preserves_order_from_llm():
    """Engine returns '3,1,5' -> memories in that exact order."""
    candidates = _make_memories(10)
    engine = MockEngine("3,1,5")
    result = await rerank_memories(candidates, "test query", engine, limit=3)
    assert result[0].id == "mem-3"
    assert result[1].id == "mem-1"
    assert result[2].id == "mem-5"


@pytest.mark.asyncio
async def test_rerank_fallback_on_engine_failure():
    """Engine raises -> returns first N from heuristic order."""
    candidates = _make_memories(10)
    engine = FailingEngine()
    result = await rerank_memories(candidates, "test query", engine, limit=3)
    assert len(result) == 3
    assert result[0].id == "mem-1"
    assert result[1].id == "mem-2"
    assert result[2].id == "mem-3"


@pytest.mark.asyncio
async def test_rerank_handles_small_candidate_set():
    """3 candidates, limit 5 -> all 3 returned (no LLM call needed)."""
    candidates = _make_memories(3)
    engine = MockEngine("should not be called")
    result = await rerank_memories(candidates, "test query", engine, limit=5)
    assert len(result) == 3
    assert [m.id for m in result] == ["mem-1", "mem-2", "mem-3"]


@pytest.mark.asyncio
async def test_rerank_fallback_on_empty_parse():
    """Engine returns gibberish with no numbers -> fallback to first N."""
    candidates = _make_memories(10)
    engine = MockEngine("I cannot determine relevance")
    result = await rerank_memories(candidates, "test query", engine, limit=3)
    # _parse_indices returns [] for no numbers, so fallback kicks in
    assert len(result) == 3
    assert result[0].id == "mem-1"


# ---------------------------------------------------------------------------
# _parse_indices tests
# ---------------------------------------------------------------------------


def test_parse_indices_valid():
    assert _parse_indices("3,1,7,2,5", max_index=10) == [3, 1, 7, 2, 5]


def test_parse_indices_with_noise():
    result = _parse_indices("The top ones are: 3, 1, and 7", max_index=10)
    assert result == [3, 1, 7]


def test_parse_indices_deduplication():
    result = _parse_indices("3,3,1,1", max_index=10)
    assert result == [3, 1]


def test_parse_indices_out_of_range():
    result = _parse_indices("99,1,2", max_index=5)
    assert result == [1, 2]


def test_parse_indices_empty_string():
    result = _parse_indices("", max_index=5)
    assert result == []


# ---------------------------------------------------------------------------
# Soul.smart_recall integration (mock-based)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_smart_recall_no_engine():
    """Soul without engine should fall back to regular recall (sliced)."""
    from unittest.mock import AsyncMock, patch

    from soul_protocol.runtime.soul import Soul

    # Create a minimal Soul with no engine
    mock_soul = AsyncMock(spec=Soul)
    mock_soul._engine = None

    # Build candidate memories
    candidates = _make_memories(10)

    # Call the real smart_recall with the mock's attributes
    mock_soul.recall = AsyncMock(return_value=candidates)
    mock_soul.smart_recall = Soul.smart_recall.__get__(mock_soul, Soul)

    result = await mock_soul.smart_recall("test query", limit=3)
    assert len(result) == 3
    # Without engine, should be first 3 from heuristic order
    assert result[0].id == "mem-1"
    assert result[1].id == "mem-2"
    assert result[2].id == "mem-3"


@pytest.mark.asyncio
async def test_smart_recall_with_engine():
    """Soul with engine should use rerank_memories for selection."""
    from unittest.mock import AsyncMock

    from soul_protocol.runtime.soul import Soul

    candidates = _make_memories(10)

    mock_soul = AsyncMock(spec=Soul)
    mock_soul._engine = MockEngine("5,3,1")
    mock_soul.recall = AsyncMock(return_value=candidates)
    mock_soul.smart_recall = Soul.smart_recall.__get__(mock_soul, Soul)

    result = await mock_soul.smart_recall("test query", limit=3)
    assert len(result) == 3
    assert result[0].id == "mem-5"
    assert result[1].id == "mem-3"
    assert result[2].id == "mem-1"
