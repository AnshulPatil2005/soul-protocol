# memory/__init__.py — Memory subsystem package for the Digital Soul Protocol.
# Updated: v0.2.0 — Added psychology modules: sentiment, activation, attention, self_model.
# Re-exports MemoryManager as the primary public interface, along with all
# memory store classes and new psychology modules for direct access.

from __future__ import annotations

from soul_protocol.memory.activation import compute_activation
from soul_protocol.memory.attention import compute_significance, is_significant
from soul_protocol.memory.core import CoreMemoryManager
from soul_protocol.memory.episodic import EpisodicStore
from soul_protocol.memory.graph import KnowledgeGraph
from soul_protocol.memory.manager import MemoryManager
from soul_protocol.memory.procedural import ProceduralStore
from soul_protocol.memory.recall import RecallEngine
from soul_protocol.memory.self_model import SelfModelManager
from soul_protocol.memory.semantic import SemanticStore
from soul_protocol.memory.sentiment import detect_sentiment

__all__ = [
    "MemoryManager",
    "CoreMemoryManager",
    "EpisodicStore",
    "SemanticStore",
    "ProceduralStore",
    "KnowledgeGraph",
    "RecallEngine",
    # v0.2.0 psychology modules
    "detect_sentiment",
    "compute_activation",
    "compute_significance",
    "is_significant",
    "SelfModelManager",
]
