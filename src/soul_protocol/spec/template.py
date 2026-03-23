# template.py — SoulTemplate spec model for creating souls from templates.
# Created: feat/memory-visibility-templates — Defines the SoulTemplate model
#   for batch spawning with personality variance and name patterns.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SoulTemplate(BaseModel):
    """Template for creating souls with shared traits.

    Templates define a blueprint for soul creation. Use with the runtime
    SoulFactory to spawn individual souls or batches with controlled
    personality variance.

    Attributes:
        name: Template name (used as default soul name if none provided).
        archetype: Personality archetype description.
        personality: OCEAN trait values (0.0-1.0). Missing traits default to 0.5.
        core_memories: List of core memory strings to initialize.
        skills: List of skill names to bootstrap.
        metadata: Open dict for runtime-specific template extensions.
        personality_variance: Max random deviation from template OCEAN traits
            when batch spawning. 0.0 = exact clones, 0.5 = maximum diversity.
        name_prefix: Prefix for auto-generated names in batch spawning.
            e.g., "Agent-" produces "Agent-001", "Agent-002", etc.
    """

    name: str
    archetype: str = "assistant"
    personality: dict[str, float] = Field(default_factory=dict)
    core_memories: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Variation settings for batch spawning
    personality_variance: float = Field(default=0.1, ge=0.0, le=0.5)
    name_prefix: str = ""
