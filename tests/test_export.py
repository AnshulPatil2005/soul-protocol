# test_export.py — Tests for pack/unpack (.soul zip archive) operations.
# Updated: 2026-02-22 — Updated for new pack_soul/unpack_soul signatures.
# pack_soul now accepts optional memory_data; unpack_soul returns
# tuple[SoulConfig, dict]. Tests cover roundtrip with and without memory.

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

    restored, memory_data = await unpack_soul(packed)

    assert restored.identity.name == "Aria"
    assert restored.identity.did == "did:soul:aria-abc123"
    assert restored.identity.archetype == "The Compassionate Creator"
    assert restored.identity.core_values == ["empathy", "creativity"]
    assert restored.version == "1.0.0"

    # Without memory_data param, only core memory is in archive
    assert "core" in memory_data


async def test_pack_contains_expected_files(config: SoulConfig):
    """Packed archive contains manifest.json, soul.json, dna.md, state.json, memory/core.json."""
    packed = await pack_soul(config)

    buf = io.BytesIO(packed)
    with zipfile.ZipFile(buf, "r") as zf:
        names = set(zf.namelist())

    expected = {"manifest.json", "soul.json", "dna.md", "state.json", "memory/core.json"}
    assert expected.issubset(names), f"Missing files: {expected - names}"


async def test_pack_with_memory_data(config: SoulConfig):
    """pack_soul with memory_data includes all memory tier files."""
    memory_data = {
        "core": {"persona": "I am Aria.", "human": "User is kind."},
        "episodic": [
            {
                "id": "ep1",
                "type": "episodic",
                "content": "User: hello\nAgent: hi",
                "importance": 5,
                "confidence": 1.0,
                "entities": [],
                "created_at": "2026-02-22T00:00:00",
                "access_count": 0,
            }
        ],
        "semantic": [
            {
                "id": "sem1",
                "type": "semantic",
                "content": "User prefers Python",
                "importance": 8,
                "confidence": 1.0,
                "entities": [],
                "created_at": "2026-02-22T00:00:00",
                "access_count": 0,
            }
        ],
        "procedural": [],
        "graph": {"entities": {"Alice": "person"}, "edges": []},
    }

    packed = await pack_soul(config, memory_data=memory_data)

    buf = io.BytesIO(packed)
    with zipfile.ZipFile(buf, "r") as zf:
        names = set(zf.namelist())

    expected_memory = {
        "memory/core.json",
        "memory/episodic.json",
        "memory/semantic.json",
        "memory/procedural.json",
        "memory/graph.json",
    }
    assert expected_memory.issubset(names), f"Missing memory files: {expected_memory - names}"


async def test_pack_unpack_roundtrip_with_memory(config: SoulConfig):
    """Full roundtrip with memory_data preserves memory content."""
    memory_data = {
        "core": {"persona": "I am Aria.", "human": "User is kind."},
        "episodic": [
            {
                "id": "ep1",
                "type": "episodic",
                "content": "User: hello\nAgent: hi",
                "importance": 5,
                "confidence": 1.0,
                "entities": [],
                "created_at": "2026-02-22T00:00:00",
                "access_count": 0,
            }
        ],
        "semantic": [],
        "procedural": [],
        "graph": {"entities": {"Alice": "person"}, "edges": []},
    }

    packed = await pack_soul(config, memory_data=memory_data)
    restored_config, restored_memory = await unpack_soul(packed)

    assert restored_config.identity.name == "Aria"
    assert restored_memory["core"]["persona"] == "I am Aria."
    assert len(restored_memory["episodic"]) == 1
    assert restored_memory["episodic"][0]["id"] == "ep1"
    assert restored_memory["graph"]["entities"]["Alice"] == "person"
