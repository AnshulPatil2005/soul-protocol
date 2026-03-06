# engine/memory/__init__.py — Re-exports for psychology-informed memory modules.
# Created: 2026-03-06 — Thin re-export layer for memory subsystem types.
#
# Note: SentimentDetector does not exist as a class; the sentiment module
# exposes detect_sentiment as a function, re-exported here as such.

from __future__ import annotations

from soul_protocol.memory.activation import spreading_activation
from soul_protocol.memory.attention import is_significant, overall_significance
from soul_protocol.memory.manager import MemoryManager
from soul_protocol.memory.search import relevance_score
from soul_protocol.memory.self_model import SelfModelManager
from soul_protocol.memory.sentiment import detect_sentiment
from soul_protocol.memory.strategy import SearchStrategy, TokenOverlapStrategy

__all__ = [
    "MemoryManager",
    "detect_sentiment",
    "SelfModelManager",
    "spreading_activation",
    "is_significant",
    "overall_significance",
    "relevance_score",
    "SearchStrategy",
    "TokenOverlapStrategy",
]
