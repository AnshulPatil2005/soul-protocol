# identity/__init__.py — Re-exports for the identity subpackage
# Updated: runtime restructure — fixed absolute import paths to soul_protocol.runtime.
# Created: 2026-02-22 — Initial identity module setup

from __future__ import annotations

from soul_protocol.runtime.identity.did import generate_did

__all__ = ["generate_did"]
