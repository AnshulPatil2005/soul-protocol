# __init__.py — Public API for the soul-protocol package
# Created: 2026-02-22 — Exports Soul class and core types
# Updated: 2026-03-06 — Added EternalLinks, EternalStorageManager,
#   EternalStorageProvider, ArchiveResult, RecoverySource exports.

from __future__ import annotations

from .soul import Soul
from .types import (
    Biorhythms,
    CommunicationStyle,
    CoreMemory,
    DNA,
    EternalLinks,
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
from .eternal import ArchiveResult, EternalStorageManager, EternalStorageProvider, RecoverySource

__all__ = [
    "Soul",
    "ArchiveResult",
    "Biorhythms",
    "CommunicationStyle",
    "CoreMemory",
    "DNA",
    "EternalLinks",
    "EternalStorageManager",
    "EternalStorageProvider",
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
    "RecoverySource",
    "SoulConfig",
    "SoulManifest",
    "SoulState",
]

__version__ = "0.1.0"
