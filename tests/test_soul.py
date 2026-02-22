# test_soul.py — Tests for the main Soul class API surface.
# Updated: 2026-02-22 — Added save/load full round-trip test and
# export/awaken memory fidelity test.

from __future__ import annotations

import pytest

from soul_protocol.soul import Soul
from soul_protocol.types import (
    Interaction,
    LifecycleState,
    MemoryType,
    Mood,
    SoulConfig,
)


async def test_birth():
    """Soul.birth creates a soul with correct defaults."""
    soul = await Soul.birth("Aria", archetype="The Compassionate Creator")

    assert soul.name == "Aria"
    assert soul.archetype == "The Compassionate Creator"
    assert soul.did.startswith("did:soul:aria-")
    assert soul.lifecycle == LifecycleState.ACTIVE
    assert soul.state.mood == Mood.NEUTRAL
    assert soul.state.energy == 100.0


async def test_birth_with_values():
    """Soul.birth with core_values stores them correctly."""
    soul = await Soul.birth(
        "Aria",
        archetype="The Compassionate Creator",
        values=["empathy", "creativity", "honesty"],
    )

    assert soul.identity.core_values == ["empathy", "creativity", "honesty"]


async def test_remember_and_recall():
    """remember() stores a fact, recall() retrieves it by keyword."""
    soul = await Soul.birth("Aria")

    memory_id = await soul.remember(
        "User prefers dark mode",
        type=MemoryType.SEMANTIC,
        importance=7,
    )
    assert memory_id  # non-empty ID returned

    results = await soul.recall("dark mode")
    assert len(results) >= 1
    assert any("dark mode" in r.content for r in results)


async def test_observe():
    """observe() processes an interaction and updates state."""
    soul = await Soul.birth("Aria")

    initial_energy = soul.state.energy
    initial_social = soul.state.social_battery

    interaction = Interaction(
        user_input="Hello, how are you?",
        agent_output="I'm doing well, thanks!",
        channel="test",
    )
    await soul.observe(interaction)

    # Energy and social battery should drain after interaction
    assert soul.state.energy < initial_energy
    assert soul.state.social_battery < initial_social
    assert soul.state.last_interaction is not None


async def test_feel():
    """feel() updates mood and energy via delta-based state changes."""
    soul = await Soul.birth("Aria")

    soul.feel(mood=Mood.TIRED)
    assert soul.state.mood == Mood.TIRED

    soul.feel(energy=-20)
    assert soul.state.energy == 80.0


async def test_export_and_awaken(tmp_path):
    """Export to .soul, awaken from it, verify identity is preserved."""
    original = await Soul.birth("Aria", archetype="The Compassionate Creator")
    soul_path = tmp_path / "aria.soul"

    await original.export(str(soul_path))
    assert soul_path.exists()

    restored = await Soul.awaken(str(soul_path))

    assert restored.name == original.name
    assert restored.archetype == original.archetype
    assert restored.did == original.did
    assert restored.lifecycle == LifecycleState.ACTIVE


async def test_system_prompt():
    """to_system_prompt() returns a non-empty string containing the soul's name."""
    soul = await Soul.birth("Aria", archetype="The Compassionate Creator")

    prompt = soul.to_system_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "Aria" in prompt


async def test_serialize_roundtrip():
    """serialize() -> SoulConfig -> new Soul -> verify equality."""
    original = await Soul.birth(
        "Aria",
        archetype="The Compassionate Creator",
        values=["empathy"],
    )

    config = original.serialize()
    assert isinstance(config, SoulConfig)
    assert config.identity.name == "Aria"

    # Roundtrip via JSON
    json_str = config.model_dump_json()
    restored_config = SoulConfig.model_validate_json(json_str)

    restored = Soul(restored_config)
    assert restored.name == original.name
    assert restored.did == original.did
    assert restored.identity.core_values == ["empathy"]


async def test_from_markdown():
    """Soul.from_markdown parses a simple SOUL.md string."""
    md_content = """---
name: TestBot
archetype: The Helper
---

# TestBot

# Personality
- openness: 0.8
- conscientiousness: 0.6
- extraversion: 0.7
- agreeableness: 0.9
- neuroticism: 0.2

# Core Values
- kindness
- reliability
"""
    soul = await Soul.from_markdown(md_content)

    assert soul.name == "TestBot"
    assert soul.archetype == "The Helper"
    assert soul.dna.personality.openness == pytest.approx(0.8, abs=0.01)
    assert soul.dna.personality.agreeableness == pytest.approx(0.9, abs=0.01)
    assert "kindness" in soul.identity.core_values
    assert "reliability" in soul.identity.core_values


async def test_export_awaken_preserves_memories(tmp_path):
    """Export/awaken round-trip preserves episodic and semantic memories."""
    soul = await Soul.birth("Aria")

    # Add memories across tiers
    await soul.remember("User likes dark mode", type=MemoryType.SEMANTIC, importance=7)
    await soul.observe(Interaction(
        user_input="My name is Prakash",
        agent_output="Nice to meet you, Prakash!",
    ))

    soul_path = tmp_path / "aria.soul"
    await soul.export(str(soul_path))

    restored = await Soul.awaken(str(soul_path))

    # Semantic memory should survive
    results = await restored.recall("dark mode")
    assert any("dark mode" in r.content for r in results)

    # Episodic memory from observe should survive
    results = await restored.recall("Prakash")
    assert len(results) >= 1


async def test_save_load_full_roundtrip(tmp_path):
    """Soul.save() + load_soul_full() preserves config and all memory tiers."""
    from soul_protocol.storage.file import load_soul_full

    soul = await Soul.birth("Aria")
    await soul.remember("User prefers Python", type=MemoryType.SEMANTIC, importance=8)
    await soul.observe(Interaction(
        user_input="I use FastAPI for my projects",
        agent_output="FastAPI is great for building APIs!",
    ))

    await soul.save(tmp_path)

    # Find the saved directory
    soul_id = soul.did
    soul_dir = tmp_path / soul_id
    assert soul_dir.exists()
    assert (soul_dir / "soul.json").exists()
    assert (soul_dir / "memory" / "semantic.json").exists()
    assert (soul_dir / "memory" / "episodic.json").exists()

    # Load and verify
    config, memory_data = await load_soul_full(soul_dir)
    assert config is not None
    assert config.identity.name == "Aria"
    assert len(memory_data.get("semantic", [])) >= 1
    assert len(memory_data.get("episodic", [])) >= 1
