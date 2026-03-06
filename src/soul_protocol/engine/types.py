# engine/types.py — Re-exports for engine-specific types (psychology, evolution, etc).
# Created: 2026-03-06 — Thin re-export layer for types used by the engine namespace.

from __future__ import annotations

from soul_protocol.types import (
    CoreMemory,
    EvolutionConfig,
    EvolutionMode,
    GeneralEvent,
    Interaction,
    MemorySettings,
    MemoryType,
    Mutation,
    ReflectionResult,
    SelfImage,
    SignificanceScore,
    SomaticMarker,
)

__all__ = [
    "SomaticMarker",
    "SignificanceScore",
    "GeneralEvent",
    "SelfImage",
    "EvolutionConfig",
    "EvolutionMode",
    "Mutation",
    "ReflectionResult",
    "Interaction",
    "MemoryType",
    "MemorySettings",
    "CoreMemory",
]
