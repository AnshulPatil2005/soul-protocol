# evolution/__init__.py — Re-exports for the evolution subpackage.
# Created: 2026-02-22 — Exposes EvolutionManager as the primary public interface.

from __future__ import annotations

from soul_protocol.evolution.manager import EvolutionManager

__all__ = ["EvolutionManager"]
