# memory/semantic.py — SemanticStore for fact-based memories with confidence.
# Created: 2026-02-22
# Stores extracted facts (semantic knowledge) about the world, the user,
# or the soul itself. Each fact has importance and confidence scores.
# Supports keyword search with optional minimum importance filtering.

from __future__ import annotations

import uuid
from datetime import datetime

from soul_protocol.types import MemoryEntry, MemoryType


class SemanticStore:
    """In-memory store for semantic (fact-based) memories.

    Semantic memories represent general knowledge and extracted facts:
    "User prefers dark mode", "User works at Acme Corp", etc.
    Each fact carries importance (1-10) and confidence (0.0-1.0) scores.
    """

    def __init__(self, max_facts: int = 1000) -> None:
        self._max_facts = max_facts
        self._facts: dict[str, MemoryEntry] = {}

    async def add(self, entry: MemoryEntry) -> str:
        """Store a semantic memory entry.

        If the entry has no ID, one is generated. The type is forced
        to SEMANTIC regardless of what was passed in.

        Returns the memory ID.
        """
        if not entry.id:
            entry.id = uuid.uuid4().hex[:12]

        entry.type = MemoryType.SEMANTIC

        # Evict lowest-importance fact if at capacity
        if len(self._facts) >= self._max_facts:
            self._evict_least_important()

        self._facts[entry.id] = entry
        return entry.id

    async def search(
        self,
        query: str,
        limit: int = 10,
        min_importance: int = 0,
    ) -> list[MemoryEntry]:
        """Search facts by keyword with optional importance filter.

        Case-insensitive substring match on content. Results sorted by
        importance (descending), then created_at (most recent first).
        """
        query_lower = query.lower()
        matches = [
            fact
            for fact in self._facts.values()
            if query_lower in fact.content.lower()
            and fact.importance >= min_importance
        ]

        matches.sort(key=lambda e: (-e.importance, -e.created_at.timestamp()))
        return matches[:limit]

    async def remove(self, memory_id: str) -> bool:
        """Remove a fact by ID. Returns True if found and removed."""
        if memory_id in self._facts:
            del self._facts[memory_id]
            return True
        return False

    def facts(self) -> list[MemoryEntry]:
        """Return all semantic facts, sorted by importance descending."""
        return sorted(
            self._facts.values(),
            key=lambda e: (-e.importance, -e.created_at.timestamp()),
        )

    def _evict_least_important(self) -> None:
        """Remove the least important fact to make room."""
        if not self._facts:
            return
        least_id = min(
            self._facts,
            key=lambda mid: (
                self._facts[mid].importance,
                self._facts[mid].created_at.timestamp(),
            ),
        )
        del self._facts[least_id]
