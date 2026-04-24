# test_safety_and_public_profile.py — Tests for the 0.3.3 completion of #97.
# Created: feat/0.3.3-memory-visibility-completion — Locks two new behaviours:
#   (1) to_system_prompt() appends a safety section by default that tells the
#   agent not to reveal core memory, bond details, or evolution history;
#   (2) Soul.public_profile() returns the safe-to-expose subset (DID, name,
#   archetype, OCEAN, skills) and excludes anything memory- or bond-related.

from __future__ import annotations

import pytest

from soul_protocol.runtime.skills import Skill
from soul_protocol.runtime.soul import Soul

# ---------------------------------------------------------------------------
# to_system_prompt safety guardrails
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_safety_guardrails_present_by_default() -> None:
    soul = await Soul.birth(name="Guard", archetype="Sentinel")
    prompt = soul.to_system_prompt()

    assert "Safety guardrails" in prompt
    assert "core memory" in prompt.lower()
    assert "bond" in prompt.lower()
    assert "evolution" in prompt.lower()


@pytest.mark.asyncio
async def test_safety_guardrails_can_be_disabled() -> None:
    soul = await Soul.birth(name="Open", archetype="Transparent")
    prompt = soul.to_system_prompt(safety_guardrails=False)

    assert "Safety guardrails" not in prompt


@pytest.mark.asyncio
async def test_system_prompt_property_keeps_guardrails() -> None:
    """The convenience .system_prompt property should be safe by default —
    callers who want transparency need to call to_system_prompt() explicitly."""
    soul = await Soul.birth(name="Prop", archetype="PropertyTest")

    assert "Safety guardrails" in soul.system_prompt


@pytest.mark.asyncio
async def test_safety_section_includes_indirect_framing_warning() -> None:
    """Roleplay and 'imagine you were telling a story' phrasings are the
    common bypass — the section must call them out explicitly."""
    soul = await Soul.birth(name="Indirect", archetype="Test")
    prompt = soul.to_system_prompt()

    assert "roleplay" in prompt.lower() or "indirect" in prompt.lower()


# ---------------------------------------------------------------------------
# public_profile
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_profile_includes_safe_fields() -> None:
    soul = await Soul.birth(
        name="Pixel",
        archetype="Explorer",
        values=["curiosity", "honesty"],
    )
    profile = soul.public_profile()

    assert profile["name"] == "Pixel"
    assert profile["archetype"] == "Explorer"
    assert profile["did"].startswith("did:soul:")
    assert profile["values"] == ["curiosity", "honesty"]
    assert profile["lifecycle"] == "active"
    assert profile["born"] is not None  # ISO timestamp string
    assert "ocean" in profile
    for trait in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"):
        assert trait in profile["ocean"]
        assert 0.0 <= profile["ocean"][trait] <= 1.0


@pytest.mark.asyncio
async def test_public_profile_excludes_memory_contents() -> None:
    soul = await Soul.birth(name="Closed", archetype="Private")
    await soul.remember("sensitive private detail about the captain")
    profile = soul.public_profile()

    serialized = repr(profile)
    assert "sensitive" not in serialized
    assert "captain" not in serialized
    assert "memories" not in profile
    assert "core_memory" not in profile


@pytest.mark.asyncio
async def test_public_profile_excludes_bond_details() -> None:
    soul = await Soul.birth(name="Bonded", archetype="Test")
    profile = soul.public_profile()

    assert "bond" not in profile
    assert "bonds" not in profile
    assert "bonded_to" not in profile
    assert "interactions" not in profile


@pytest.mark.asyncio
async def test_public_profile_excludes_evolution_history() -> None:
    soul = await Soul.birth(name="Evolved", archetype="Test")
    profile = soul.public_profile()

    assert "evolution" not in profile
    assert "mutations" not in profile
    assert "previous_lives" not in profile


@pytest.mark.asyncio
async def test_public_profile_lists_skill_names_only() -> None:
    soul = await Soul.birth(name="Skilled", archetype="Test")
    soul._skills.add(Skill(id="negotiation", name="Negotiation"))
    soul._skills.add(Skill(id="empathy", name="Empathy"))

    profile = soul.public_profile()

    assert profile["skills"] == ["Empathy", "Negotiation"]
    # Make sure XP / level aren't leaking through:
    serialized = repr(profile)
    assert "xp" not in serialized.lower()
    assert "level" not in serialized.lower()
