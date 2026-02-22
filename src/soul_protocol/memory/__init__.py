# memory/__init__.py — Memory subsystem package for the Digital Soul Protocol.
# Created: 2026-02-22
# Re-exports MemoryManager as the primary public interface, along with all
# memory store classes for direct access when needed.

from __future__ import annotations

from soul_protocol.memory.core import CoreMemoryManager
from soul_protocol.memory.episodic import EpisodicStore
from soul_protocol.memory.graph import KnowledgeGraph
from soul_protocol.memory.manager import MemoryManager
from soul_protocol.memory.procedural import ProceduralStore
from soul_protocol.memory.recall import RecallEngine
from soul_protocol.memory.semantic import SemanticStore

__all__ = [
    "MemoryManager",
    "CoreMemoryManager",
    "EpisodicStore",
    "SemanticStore",
    "ProceduralStore",
    "KnowledgeGraph",
    "RecallEngine",
]
