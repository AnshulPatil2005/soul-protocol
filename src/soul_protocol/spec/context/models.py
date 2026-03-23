# spec/context/models.py — Pydantic models for Lossless Context Management.
# Created: v0.3.0 — CompactionLevel, ContextMessage, ContextNode, AssembleResult,
# GrepResult, ExpandResult, DescribeResult. These are spec-layer primitives:
# minimal, unopinionated, zero runtime imports.

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class CompactionLevel(StrEnum):
    """How aggressively a context node has been compressed.

    Ordered from least to most lossy:
    - VERBATIM: original message, no compression
    - SUMMARY: LLM-generated prose summary of a batch
    - BULLETS: LLM-generated bullet-point summary (more compact)
    - TRUNCATED: deterministic head-truncation (guaranteed convergence, no LLM)
    """

    VERBATIM = "verbatim"
    SUMMARY = "summary"
    BULLETS = "bullets"
    TRUNCATED = "truncated"


class ContextMessage(BaseModel):
    """A single message in the conversation — the atomic unit of context.

    Messages are immutable once ingested. The store NEVER updates or deletes them.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    role: str
    content: str
    token_count: int = 0
    seq: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextNode(BaseModel):
    """A DAG node representing a compacted view of one or more messages.

    Nodes form a directed acyclic graph: a SUMMARY node points to the
    VERBATIM messages it summarizes. A BULLETS node may point to SUMMARY
    nodes it further compressed. This enables expand() to walk back to
    the original messages.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    level: CompactionLevel = CompactionLevel.VERBATIM
    content: str = ""
    token_count: int = 0
    children_ids: list[str] = Field(default_factory=list)
    seq_start: int = 0
    seq_end: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class AssembleResult(BaseModel):
    """Result of assembling context for an LLM call.

    Contains the ordered list of nodes (verbatim + compacted) that fit
    within the requested token budget, along with metadata about what
    compaction was applied.
    """

    nodes: list[ContextNode] = Field(default_factory=list)
    total_tokens: int = 0
    compaction_applied: bool = False


class GrepResult(BaseModel):
    """A single hit from searching the immutable message store."""

    message_id: str
    seq: int
    role: str
    content_snippet: str
    created_at: datetime = Field(default_factory=datetime.now)


class ExpandResult(BaseModel):
    """Result of expanding a compacted node back to its original messages."""

    node_id: str
    level: CompactionLevel = CompactionLevel.VERBATIM
    original_messages: list[ContextMessage] = Field(default_factory=list)


class DescribeResult(BaseModel):
    """Metadata snapshot of the entire context store."""

    total_messages: int = 0
    total_nodes: int = 0
    total_tokens: int = 0
    date_range: tuple[datetime | None, datetime | None] = (None, None)
    compaction_stats: dict[str, int] = Field(default_factory=dict)
