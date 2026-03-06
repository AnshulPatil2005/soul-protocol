# core/__init__.py — Public exports for the core primitives layer.
# Created: v0.4.0 — The "HTTP layer" of soul-protocol: minimal, unopinionated
# primitives that any runtime can implement. Zero imports from opinionated
# modules (memory/, cognitive/, evolution/, state/, dna/).

from __future__ import annotations

from .container import SoulContainer
from .identity import Identity
from .manifest import Manifest
from .memory import DictMemoryStore, MemoryEntry, MemoryStore
from .soul_file import pack_soul, unpack_soul, unpack_to_container

__all__ = [
    # Container
    "SoulContainer",
    # Identity
    "Identity",
    # Memory
    "MemoryEntry",
    "MemoryStore",
    "DictMemoryStore",
    # Soul file format
    "pack_soul",
    "unpack_soul",
    "unpack_to_container",
    # Manifest
    "Manifest",
]
