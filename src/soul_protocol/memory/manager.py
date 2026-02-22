# memory/manager.py — MemoryManager facade orchestrating all memory subsystems.
# Updated: 2026-02-22 — Improved to_dict() to use entries() for procedural
#   store; improved from_dict() to use MemoryEntry.model_validate() for safe
#   deserialization. Full round-trip serialization for all memory tiers.
#   Heuristic fact extraction (extract_facts) and entity extraction
#   (extract_entities) using regex pattern matching.

from __future__ import annotations

import re
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


# ---------------------------------------------------------------------------
# Heuristic fact-extraction patterns
# Each tuple: (compiled_regex, importance_score, template_string)
# Templates use {0}, {1}, ... for captured groups.
# ---------------------------------------------------------------------------

FACT_PATTERNS: list[tuple[re.Pattern[str], int, str]] = [
    (re.compile(r"my name is (\w+)", re.IGNORECASE), 9, "User's name is {0}"),
    (
        re.compile(r"i(?:'m| am) (?:a |an )?(\w[\w\s]{2,30})", re.IGNORECASE),
        7,
        "User is {0}",
    ),
    (
        re.compile(r"i (?:prefer|like|love) (\w[\w\s]{2,30})", re.IGNORECASE),
        7,
        "User prefers {0}",
    ),
    (
        re.compile(r"i (?:hate|dislike|don'?t like) (\w[\w\s]{2,30})", re.IGNORECASE),
        7,
        "User dislikes {0}",
    ),
    (
        re.compile(r"i (?:use|work with|am using) (\w[\w\s]{2,30})", re.IGNORECASE),
        6,
        "User uses {0}",
    ),
    (
        re.compile(
            r"i(?:'m| am) (?:building|creating|making) (\w[\w\s]{2,30})", re.IGNORECASE
        ),
        7,
        "User is building {0}",
    ),
    (
        re.compile(r"i (?:work at|work for) (\w[\w\s]{2,30})", re.IGNORECASE),
        8,
        "User works at {0}",
    ),
    (
        re.compile(r"i(?:'m| am) from (\w[\w\s]{2,30})", re.IGNORECASE),
        7,
        "User is from {0}",
    ),
    (
        re.compile(r"i live in (\w[\w\s]{2,30})", re.IGNORECASE),
        7,
        "User lives in {0}",
    ),
    (
        re.compile(r"my favorite (\w+) is (\w[\w\s]{2,30})", re.IGNORECASE),
        6,
        "User's favorite {0} is {1}",
    ),
]

# ---------------------------------------------------------------------------
# Known technology names (lowercase) for entity extraction
# ---------------------------------------------------------------------------

KNOWN_TECH: set[str] = {
    "python", "javascript", "typescript", "rust", "go", "java", "ruby", "swift",
    "react", "vue", "angular", "django", "flask", "fastapi", "express", "nextjs",
    "docker", "kubernetes", "aws", "gcp", "azure", "firebase", "supabase",
    "postgres", "mysql", "mongodb", "redis", "sqlite",
    "git", "github", "gitlab", "vscode", "neovim", "vim",
    "linux", "macos", "windows", "ubuntu",
    "openai", "anthropic", "claude", "gpt", "gemini", "ollama", "langchain",
    "pocketpaw", "soul-protocol",
}

# Regex-to-relation mapping for entity relationship inference.
# Each tuple: (compiled_regex, relation_verb)
ENTITY_RELATIONS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"i (?:use|am using|work with)\b", re.IGNORECASE), "uses"),
    (re.compile(r"i(?:'m| am) (?:building|creating|making)\b", re.IGNORECASE), "builds"),
    (re.compile(r"i (?:prefer|like|love)\b", re.IGNORECASE), "prefers"),
    (re.compile(r"i (?:work at|work for)\b", re.IGNORECASE), "works_at"),
    (re.compile(r"i(?:'m| am) (?:learning|studying)\b", re.IGNORECASE), "learns"),
]

# Words that should never be treated as proper-noun entities even when
# capitalised (common sentence starters, pronouns, filler words).
_STOP_WORDS: set[str] = {
    "i", "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "it", "its", "my", "we", "our", "you", "your", "he", "she", "they",
    "this", "that", "these", "those", "what", "which", "who", "how",
    "can", "could", "will", "would", "should", "do", "does", "did",
    "but", "and", "or", "not", "no", "yes", "so", "if", "then",
    "also", "just", "very", "really", "well", "here", "there",
    "user", "agent", "let", "me", "hi", "hello", "hey", "thanks",
    "thank", "please", "sure", "okay", "ok",
}


def _clean_captured(text: str) -> str:
    """Strip whitespace and trailing punctuation from a regex capture."""
    return text.strip().rstrip(".,;:!?")


