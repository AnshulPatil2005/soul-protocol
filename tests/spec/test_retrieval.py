# test_retrieval.py — Spec-level tests for the retrieval vocabulary.
# Created: feat/0.3.2-prune-retrieval-infra (2026-04-19) — covers the types
# and Protocols that moved from engine/retrieval/ into spec/retrieval.py.
# The concrete orchestration (RetrievalRouter, InMemoryCredentialBroker,
# ProjectionAdapter) now lives in pocketpaw and is tested there; this file
# covers only the standard's contract.

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from soul_protocol.spec.journal import Actor
from soul_protocol.spec.retrieval import (
    AsyncSourceAdapter,
    Credential,
    DataRef,
    PointInTimeNotSupported,
    RetrievalCandidate,
    RetrievalRequest,
    SourceAdapter,
)

# --- Credential -----------------------------------------------------------


class TestCredentialValidation:
    def test_valid_credential_round_trip(self) -> None:
        now = datetime.now(UTC)
        cred = Credential(
            source="drive",
            scopes=["org:sales:*"],
            token="opaque-bearer",
            acquired_at=now,
            expires_at=now + timedelta(minutes=5),
        )
        assert cred.source == "drive"
        assert cred.scopes == ["org:sales:*"]
        assert cred.token == "opaque-bearer"
        assert cred.last_used_at is None
        assert isinstance(cred.id, type(uuid4()))

    def test_empty_scopes_rejected(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(ValidationError):
            Credential(
                source="drive",
                scopes=[],
                token="opaque-bearer",
                acquired_at=now,
                expires_at=now + timedelta(minutes=5),
            )

    def test_empty_source_rejected(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(ValidationError):
            Credential(
                source="",
                scopes=["org:sales"],
                token="opaque-bearer",
                acquired_at=now,
                expires_at=now + timedelta(minutes=5),
            )

    def test_empty_token_rejected(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(ValidationError):
            Credential(
                source="drive",
                scopes=["org:sales"],
                token="",
                acquired_at=now,
                expires_at=now + timedelta(minutes=5),
            )


class TestCredentialIsExpired:
    def _build(self, *, expires_at: datetime) -> Credential:
        return Credential(
            source="drive",
            scopes=["org:sales"],
            token="opaque-bearer",
            acquired_at=datetime.now(UTC) - timedelta(minutes=1),
            expires_at=expires_at,
        )

    def test_future_expiry_is_not_expired(self) -> None:
        cred = self._build(expires_at=datetime.now(UTC) + timedelta(minutes=5))
        assert cred.is_expired() is False

    def test_past_expiry_is_expired(self) -> None:
        cred = self._build(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        assert cred.is_expired() is True

    def test_now_override_controls_boundary(self) -> None:
        pinned = datetime(2026, 4, 19, 12, 0, 0, tzinfo=UTC)
        cred = self._build(expires_at=pinned)
        assert cred.is_expired(now=pinned - timedelta(seconds=1)) is False
        # At the boundary (now == expires_at) the credential is expired.
        assert cred.is_expired(now=pinned) is True
        assert cred.is_expired(now=pinned + timedelta(seconds=1)) is True


# --- Protocol conformance -------------------------------------------------


class _StubSyncAdapter:
    """Minimal object that should structurally match SourceAdapter."""

    supports_dataref: bool = False

    def query(
        self,
        request: RetrievalRequest,
        credential: Credential | None,
    ) -> list[RetrievalCandidate]:
        return []


class _StubAsyncAdapter:
    """Minimal object that should structurally match both Protocols."""

    supports_dataref: bool = True

    def query(
        self,
        request: RetrievalRequest,
        credential: Credential | None,
    ) -> list[RetrievalCandidate]:
        return []

    async def aquery(
        self,
        request: RetrievalRequest,
        credential: Credential | None,
    ) -> list[RetrievalCandidate]:
        return []


class TestProtocolConformance:
    def test_sync_adapter_matches_source_adapter(self) -> None:
        assert isinstance(_StubSyncAdapter(), SourceAdapter)

    def test_sync_adapter_does_not_match_async_protocol(self) -> None:
        assert not isinstance(_StubSyncAdapter(), AsyncSourceAdapter)

    def test_async_adapter_matches_both_protocols(self) -> None:
        stub = _StubAsyncAdapter()
        assert isinstance(stub, SourceAdapter)
        assert isinstance(stub, AsyncSourceAdapter)

    def test_plain_object_does_not_match(self) -> None:
        assert not isinstance(object(), SourceAdapter)
        assert not isinstance(object(), AsyncSourceAdapter)


# --- DataRef + promotion --------------------------------------------------


class TestDataRefPromotion:
    def test_dict_with_kind_promotes_to_dataref(self) -> None:
        cand = RetrievalCandidate(
            source="drive",
            content={"kind": "dataref", "source": "drive", "id": "file_1", "scopes": ["org:sales:*"]},
            as_of=datetime.now(UTC),
        )
        assert isinstance(cand.content, DataRef)
        assert cand.content.kind == "dataref"
        assert cand.content.source == "drive"
        assert cand.content.id == "file_1"

    def test_plain_dict_content_stays_dict(self) -> None:
        cand = RetrievalCandidate(
            source="soul_memory",
            content={"text": "hello", "score": 0.9},
            as_of=datetime.now(UTC),
        )
        assert isinstance(cand.content, dict)
        assert cand.content["text"] == "hello"


# --- RetrievalRequest.point_in_time ---------------------------------------


class TestRetrievalRequestPointInTime:
    def _actor(self) -> Actor:
        return Actor(kind="agent", id="did:soul:test", scope_context=["org:sales"])

    def test_utc_datetime_accepted(self) -> None:
        req = RetrievalRequest(
            query="Q3 forecast",
            actor=self._actor(),
            scopes=["org:sales"],
            point_in_time=datetime(2026, 4, 1, 12, 0, 0, tzinfo=UTC),
        )
        assert req.point_in_time == datetime(2026, 4, 1, 12, 0, 0, tzinfo=UTC)

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RetrievalRequest(
                query="Q3 forecast",
                actor=self._actor(),
                scopes=["org:sales"],
                point_in_time=datetime(2026, 4, 1, 12, 0, 0),  # no tzinfo
            )

    def test_none_accepted(self) -> None:
        req = RetrievalRequest(
            query="Q3 forecast",
            actor=self._actor(),
            scopes=["org:sales"],
        )
        assert req.point_in_time is None


def test_point_in_time_not_supported_is_an_exception() -> None:
    with pytest.raises(PointInTimeNotSupported):
        raise PointInTimeNotSupported("adapter cannot time-travel")
