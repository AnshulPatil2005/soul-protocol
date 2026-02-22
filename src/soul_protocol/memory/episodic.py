# memory/episodic.py — EpisodicStore for timestamped interaction memories.
# Created: 2026-02-22
# Stores chronological memories of user-agent interactions. Each interaction
# becomes a MemoryEntry with a unique ID. Supports keyword-based search
# with case-insensitive substring matching, sorted by importance then recency.

from __future__ import annotations

import uuid
from datetime import datetime

from soul_protocol.types import Interaction, MemoryEntry, MemoryType


class EpisodicStore:
    """In-memory store for episodic (interaction) memories.

    Episodic memories capture what happened — timestamped records of
    conversations and events. They form the soul's autobiographical memory.
    """

    def __init__(self, max_entries: int = 10000) -> None:
        self._max_entries = max_entries
        self._memories: dict[str, MemoryEntry] = {}

    async def add(self, interaction: Interaction) -> str:
        """Convert an Interaction into a MemoryEntry and store it.

        Returns the generated memory ID.
        """
        memory_id = uuid.uuid4().hex[:12]

        content = f"User: {interaction.user_input}\nAgent: {interaction.agent_output}"

        entry = MemoryEntry(
            id=memory_id,
            type=MemoryType.EPISODIC,
            content=content,
            importance=5,
            created_at=interaction.timestamp,
            entities=[],
        )

        # Evict oldest entry if at capacity
        if len(self._memories) >= self._max_entries:
            self._evict_oldest()

        self._memories[memory_id] = entry
        return memory_id

    async def get(self, memory_id: str) -> MemoryEntry | None:
        """Retrieve a single memory by ID, updating access metadata."""
        entry = self._memories.get(memory_id)
        if entry is not None:
            entry.last_accessed = datetime.now()
            entry.access_count += 1
        return entry

    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search memories by keyword (case-insensitive substring match).

        Results are sorted by importance (descending), then by created_at
        (most recent first).
        """
        query_lower = query.lower()
        matches = [
            entry
            for entry in self._memories.values()
            if query_lower in entry.content.lower()
        ]

        matches.sort(key=lambda e: (-e.importance, -e.created_at.timestamp()))
        return matches[:limit]

    async def remove(self, memory_id: str) -> bool:
        """Remove a memory by ID. Returns True if found and removed."""
        if memory_id in self._memories:
            del self._memories[memory_id]
            return True
        return False

    def entries(self) -> list[MemoryEntry]:
        """Return all episodic memories, sorted by created_at descending."""
        return sorted(
            self._memories.values(),
            key=lambda e: e.created_at.timestamp(),
            reverse=True,
        )

    def _evict_oldest(self) -> None:
        """Remove the oldest entry (by created_at) to make room."""
        if not self._memories:
            return
        oldest_id = min(
            self._memories,
            key=lambda mid: self._memories[mid].created_at.timestamp(),
        )
        del self._memories[oldest_id]
