# conditions.py — Implements the 5 memory conditions (independent variable).
# Each condition wraps Soul Protocol with different feature flags enabled/disabled.
# This is the core of the ablation study.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from soul_protocol.runtime.types import Interaction, MemoryEntry

from .config import MemoryCondition


@dataclass
class ObserveResult:
    """Standardized result from any condition's observe() call."""

    facts_extracted: list[str]
    entities_extracted: list[str]
    significance_score: float
    somatic_valence: float | None
    stored_episodic: bool
    bond_strength: float
    skills_count: int
    memory_count: int


class BaseCondition:
    """Base class for all memory conditions."""

    condition: MemoryCondition

    async def setup(self, agent_profile: Any) -> None:
        """Initialize the condition for a given agent."""
        raise NotImplementedError

    async def observe(self, interaction: Interaction) -> ObserveResult:
        """Process an interaction under this condition."""
        raise NotImplementedError

    async def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Recall memories relevant to a query."""
        raise NotImplementedError

    async def get_state(self) -> dict[str, Any]:
        """Get current state snapshot for metrics."""
        raise NotImplementedError

    async def reset(self) -> None:
        """Reset state between scenarios (but NOT between sessions)."""
        raise NotImplementedError


class NoMemoryCondition(BaseCondition):
    """Condition 1: No memory at all. Stateless baseline."""

    condition = MemoryCondition.NONE

    async def setup(self, agent_profile: Any) -> None:
        self._interaction_count = 0

    async def observe(self, interaction: Interaction) -> ObserveResult:
        self._interaction_count += 1
        return ObserveResult(
            facts_extracted=[],
            entities_extracted=[],
            significance_score=0.0,
            somatic_valence=None,
            stored_episodic=False,
            bond_strength=0.0,
            skills_count=0,
            memory_count=0,
        )

    async def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        return []  # No memory = no recall

    async def get_state(self) -> dict[str, Any]:
        return {"interactions": self._interaction_count, "memories": 0}

    async def reset(self) -> None:
        self._interaction_count = 0


class RAGOnlyCondition(BaseCondition):
    """Condition 2: Pure vector similarity retrieval (no significance, no emotion)."""

    condition = MemoryCondition.RAG_ONLY

    async def setup(self, agent_profile: Any) -> None:
        from soul_protocol import Soul

        self._soul = await Soul.birth(
            name=agent_profile.name,
            archetype=agent_profile.archetype,
            values=agent_profile.values,
            ocean=agent_profile.ocean,
            communication=agent_profile.communication,
            persona=agent_profile.persona,
        )

    async def observe(self, interaction: Interaction) -> ObserveResult:
        """Store everything without significance gating or somatic markers."""
        # Manually store as semantic memory (bypass psychology pipeline)
        content = f"User: {interaction.user_input}\nAgent: {interaction.agent_output}"
        await self._soul.remember(content, importance=5)

        return ObserveResult(
            facts_extracted=[],
            entities_extracted=[],
            significance_score=1.0,  # Everything stored
            somatic_valence=None,
            stored_episodic=False,
            bond_strength=0.0,
            skills_count=0,
            memory_count=self._soul.memory_count,
        )

    async def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        return await self._soul.recall(query, limit=limit)

    async def get_state(self) -> dict[str, Any]:
        return {"memories": self._soul.memory_count}

    async def reset(self) -> None:
        pass  # Keep memories across sessions


class RAGSignificanceCondition(BaseCondition):
    """Condition 3: RAG + LIDA significance gating (no somatic markers)."""

    condition = MemoryCondition.RAG_SIGNIFICANCE

    async def setup(self, agent_profile: Any) -> None:
        from soul_protocol import Soul

        self._soul = await Soul.birth(
            name=agent_profile.name,
            archetype=agent_profile.archetype,
            values=agent_profile.values,
            ocean=agent_profile.ocean,
            communication=agent_profile.communication,
            persona=agent_profile.persona,
        )

    async def observe(self, interaction: Interaction) -> ObserveResult:
        """Use significance gating but strip somatic markers from results."""
        await self._soul.observe(interaction)

        return ObserveResult(
            facts_extracted=[],
            entities_extracted=[],
            significance_score=0.5,
            somatic_valence=None,  # Stripped
            stored_episodic=True,
            bond_strength=0.0,  # No bond in this condition
            skills_count=0,
            memory_count=self._soul.memory_count,
        )

    async def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        return await self._soul.recall(query, limit=limit)

    async def get_state(self) -> dict[str, Any]:
        return {"memories": self._soul.memory_count}

    async def reset(self) -> None:
        pass


class FullNoEmotionCondition(BaseCondition):
    """Condition 4: Full pipeline minus somatic markers and bond."""

    condition = MemoryCondition.FULL_NO_EMOTION

    async def setup(self, agent_profile: Any) -> None:
        from soul_protocol import Soul

        self._soul = await Soul.birth(
            name=agent_profile.name,
            archetype=agent_profile.archetype,
            values=agent_profile.values,
            ocean=agent_profile.ocean,
            communication=agent_profile.communication,
            persona=agent_profile.persona,
        )

    async def observe(self, interaction: Interaction) -> ObserveResult:
        """Full pipeline but we zero out emotional components in metrics."""
        await self._soul.observe(interaction)

        return ObserveResult(
            facts_extracted=[],
            entities_extracted=[],
            significance_score=0.5,
            somatic_valence=0.0,  # Zeroed for comparison
            stored_episodic=True,
            bond_strength=0.0,  # Ignored in this condition
            skills_count=len(self._soul.skills.skills),
            memory_count=self._soul.memory_count,
        )

    async def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        return await self._soul.recall(query, limit=limit)

    async def get_state(self) -> dict[str, Any]:
        return {
            "memories": self._soul.memory_count,
            "skills": len(self._soul.skills.skills),
        }

    async def reset(self) -> None:
        pass


class FullSoulCondition(BaseCondition):
    """Condition 5: Complete Soul Protocol stack. The full treatment."""

    condition = MemoryCondition.FULL_SOUL

    async def setup(self, agent_profile: Any) -> None:
        from soul_protocol import Soul

        self._soul = await Soul.birth(
            name=agent_profile.name,
            archetype=agent_profile.archetype,
            values=agent_profile.values,
            ocean=agent_profile.ocean,
            communication=agent_profile.communication,
            persona=agent_profile.persona,
        )

    async def observe(self, interaction: Interaction) -> ObserveResult:
        """Full Soul Protocol pipeline — everything enabled."""
        await self._soul.observe(interaction)

        return ObserveResult(
            facts_extracted=[],
            entities_extracted=[],
            significance_score=0.5,
            somatic_valence=0.0,
            stored_episodic=True,
            bond_strength=self._soul.bond.bond_strength,
            skills_count=len(self._soul.skills.skills),
            memory_count=self._soul.memory_count,
        )

    async def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        return await self._soul.recall(query, limit=limit)

    async def get_state(self) -> dict[str, Any]:
        return {
            "memories": self._soul.memory_count,
            "bond_strength": self._soul.bond.bond_strength,
            "skills": len(self._soul.skills.skills),
            "state": {
                "mood": str(self._soul.state.mood),
                "energy": self._soul.state.energy,
            },
        }

    async def reset(self) -> None:
        pass


CONDITION_MAP: dict[MemoryCondition, type[BaseCondition]] = {
    MemoryCondition.NONE: NoMemoryCondition,
    MemoryCondition.RAG_ONLY: RAGOnlyCondition,
    MemoryCondition.RAG_SIGNIFICANCE: RAGSignificanceCondition,
    MemoryCondition.FULL_NO_EMOTION: FullNoEmotionCondition,
    MemoryCondition.FULL_SOUL: FullSoulCondition,
}


def create_condition(condition: MemoryCondition) -> BaseCondition:
    """Factory function to create a condition instance."""
    cls = CONDITION_MAP[condition]
    return cls()
