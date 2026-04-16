# test_0_3_2_primitives.py — E2E + smoke + real-world sim tests for 0.3.2 primitives.
# Created: feat/0.3.2-spike — tests each 0.3.2 primitive across 4 layers:
# unit (in test_journal.py), e2e (full lifecycle), smoke (basic sanity),
# real-world sim (realistic consumer pattern from pocketpaw Wave 3).
#
# Primitives covered in this file:
#   #1 Journal.append returns committed EventEntry
#   #2 Journal.query(action_prefix=...)  — TODO next slice
#   #3 Async SourceAdapter.aquery        — TODO next slice
#   #4 DataRef Pydantic discrimination   — TODO next slice
#   #5 RetrievalRequest.point_in_time    — TODO next slice

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from soul_protocol.engine.journal import Journal, open_journal
from soul_protocol.spec.journal import Actor, EventEntry


def _entry(action: str, payload: dict | None = None) -> EventEntry:
    return EventEntry(
        id=uuid4(),
        ts=datetime.now(UTC),
        actor=Actor(kind="agent", id="did:soul:test"),
        action=action,
        scope=["org:test"],
        payload=payload or {},
    )


@pytest.fixture
def journal(tmp_path: Path) -> Journal:
    j = open_journal(tmp_path / "journal.db")
    yield j
    j.close()


# ---------- primitive #1: smoke tests ---------------------------------


def test_smoke_append_returns_entry(journal: Journal) -> None:
    """Smoke: happy path — append returns committed entry with seq."""
    committed = journal.append(_entry("memory.remembered"))
    assert committed is not None
    assert committed.seq is not None


def test_smoke_append_none_caller_still_works(journal: Journal) -> None:
    """Smoke: backward compat — caller that discards return sees no error."""
    journal.append(_entry("memory.remembered"))
    assert len(journal.query()) == 1


# ---------- primitive #1: e2e tests -----------------------------------


def test_e2e_seq_drives_client_sync(journal: Journal) -> None:
    """E2E: a consumer writes events and uses seq to bookmark 'seen' position.

    Mirrors the widget store pattern in pocketpaw (ee/widget/store.py) that
    reached into backend.append() pre-0.3.2. With the committed entry returned,
    callers can ack-with-seq cleanly.
    """
    last_seen = -1

    # Write a batch and track the highest seq we've committed.
    for i in range(10):
        committed = journal.append(_entry("widget.interaction.recorded", {"i": i}))
        assert committed.seq > last_seen
        last_seen = committed.seq

    # Resume: a client bookmarked 'last_seen'. Query for anything newer.
    all_events = journal.query(limit=100)
    assert len(all_events) == 10
    assert last_seen == 9  # 10 events, gap-free, starting at 0


def test_e2e_seq_survives_reopen(tmp_path: Path) -> None:
    """E2E: seq is persisted — closing and reopening the journal doesn't reset."""
    path = tmp_path / "journal.db"

    j = open_journal(path)
    first = j.append(_entry("memory.remembered"))
    j.close()

    j = open_journal(path)
    second = j.append(_entry("memory.remembered"))
    j.close()

    assert second.seq > first.seq


# ---------- primitive #1: real-world sim (pocketpaw widget store pattern) ----


def test_realworld_widget_store_ack_with_seq(journal: Journal) -> None:
    """Real-world sim: replays the pocketpaw widget store's client-sync pattern.

    Pre-0.3.2: ee/widget/store.py had to reach into backend.append() and
    replicate Journal's hash-link logic to get seq for its ack response.
    Post-0.3.2: it can just read seq off the returned EventEntry.

    This test proves the primitive #1 API is sufficient for that consumer.
    """

    def log_widget_interaction(payload: dict) -> dict:
        """Simulated pocketpaw widget store helper using the new API."""
        committed = journal.append(_entry("widget.interaction.recorded", payload))
        return {
            "seq": committed.seq,
            "event_id": str(committed.id),
            "ts": committed.ts.isoformat(),
        }

    acks = [log_widget_interaction({"click": n}) for n in range(50)]

    # Client uses seqs to detect gaps / order events.
    seqs = [a["seq"] for a in acks]
    assert seqs == sorted(seqs)
    assert len(set(seqs)) == 50  # no duplicates
    assert seqs[0] == 0
    assert seqs[-1] == 49  # gap-free


def test_realworld_correlated_flow_uses_seq_for_ordering(journal: Journal) -> None:
    """Real-world sim: correlated events in a flow ordered by seq, not ts.

    Why seq and not ts: ts can tie at sub-microsecond resolution under fast
    writers. Seq is the tiebreaker that gives deterministic flow order.
    """
    corr = uuid4()

    flow_events = []
    for step in ("retrieval.query", "memory.remembered", "memory.graduated"):
        e = EventEntry(
            id=uuid4(),
            ts=datetime.now(UTC),
            actor=Actor(kind="agent", id="did:soul:test"),
            action=step,
            scope=["org:test"],
            correlation_id=corr,
            payload={"step": step},
        )
        flow_events.append(journal.append(e))

    # Order the flow by seq — stable regardless of ts resolution.
    ordered = sorted(flow_events, key=lambda e: e.seq)
    assert [e.action for e in ordered] == [
        "retrieval.query",
        "memory.remembered",
        "memory.graduated",
    ]
