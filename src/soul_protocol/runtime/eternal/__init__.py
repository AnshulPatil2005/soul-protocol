# eternal/__init__.py — Public API for the eternal storage subsystem.
# Created: 2026-03-06 — Exports protocol, models, manager, and mock providers.

from __future__ import annotations

from .protocol import ArchiveResult, EternalStorageProvider, RecoverySource
from .manager import EternalStorageManager

__all__ = [
    "ArchiveResult",
    "EternalStorageProvider",
    "EternalStorageManager",
    "RecoverySource",
]
