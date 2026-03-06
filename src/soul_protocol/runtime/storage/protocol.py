# storage/protocol.py — StorageProtocol defining the interface all storage backends must satisfy.
# Updated: runtime restructure — fixed absolute import paths to soul_protocol.runtime.
# Created: 2026-02-22 — Runtime-checkable Protocol for save/load/delete/list_souls.

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from soul_protocol.runtime.types import SoulConfig


@runtime_checkable
class StorageProtocol(Protocol):
    """Interface that all soul storage backends must implement.

    Backends are responsible for persisting and retrieving ``SoulConfig``
    instances identified by ``soul_id``.
    """

    async def save(self, soul_id: str, config: SoulConfig, path: Path | None = None) -> None:
        """Persist a soul configuration."""
        ...

    async def load(self, soul_id: str, path: Path | None = None) -> SoulConfig | None:
        """Load a soul configuration, returning ``None`` if not found."""
        ...

    async def delete(self, soul_id: str) -> bool:
        """Delete a soul. Returns ``True`` if it existed."""
        ...

    async def list_souls(self) -> list[str]:
        """Return a list of all stored soul IDs."""
        ...
