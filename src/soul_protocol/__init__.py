# __init__.py — Public API for the soul-protocol package
# Updated: v0.2.0 — Added psychology types (SomaticMarker, SignificanceScore,
#   GeneralEvent, SelfImage) to public exports.

from __future__ import annotations

from .soul import Soul
from .types import (
    Biorhythms,
    CommunicationStyle,
    CoreMemory,
    DNA,
    EvolutionConfig,
    EvolutionMode,
    GeneralEvent,
    Identity,
    Interaction,
    LifecycleState,
    MemoryEntry,
    MemorySettings,
    MemoryType,
    Mood,
    Mutation,
    Personality,
    SelfImage,
    SignificanceScore,
    SomaticMarker,
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
    "GeneralEvent",
    "Identity",
    "Interaction",
    "LifecycleState",
    "MemoryEntry",
    "MemorySettings",
    "MemoryType",
    "Mood",
    "Mutation",
    "Personality",
    "SelfImage",
    "SignificanceScore",
    "SomaticMarker",
    "SoulConfig",
    "SoulManifest",
    "SoulState",
]

__version__ = "0.2.0"
