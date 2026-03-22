# spec/__init__.py — Public exports for the spec primitives layer.
# Created: v0.4.0 — The "HTTP layer" of soul-protocol: minimal, unopinionated
# primitives that any runtime can implement. Zero imports from opinionated
# modules (memory/, cognitive/, evolution/, state/, dna/).
# Updated: Added EternalStorageProvider, EmbeddingProvider, similarity functions.

from __future__ import annotations

from .container import SoulContainer
from .embeddings import (
    EmbeddingProvider,
    cosine_similarity,
    dot_product,
    euclidean_distance,
)
from .eternal import ArchiveResult, EternalStorageProvider, RecoverySource
from .identity import Identity
from .manifest import Manifest
from .memory import DictMemoryStore, MemoryEntry, MemoryStore
from .learning import LearningEvent
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
    # Learning
    "LearningEvent",
    # Soul file format
    "pack_soul",
    "unpack_soul",
    "unpack_to_container",
    # Manifest
    "Manifest",
    # Eternal storage protocol
    "ArchiveResult",
    "EternalStorageProvider",
    "RecoverySource",
    # Embedding protocol
    "EmbeddingProvider",
    "cosine_similarity",
    "euclidean_distance",
    "dot_product",
]
