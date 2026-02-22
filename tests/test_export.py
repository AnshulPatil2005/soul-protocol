# test_export.py — Tests for pack/unpack (.soul zip archive) operations.
# Created: 2026-02-22 — Covers roundtrip serialization and archive contents.

from __future__ import annotations

import io
import zipfile

import pytest

from soul_protocol.export.pack import pack_soul
from soul_protocol.export.unpack import unpack_soul
from soul_protocol.types import Identity, SoulConfig


@pytest.fixture
def config() -> SoulConfig:
    """Return a SoulConfig for export tests."""
    return SoulConfig(
        identity=Identity(
            name="Aria",
            did="did:soul:aria-abc123",
            archetype="The Compassionate Creator",
            core_values=["empathy", "creativity"],
        ),
    )


async def test_pack_and_unpack_roundtrip(config: SoulConfig):
    """pack_soul -> unpack_soul preserves the SoulConfig data."""
    packed = await pack_soul(config)
    assert isinstance(packed, bytes)
    assert len(packed) > 0

    restored = await unpack_soul(packed)

    assert restored.identity.name == "Aria"
    assert restored.identity.did == "did:soul:aria-abc123"
    assert restored.identity.archetype == "The Compassionate Creator"
    assert restored.identity.core_values == ["empathy", "creativity"]
    assert restored.version == "1.0.0"


async def test_pack_contains_expected_files(config: SoulConfig):
    """Packed archive contains manifest.json, soul.json, dna.md, state.json, memory/core.json."""
    packed = await pack_soul(config)

    buf = io.BytesIO(packed)
    with zipfile.ZipFile(buf, "r") as zf:
        names = set(zf.namelist())

    expected = {"manifest.json", "soul.json", "dna.md", "state.json", "memory/core.json"}
    assert expected.issubset(names), f"Missing files: {expected - names}"
