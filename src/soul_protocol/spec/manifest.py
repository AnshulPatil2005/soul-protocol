# manifest.py — Manifest model for .soul archive files (core layer).
# Created: v0.4.0 — Minimal manifest with format version, soul metadata,
# creation timestamp, checksum placeholder, and open stats dict.

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Manifest(BaseModel):
    """Manifest for a .soul archive file.

    Stored as ``manifest.json`` at the root of the zip archive.
    The ``stats`` dict is open for runtime-specific metadata
    (memory counts, layer names, export tool version, etc.).
    """

    format_version: str = "1.0.0"
    soul_id: str = ""
    soul_name: str = ""
    created: datetime = Field(default_factory=datetime.now)
    checksum: str = ""
    stats: dict[str, Any] = Field(default_factory=dict)
