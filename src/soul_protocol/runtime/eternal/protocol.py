# eternal/protocol.py — Re-exports from spec for convenience.
# Updated: v0.4.0 — Canonical definitions moved to spec/eternal/protocol.py.
# Updated: runtime restructure — import path changed from core → spec.
# This module re-exports them so existing imports continue to work.

from soul_protocol.spec.eternal.protocol import (
    ArchiveResult,
    EternalStorageProvider,
    RecoverySource,
)

__all__ = ["EternalStorageProvider", "ArchiveResult", "RecoverySource"]
