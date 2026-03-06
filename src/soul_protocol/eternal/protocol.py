# eternal/protocol.py — Re-exports from core for convenience.
# Updated: v0.4.0 — Canonical definitions moved to core/eternal/protocol.py.
# This module re-exports them so existing imports continue to work.

from soul_protocol.core.eternal.protocol import (
    ArchiveResult,
    EternalStorageProvider,
    RecoverySource,
)

__all__ = ["EternalStorageProvider", "ArchiveResult", "RecoverySource"]
