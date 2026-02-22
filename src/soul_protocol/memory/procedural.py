# memory/procedural.py — ProceduralStore for how-to memories.
# Created: 2026-02-22
# Stores procedural knowledge — instructions, workflows, and learned
# procedures the soul can reference when performing tasks. Supports
# keyword-based search with case-insensitive substring matching.

from __future__ import annotations

import uuid
from datetime import datetime

from soul_protocol.types import MemoryEntry, MemoryType


class ProceduralStore:
    """In-memory store for procedural (how-to) memories.

    Procedural memories capture learned processes and instructions:
    "To deploy, run X then Y", "User prefers PR workflow over direct push", etc.
    """

    def __init__(self) -> None:
        self._procedures: dict[str, MemoryEntry] = {}

    async def add(self, entry: MemoryEntry) -> str:
        """Store a procedural memory entry.

        If the entry has no ID, one is generated. The type is forced
        to PROCEDURAL regardless of what was passed in.

        Returns the memory ID.
        """
        if not entry.id:
            entry.id = uuid.uuid4().hex[:12]

        entry.type = MemoryType.PROCEDURAL
        self._procedures[entry.id] = entry
        return entry.id

    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search procedures by keyword (case-insensitive substring match).

        Results sorted by importance (descending), then created_at
        (most recent first).
        """
        query_lower = query.lower()
        matches = [
            proc
            for proc in self._procedures.values()
            if query_lower in proc.content.lower()
        ]

        matches.sort(key=lambda e: (-e.importance, -e.created_at.timestamp()))
        return matches[:limit]

    async def remove(self, memory_id: str) -> bool:
        """Remove a procedure by ID. Returns True if found and removed."""
        if memory_id in self._procedures:
            del self._procedures[memory_id]
            return True
        return False
