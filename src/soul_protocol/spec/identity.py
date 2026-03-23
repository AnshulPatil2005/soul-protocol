# identity.py — Schema-free identity primitive for the core layer.
# Updated: feat/spec-multi-participant — Added BondTarget model for multi-bond
#   identity support. A soul can bond to multiple entities (humans, other souls,
#   agents, groups, services). Identity gains a bonds list alongside the
#   deprecated bonded_to field for backward compatibility.
# Created: v0.4.0 — Minimal identity with arbitrary traits dict.
# No opinions about OCEAN, Big Five, or any personality model.
# Traits are just key-value pairs the runtime can interpret however it wants.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BondTarget(BaseModel):
    """An entity this soul is bonded to.

    Bond targets are portable — they travel with the soul across platforms.
    The bond_type field classifies the relationship kind.
    """

    id: str  # DID or identifier
    label: str = ""  # Human-readable name
    bond_type: str = "human"  # "human", "soul", "agent", "group", "service"


class Identity(BaseModel):
    """A soul's identity — schema-free, portable.

    The protocol doesn't prescribe a personality model. ``traits`` is an
    open dict — runtimes can store OCEAN scores, Myers-Briggs, custom
    dimensions, or nothing at all.

    Multi-bond support: ``bonds`` holds a list of BondTarget entities.
    The legacy ``bonded_to`` field is preserved for backward compatibility.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    traits: dict[str, Any] = Field(default_factory=dict)
    bonded_to: str | None = None  # DEPRECATED — use bonds instead
    bonds: list[BondTarget] = Field(default_factory=list)
