# test_core/test_manifest.py — Tests for the Manifest model.
# Created: 2026-03-06 — Covers default field values and Pydantic roundtrip serialization.

from __future__ import annotations

from soul_protocol.core import Manifest


def test_manifest_defaults():
    """Manifest has sensible defaults for all fields."""
    manifest = Manifest()

    assert manifest.format_version == "1.0.0"
    assert manifest.soul_id == ""
    assert manifest.soul_name == ""
    assert manifest.checksum == ""
    assert manifest.stats == {}
    assert manifest.created is not None


def test_manifest_with_values():
    """Manifest stores provided values correctly."""
    manifest = Manifest(
        soul_id="abc123",
        soul_name="Aria",
        stats={"total_memories": 5, "layers": ["episodic"]},
    )

    assert manifest.soul_id == "abc123"
    assert manifest.soul_name == "Aria"
    assert manifest.stats["total_memories"] == 5


def test_manifest_serialization():
    """model_dump / model_validate roundtrip preserves all fields."""
    manifest = Manifest(
        soul_id="xyz789",
        soul_name="Kairos",
        format_version="1.0.0",
        checksum="sha256:abc",
        stats={"total_memories": 3, "layers": ["semantic", "episodic"]},
    )

    raw = manifest.model_dump()
    restored = Manifest.model_validate(raw)

    assert restored.soul_id == manifest.soul_id
    assert restored.soul_name == manifest.soul_name
    assert restored.format_version == manifest.format_version
    assert restored.checksum == manifest.checksum
    assert restored.stats == manifest.stats
    assert restored.created == manifest.created
