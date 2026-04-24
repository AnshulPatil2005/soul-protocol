# backend.py — Journal backend Protocol.
# Updated: feat/0.3.2-spike — added action_prefix kwarg to query() for
# namespace-prefix matching (primitive #2 of 0.3.2). Mutually exclusive with
# action=. Pushes the action-family filter into SQL so projections don't
# have to pull all events and loop in Python.

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from soul_protocol.spec.journal import Actor, EventEntry


@runtime_checkable
class JournalBackend(Protocol):
    """Storage contract for journal events. All methods are synchronous."""

    def append(self, entry: EventEntry) -> int:
        """Persist `entry`, assigning and returning its monotonic seq atomically."""

    def query(
        self,
        *,
        action: str | None = None,
        action_prefix: str | None = None,
        actor: Actor | None = None,
        scope: list[str] | None = None,
        correlation_id: UUID | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventEntry]:
        """Return events matching the conjunction of filters.

        ``action`` and ``action_prefix`` are mutually exclusive. ``action_prefix``
        matches the exact string or anything starting with the prefix followed
        by a ``.``. See :meth:`Journal.query` for semantics.
        """

    def replay_from(self, seq: int = 0) -> Iterator[EventEntry]:
        """Yield events with seq >= given value in ascending seq order."""

    def last_entry(self) -> tuple[EventEntry, int] | None:
        """Return (last_entry, last_seq) or None if journal is empty."""

    def close(self) -> None:
        """Release any resources. Idempotent."""
