# memory/recall.py — RecallEngine for cross-store memory retrieval.
# Created: 2026-02-22
# Unified keyword-based search across episodic, semantic, and procedural
# memory stores. Supports filtering by memory type and minimum importance.
# Results are merged and sorted by importance then recency.

from __future__ import annotations

from soul_protocol.memory.episodic import EpisodicStore
from soul_protocol.memory.procedural import ProceduralStore
from soul_protocol.memory.semantic import SemanticStore
from soul_protocol.types import MemoryEntry, MemoryType


class RecallEngine:
    """Cross-store memory retrieval engine.

    Queries all configured memory stores in parallel and merges results
    into a single ranked list. Supports type filtering and importance
    thresholds.
    """

    def __init__(
        self,
        episodic: EpisodicStore,
        semantic: SemanticStore,
        procedural: ProceduralStore,
    ) -> None:
        self._episodic = episodic
        self._semantic = semantic
        self._procedural = procedural

    async def recall(
        self,
        query: str,
        limit: int = 10,
        types: list[MemoryType] | None = None,
        min_importance: int = 0,
    ) -> list[MemoryEntry]:
        """Search across memory stores and return merged, ranked results.

        Args:
            query: Search string for keyword matching.
            limit: Maximum number of results to return.
            types: If provided, only search these memory types.
                   If None, search all stores.
            min_importance: Minimum importance score (1-10) for results.

        Returns:
            List of MemoryEntry sorted by importance desc, then recency desc.
        """
        results: list[MemoryEntry] = []
        search_all = types is None

        # Query each store based on requested types
        if search_all or MemoryType.EPISODIC in types:
            episodic_results = await self._episodic.search(query, limit=limit)
            results.extend(episodic_results)

        if search_all or MemoryType.SEMANTIC in types:
            semantic_results = await self._semantic.search(
                query, limit=limit, min_importance=min_importance
            )
            results.extend(semantic_results)

        if search_all or MemoryType.PROCEDURAL in types:
            procedural_results = await self._procedural.search(query, limit=limit)
            results.extend(procedural_results)

        # Apply importance filter to non-semantic results (semantic already filtered)
        if min_importance > 0:
            results = [r for r in results if r.importance >= min_importance]

        # Sort: importance descending, then created_at descending
        results.sort(key=lambda e: (-e.importance, -e.created_at.timestamp()))

        return results[:limit]