def _token_overlap_score(a: str, b: str) -> float:
    """Return Jaccard token-overlap score between two strings (0.0-1.0)."""
    tokens_a = set(a.lower().split())
    tokens_b = set(b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


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
        """Extract semantic facts from an interaction using heuristic patterns.

        Scans the combined text of user_input and agent_output for
        predefined regex patterns (preferences, identity, tech usage, etc.).
        Each match produces a MemoryEntry of type SEMANTIC.

        Deduplication: if an existing semantic fact has a token-overlap
        score > 0.7 with a newly extracted fact, the new fact is skipped.

        Returns:
            List of MemoryEntry objects ready to be added to the semantic store.
        """
        combined = f"{interaction.user_input} {interaction.agent_output}"
        extracted: list[MemoryEntry] = []
        seen_contents: set[str] = set()

        # Collect existing semantic fact contents for dedup comparison
        existing_facts = [f.content for f in self._semantic.facts()]

        for pattern, importance, template in FACT_PATTERNS:
            for match in pattern.finditer(combined):
                groups = [_clean_captured(g) for g in match.groups()]
                # Skip if any captured group is empty after cleaning
                if not all(groups):
                    continue

                content = template.format(*groups)

                # Skip exact duplicates within this extraction batch
                if content in seen_contents:
                    continue

                # Skip if a sufficiently similar fact already exists
                is_duplicate = any(
                    _token_overlap_score(content, existing) > 0.7
                    for existing in existing_facts
                )
                if is_duplicate:
                    continue

                seen_contents.add(content)
                extracted.append(
                    MemoryEntry(
                        type=MemoryType.SEMANTIC,
                        content=content,
                        importance=importance,
                    )
                )

        return extracted

    def extract_entities(self, interaction: Interaction) -> list[dict]:
        """Extract named entities from an interaction using heuristics.

        Detection strategies:
          1. Known technology terms matched case-insensitively.
          2. Capitalised words that are NOT at the start of a sentence and
             NOT common stop-words — treated as proper nouns (person/place).

        Each entity dict contains:
          - name (str): the entity surface form
          - type (str): "technology", "person", "project", or "unknown"
          - relation (str | None): inferred verb relation to the user

        Returns:
            List of entity dicts.
        """
        combined = f"{interaction.user_input} {interaction.agent_output}"
        entities: dict[str, dict] = {}  # name_lower -> entity dict

        # --- 1. Known tech terms ---
        words = re.findall(r"[\w][\w\-]*", combined)
        for word in words:
            if word.lower() in KNOWN_TECH and word.lower() not in entities:
                # Preserve original casing from the text
                entities[word.lower()] = {
                    "name": word,
                    "type": "technology",
                    "relation": None,
                }

        # --- 2. Capitalised words not at sentence start ---
        # Split into sentences on . ! ? then inspect each word
        sentences = re.split(r"[.!?]+", combined)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            # Tokenize preserving hyphens
            tokens = re.findall(r"[\w][\w\-]*", sentence)
            # Skip the first token (sentence-start capitalisation is expected)
            for token in tokens[1:]:
                if (
                    token[0].isupper()
                    and token.lower() not in _STOP_WORDS
                    and token.lower() not in KNOWN_TECH
                    and token.lower() not in entities
                    and len(token) >= 2
                ):
                    entities[token.lower()] = {
                        "name": token,
                        "type": "person",  # default guess for proper nouns
                        "relation": None,
                    }

        # --- 3. Infer relationships from surrounding context ---
        for entity_info in entities.values():
            name = entity_info["name"]
            for rel_pattern, relation in ENTITY_RELATIONS:
                # Check if the relation pattern appears near the entity name
                # e.g. "I use Python" or "I'm building PocketPaw"
                context_pat = re.compile(
                    rel_pattern.pattern + r"\s+" + re.escape(name),
                    re.IGNORECASE,
                )
                if context_pat.search(combined):
                    entity_info["relation"] = relation
                    # Upgrade type if we have a "builds" relation
                    if relation == "builds":
                        entity_info["type"] = "project"
                    break

        return list(entities.values())

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
                for proc in self._procedural.entries()
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
            entry = MemoryEntry.model_validate(entry_data)
            manager._episodic._memories[entry.id] = entry

        # Restore semantic facts
        for fact_data in data.get("semantic", []):
            fact = MemoryEntry.model_validate(fact_data)
            manager._semantic._facts[fact.id] = fact

        # Restore procedural memories
        for proc_data in data.get("procedural", []):
            proc = MemoryEntry.model_validate(proc_data)
            manager._procedural._procedures[proc.id] = proc

        # Restore knowledge graph
        graph_data = data.get("graph", {})
        if graph_data:
            manager._graph = KnowledgeGraph.from_dict(graph_data)

        return manager
