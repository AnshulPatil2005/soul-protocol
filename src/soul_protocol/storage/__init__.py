# storage/__init__.py — Re-exports for the storage subpackage.
# Created: 2026-02-22 — Exposes StorageProtocol and both backend implementations.

from __future__ import annotations

from soul_protocol.storage.file import FileStorage, save_soul, load_soul
from soul_protocol.storage.memory_store import InMemoryStorage
from soul_protocol.storage.protocol import StorageProtocol

__all__ = [
    "StorageProtocol",
    "FileStorage",
    "InMemoryStorage",
    "save_soul",
    "load_soul",
]
