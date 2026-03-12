# storage/__init__.py — Re-exports for the storage subpackage.
# Updated: runtime restructure — fixed absolute import paths to soul_protocol.runtime.
# Updated: 2026-02-22 — Added save_soul_full, load_soul_full for full memory persistence.

from __future__ import annotations

from soul_protocol.runtime.storage.file import (
    FileStorage,
    load_soul,
    load_soul_full,
    save_soul,
    save_soul_full,
)
from soul_protocol.runtime.storage.memory_store import InMemoryStorage
from soul_protocol.runtime.storage.protocol import StorageProtocol

__all__ = [
    "StorageProtocol",
    "FileStorage",
    "InMemoryStorage",
    "save_soul",
    "load_soul",
    "save_soul_full",
    "load_soul_full",
]
