# __init__.py — Public API for the soul-protocol package
# Created: 2026-02-22 — Exports Soul class and core types

from __future__ import annotations

from .soul import Soul
from .types import (
    Biorhythms,
    CommunicationStyle,
    CoreMemory,
    DNA,
    EvolutionConfig,
    EvolutionMode,
    Identity,
    Interaction,
    LifecycleState,
    MemoryEntry,
    MemorySettings,
    MemoryType,
    Mood,
    Mutation,
    Personality,
    SoulConfig,
    SoulManifest,
    SoulState,
)

__all__ = [
    "Soul",
    "Biorhythms",
    "CommunicationStyle",
    "CoreMemory",
    "DNA",
    "EvolutionConfig",
    "EvolutionMode",
    "Identity",
    "Interaction",
    "LifecycleState",
    "MemoryEntry",
    "MemorySettings",
    "MemoryType",
    "Mood",
    "Mutation",
    "Personality",
    "SoulConfig",
    "SoulManifest",
    "SoulState",
]

__version__ = "0.1.0"
