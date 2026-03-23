# spec/__init__.py — Public exports for the spec primitives layer.
# Created: v0.4.0 — The "HTTP layer" of soul-protocol: minimal, unopinionated
# primitives that any runtime can implement. Zero imports from opinionated
# modules (memory/, cognitive/, evolution/, state/, dna/).
# Updated: Added EternalStorageProvider, EmbeddingProvider, similarity functions.
# Updated: Added ContextEngine protocol and LCM models for Lossless Context Management.

from __future__ import annotations

from .container import SoulContainer
from .context import (
    AssembleResult,
    CompactionLevel,
    ContextEngine,
    ContextMessage,
    ContextNode,
    DescribeResult,
    ExpandResult,
    GrepResult,
)
from .embeddings import (
    EmbeddingProvider,
    cosine_similarity,
    dot_product,
    euclidean_distance,
)
from .eternal import ArchiveResult, EternalStorageProvider, RecoverySource
from .identity import BondTarget, Identity
from .manifest import Manifest
from .memory import DictMemoryStore, Interaction, MemoryEntry, MemoryStore, MemoryVisibility, Participant
from .template import SoulTemplate
from .learning import LearningEvent
from .soul_file import pack_soul, unpack_soul, unpack_to_container

__all__ = [
    # Container
    "SoulContainer",
    # Context (LCM)
    "AssembleResult",
    "CompactionLevel",
    "ContextEngine",
    "ContextMessage",
    "ContextNode",
    "DescribeResult",
    "ExpandResult",
    "GrepResult",
    # Identity
    "BondTarget",
    "Identity",
    # Memory
    "Interaction",
    "MemoryEntry",
    "Participant",
    "MemoryStore",
    "MemoryVisibility",
    "DictMemoryStore",
    # Learning
    "LearningEvent",
    "SoulTemplate",
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
