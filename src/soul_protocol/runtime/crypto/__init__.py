# crypto/__init__.py — Re-exports for the crypto subpackage.
# Updated: runtime restructure — fixed absolute import paths to soul_protocol.runtime.
# Created: 2026-02-22 — Exposes symmetric encryption helpers for soul file protection.

from __future__ import annotations

from soul_protocol.runtime.crypto.encrypt import decrypt_data, derive_key, encrypt_data

__all__ = ["derive_key", "encrypt_data", "decrypt_data"]
