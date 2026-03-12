# state/__init__.py — Re-exports for the state management subpackage.
# Updated: runtime restructure — fixed absolute import paths to soul_protocol.runtime.
# Created: 2026-02-22 — Exposes StateManager as the primary public interface.

from __future__ import annotations

from soul_protocol.runtime.state.manager import StateManager

__all__ = ["StateManager"]
