# identity.py — Schema-free identity primitive for the core layer.
# Created: v0.4.0 — Minimal identity with arbitrary traits dict.
# No opinions about OCEAN, Big Five, or any personality model.
# Traits are just key-value pairs the runtime can interpret however it wants.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Identity(BaseModel):
    """A soul's identity — schema-free, portable.

    The protocol doesn't prescribe a personality model. ``traits`` is an
    open dict — runtimes can store OCEAN scores, Myers-Briggs, custom
    dimensions, or nothing at all.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    traits: dict[str, Any] = Field(default_factory=dict)
