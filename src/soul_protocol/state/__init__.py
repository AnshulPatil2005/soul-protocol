# state/__init__.py — Re-exports for the state management subpackage.
# Created: 2026-02-22 — Exposes StateManager as the primary public interface.

from __future__ import annotations

from soul_protocol.state.manager import StateManager

__all__ = ["StateManager"]
