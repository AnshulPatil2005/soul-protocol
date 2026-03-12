# spec/eternal/__init__.py — Protocol-level eternal storage interfaces.
# Created: v0.4.0 — EternalStorageProvider protocol and result models.
# These define the storage tier interface — implementations live in engine.

from .protocol import ArchiveResult, EternalStorageProvider, RecoverySource

__all__ = [
    "EternalStorageProvider",
    "ArchiveResult",
    "RecoverySource",
]
