# engine/__init__.py — The opinionated runtime that brings souls alive.
# Created: 2026-03-06 — Thin re-export namespace for the "alive souls" layer.
# This namespace re-exports from existing soul_protocol modules.
# Use `from soul_protocol.engine import AliveSoul` for the full-featured soul.
# Use `from soul_protocol.core import SoulContainer` for just the primitives.

from __future__ import annotations

from soul_protocol.cognitive.engine import CognitiveEngine, HeuristicEngine
from soul_protocol.dna.prompt import dna_to_system_prompt
from soul_protocol.evolution.manager import EvolutionManager
from soul_protocol.memory.manager import MemoryManager
from soul_protocol.soul import Soul
from soul_protocol.soul import Soul as AliveSoul
from soul_protocol.state.manager import StateManager

__all__ = [
    "AliveSoul",
    "Soul",
    "CognitiveEngine",
    "HeuristicEngine",
    "MemoryManager",
    "StateManager",
    "EvolutionManager",
    "dna_to_system_prompt",
]
