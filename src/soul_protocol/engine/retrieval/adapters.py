# adapters.py — SourceAdapter Protocol + two reference implementations.
# Updated: feat/0.3.2-spike — added optional async ``aquery`` method to the
# Protocol. Adapters backed by async-native SDKs (most modern Salesforce,
# Slack, Gmail clients) can implement it directly instead of bridging
# through asyncio.run(). The router's new ``adispatch`` prefers ``aquery``
# when present and falls back to thread-pooling the sync ``query`` otherwise.
# (Primitive #5 of 5 additive gaps.)
#
# Two concrete adapters live here:
#   * `MockAdapter` — returns fixed candidates and tracks invocations. Pure
#     test fixture; not exported from the retrieval __init__.
#   * `ProjectionAdapter` — wraps a callable so soul memory, kb, and fabric
#     can plug in without each building a class. Represents the
#     "local rebuilt view" case.
#
# The concrete external-federation adapters (Drive, Salesforce, ...) are C2.

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from soul_protocol.spec.retrieval import RetrievalCandidate, RetrievalRequest

from .broker import Credential


@runtime_checkable
class SourceAdapter(Protocol):
    """Protocol implemented by every retrieval source adapter.

    An adapter is registered under a `CandidateSource`. `query` receives
    the full request (so it can read `query`, `limit`, `scopes`) plus an
    optional credential — projection adapters ignore the credential,
    DataRef adapters require it.

    The `supports_dataref` class attribute advertises whether this adapter
    can produce Zero-Copy candidates whose content is a DataRef payload.

    **Optional async companion** (added in 0.3.2): adapters backed by
    async-native SDKs can additionally implement an ``aquery`` coroutine
    with the same signature. The router's ``adispatch`` uses ``aquery``
    when it's present (detected via ``inspect.iscoroutinefunction``) and
    threads ``query`` otherwise. ``aquery`` is **not** part of the
    Protocol signature because ``runtime_checkable`` would then require
    every sync-only adapter to stub it — the detection at dispatch time
    keeps both paths clean. See :class:`AsyncSourceAdapter` below for a
    pure structural tag when you want ``isinstance(adapter,
    AsyncSourceAdapter)``.
    """

    supports_dataref: bool

    def query(
        self,
        request: RetrievalRequest,
        credential: Credential | None,
    ) -> list[RetrievalCandidate]: ...


@runtime_checkable
class AsyncSourceAdapter(Protocol):
    """Structural tag for adapters that also implement async ``aquery``.

    ``isinstance(adapter, AsyncSourceAdapter)`` is true iff the adapter
    has both ``query`` and an async ``aquery``. Added in 0.3.2 —
    consumers that want to route differently based on async support
    can use this as a clean predicate instead of poking at attributes.
    """

    def query(
        self,
        request: RetrievalRequest,
        credential: Credential | None,
    ) -> list[RetrievalCandidate]: ...

    async def aquery(
        self,
        request: RetrievalRequest,
        credential: Credential | None,
    ) -> list[RetrievalCandidate]: ...


class MockAdapter:
    """Test adapter. Returns a fixed list, records every call.

    Parameters:
        candidates: What to return on `query`.
        delay_s: If >0, sleeps that long before returning. Lets tests
            exercise the router's per-source timeout path.
        raises: If set, raises this exception instead of returning.
    """

    supports_dataref: bool = False

    def __init__(
        self,
        candidates: list[RetrievalCandidate] | None = None,
        *,
        delay_s: float = 0.0,
        raises: Exception | None = None,
    ) -> None:
        self._candidates = candidates or []
        self._delay_s = delay_s
        self._raises = raises
        self.calls: list[tuple[RetrievalRequest, Credential | None]] = []

    def query(
        self,
        request: RetrievalRequest,
        credential: Credential | None,
    ) -> list[RetrievalCandidate]:
        self.calls.append((request, credential))
        if self._delay_s > 0:
            import time

            time.sleep(self._delay_s)
        if self._raises is not None:
            raise self._raises
        return list(self._candidates)


class ProjectionAdapter:
    """Adapter over a plain callable — the "local rebuilt view" shape.

    Soul memory, kb, and fabric all live inside the same Paw OS instance
    the router runs in. They don't need federation or credentials. A
    callable that takes the request and returns candidates is enough.
    """

    supports_dataref: bool = False

    def __init__(
        self,
        fn: Callable[[RetrievalRequest], list[RetrievalCandidate]],
    ) -> None:
        self._fn = fn

    def query(
        self,
        request: RetrievalRequest,
        credential: Credential | None,  # noqa: ARG002 — projection ignores creds
    ) -> list[RetrievalCandidate]:
        return list(self._fn(request))
