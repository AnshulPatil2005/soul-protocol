# evolution/__init__.py — Re-exports for the evolution subpackage.
# Updated: runtime restructure — fixed absolute import paths to soul_protocol.runtime.
# Created: 2026-02-22 — Exposes EvolutionManager as the primary public interface.

from __future__ import annotations

from soul_protocol.runtime.evolution.manager import EvolutionManager

__all__ = ["EvolutionManager"]
