# identity/__init__.py — Re-exports for the identity subpackage
# Created: 2026-02-22 — Initial identity module setup

from __future__ import annotations

from soul_protocol.identity.did import generate_did

__all__ = ["generate_did"]
