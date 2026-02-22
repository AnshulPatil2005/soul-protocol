# memory/manager.py — MemoryManager facade orchestrating all memory subsystems.
# Created: 2026-02-22
# Top-level interface for the memory subsystem. Coordinates core memory,
# episodic/semantic/procedural stores, knowledge graph, and recall engine.
# Provides convenience methods for common operations and serialization.

from __future__ import annotations

from datetime import datetime

from soul_protocol.memory.core import CoreMemoryManager
from soul_protocol.memory.episodic import EpisodicStore
from soul_protocol.memory.graph import KnowledgeGraph
from soul_protocol.memory.procedural import ProceduralStore
from soul_protocol.memory.recall import RecallEngine
from soul_protocol.memory.semantic import SemanticStore
from soul_protocol.types import (
    CoreMemory,
    Interaction,
    MemoryEntry,
    MemorySettings,
    MemoryType,
)


class MemoryManager:
    """Facade that orchestrates all memory subsystems.

    Provides a unified API for:
      - Core memory (always-loaded persona + human profile)
      - Episodic memory (interaction history)
      - Semantic memory (extracted facts)
      - Procedural memory (how-to knowledge)
      - Knowledge graph (entity relationships)
      - Cross-store recall (unified search)
    """

    def __init__(self, core: CoreMemory, settings: MemorySettings) -> None:
        self._settings = settings

        # Initialize subsystems
        self._core_manager = CoreMemoryManager(core)
        self._episodic = EpisodicStore(max_entries=settings.episodic_max_entries)
        self._semantic = SemanticStore(max_facts=settings.semantic_max_facts)
        self._procedural = ProceduralStore()
        self._graph = KnowledgeGraph()
        self._recall_engine = RecallEngine(
            episodic=self._episodic,
            semantic=self._semantic,
            procedural=self._procedural,
        )

    # ---- Core memory ----

    def get_core(self) -> CoreMemory:
        """Return the current core memory."""
        return self._core_manager.get()

    def set_core(self, persona: str, human: str) -> None:
        """Replace core memory fields."""
        self._core_manager.set(persona=persona, human=human)

    async def edit_core(
        self, persona: str | None = None, human: str | None = None
    ) -> None:
        """Append to core memory fields (incremental update)."""
        self._core_manager.edit(persona=persona, human=human)

    # ---- Memory operations ----

    async def add(self, entry: MemoryEntry) -> str:
        """Add a memory entry to the appropriate store based on its type.

        Routes the entry to episodic, semantic, or procedural store.
        Returns the memory ID.
        """
        if entry.type == MemoryType.EPISODIC:
            # For direct episodic adds, store the entry in episodic store
            # by creating a minimal Interaction wrapper
            interaction = Interaction(
                user_input=entry.content,
                agent_output="",
                timestamp=entry.created_at,
            )
            return await self._episodic.add(interaction)
        elif entry.type == MemoryType.SEMANTIC:
            return await self._semantic.add(entry)
        elif entry.type == MemoryType.PROCEDURAL:
            return await self._procedural.add(entry)
        else:
            # Core memories are handled via set_core/edit_core
            raise ValueError(
                f"Cannot add memory of type {entry.type} via add(). "
                "Use set_core() or edit_core() for core memories."
            )

    async def add_episodic(self, interaction: Interaction) -> str:
        """Add an interaction as an episodic memory.

        This is the primary way to record interactions. Returns memory ID.
        """
        return await self._episodic.add(interaction)

    async def recall(
        self,
        query: str,
        limit: int = 10,
        types: list[MemoryType] | None = None,
        min_importance: int = 0,
    ) -> list[MemoryEntry]:
        """Search across all memory stores for relevant memories.

        Args:
            query: Keyword search string.
            limit: Maximum results.
            types: Filter to specific memory types (None = all).
            min_importance: Minimum importance threshold.

        Returns:
            Ranked list of matching MemoryEntry objects.
        """
        return await self._recall_engine.recall(
            query=query,
            limit=limit,
            types=types,
            min_importance=min_importance,
        )

    async def remove(self, memory_id: str) -> bool:
        """Remove a memory by ID from all stores.

        Tries each store until the memory is found and removed.
        Returns True if the memory was found and removed.
        """
        if await self._episodic.remove(memory_id):
            return True
        if await self._semantic.remove(memory_id):
            return True
        if await self._procedural.remove(memory_id):
            return True
        return False

    # ---- Extraction helpers (MVP placeholders) ----

    def extract_facts(self, interaction: Interaction) -> list[MemoryEntry]:
        """Extract semantic facts from an interaction.

        MVP placeholder: returns empty list. Future versions will use
        heuristics to detect patterns like "prefers X", "likes X",
        "uses X", "works with X" in agent_output.
        """
        # TODO: Implement heuristic fact extraction
        # Patterns to detect: "prefers X", "likes X", "uses X", "works with X"
        return []

    def extract_entities(self, interaction: Interaction) -> list[dict]:
        """Extract named entities from an interaction.

        MVP placeholder: returns empty list. Future versions will use
        simple heuristics (capitalized words) to identify potential entities.
        """
        # TODO: Implement simple entity extraction (capitalized words, etc.)
        return []

    # ---- Graph operations ----

    async def update_graph(self, entities: list[dict]) -> None:
        """Update the knowledge graph with extracted entities.

        Each entity dict should have:
          - name (str): entity name
          - entity_type (str, optional): type of entity
          - relationships (list[dict], optional): list of
            {target: str, relation: str} dicts
        """
        for entity in entities:
            name = entity.get("name", "")
            if not name:
                continue
            entity_type = entity.get("entity_type", "unknown")
            self._graph.add_entity(name, entity_type)

            for rel in entity.get("relationships", []):
                target = rel.get("target", "")
                relation = rel.get("relation", "related_to")
                if target:
                    self._graph.add_relationship(name, target, relation)

    # ---- Lifecycle ----

    async def clear(self) -> None:
        """Clear all memory stores and reset the knowledge graph.

        Core memory is preserved — use set_core() to reset it.
        """
        self._episodic = EpisodicStore(max_entries=self._settings.episodic_max_entries)
        self._semantic = SemanticStore(max_facts=self._settings.semantic_max_facts)
        self._procedural = ProceduralStore()
        self._graph = KnowledgeGraph()

        # Rebuild recall engine with new stores
        self._recall_engine = RecallEngine(
            episodic=self._episodic,
            semantic=self._semantic,
            procedural=self._procedural,
        )

    @property
    def settings(self) -> MemorySettings:
        """Return the current memory settings."""
        return self._settings

    # ---- Serialization ----

    def to_dict(self) -> dict:
        """Serialize the entire memory state to a plain dict.

        Includes core memory, all store entries, and the knowledge graph.
        Suitable for JSON persistence.
        """
        return {
            "core": self._core_manager.get().model_dump(),
            "episodic": [
                entry.model_dump(mode="json") for entry in self._episodic.entries()
            ],
            "semantic": [
                fact.model_dump(mode="json") for fact in self._semantic.facts()
            ],
            "procedural": [
                proc.model_dump(mode="json")
                for proc in sorted(
                    self._procedural._procedures.values(),
                    key=lambda e: (-e.importance, -e.created_at.timestamp()),
                )
            ],
            "graph": self._graph.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict, settings: MemorySettings) -> MemoryManager:
        """Deserialize memory state from a plain dict.

        Args:
            data: Dict as produced by to_dict().
            settings: MemorySettings to configure the new manager.

        Returns:
            A fully reconstituted MemoryManager.
        """
        # Restore core memory
        core_data = data.get("core", {})
        core = CoreMemory(**core_data)

        manager = cls(core=core, settings=settings)

        # Restore episodic memories
        for entry_data in data.get("episodic", []):
            entry = MemoryEntry(**entry_data)
            manager._episodic._memories[entry.id] = entry

        # Restore semantic facts
        for fact_data in data.get("semantic", []):
            fact = MemoryEntry(**fact_data)
            manager._semantic._facts[fact.id] = fact

        # Restore procedural memories
        for proc_data in data.get("procedural", []):
            proc = MemoryEntry(**proc_data)
            manager._procedural._procedures[proc.id] = proc

        # Restore knowledge graph
        graph_data = data.get("graph", {})
        if graph_data:
            manager._graph = KnowledgeGraph.from_dict(graph_data)

        return manager
