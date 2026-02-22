# test_self_model.py — Tests for Klein's self-concept model.
# Created: 2026-02-22 — Full coverage of SelfModelManager: domain detection,
#   confidence accumulation, multi-domain coexistence, serialization round-trip,
#   prompt fragment generation, and relationship note extraction.

from __future__ import annotations

import pytest

from soul_protocol.memory.self_model import DOMAIN_KEYWORDS, SelfModelManager
from soul_protocol.types import Interaction, MemoryEntry, MemoryType, SelfImage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _interaction(user_input: str = "", agent_output: str = "") -> Interaction:
    """Build a minimal Interaction for testing."""
    return Interaction(user_input=user_input, agent_output=agent_output)


def _fact(content: str) -> MemoryEntry:
    """Build a semantic MemoryEntry with the given content."""
    return MemoryEntry(type=MemoryType.SEMANTIC, content=content)


def _expected_confidence(evidence_count: int) -> float:
    """The confidence formula used by SelfModelManager._update_domain."""
    return min(0.95, 0.1 + 0.85 * (1 - 1 / (1 + evidence_count * 0.1)))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def manager() -> SelfModelManager:
    """Return a fresh SelfModelManager with no prior experience."""
    return SelfModelManager()


# ---------------------------------------------------------------------------
# 1. New manager starts empty
# ---------------------------------------------------------------------------

def test_new_manager_has_no_self_images(manager: SelfModelManager) -> None:
    """A freshly created SelfModelManager has no self-images."""
    assert manager.self_images == {}


def test_new_manager_has_no_relationship_notes(manager: SelfModelManager) -> None:
    """A freshly created SelfModelManager has no relationship notes."""
    assert manager.relationship_notes == {}


# ---------------------------------------------------------------------------
# 2. Technical interaction creates technical_helper self-image
# ---------------------------------------------------------------------------

def test_technical_interaction_creates_technical_helper(manager: SelfModelManager) -> None:
    """An interaction mentioning Python code should create a technical_helper self-image."""
    manager.update_from_interaction(
        _interaction("Help me write a python function", "Sure, here is the code"),
        [],
    )
    assert "technical_helper" in manager.self_images


def test_technical_helper_confidence_above_baseline(manager: SelfModelManager) -> None:
    """After a technical interaction, technical_helper confidence exceeds the initial 0.1 floor."""
    manager.update_from_interaction(
        _interaction("Debug my python code", "Found the error"),
        [],
    )
    img = manager.self_images["technical_helper"]
    assert img.confidence > 0.1


# ---------------------------------------------------------------------------
# 3. Evidence accumulates across multiple interactions
# ---------------------------------------------------------------------------

def test_evidence_accumulates_with_repeated_interactions(manager: SelfModelManager) -> None:
    """Each technical interaction increases evidence_count for technical_helper."""
    interaction = _interaction("Review this python code", "Looks good")
    manager.update_from_interaction(interaction, [])
    first_count = manager.self_images["technical_helper"].evidence_count

    manager.update_from_interaction(interaction, [])
    second_count = manager.self_images["technical_helper"].evidence_count

    assert second_count > first_count


def test_confidence_grows_with_more_interactions(manager: SelfModelManager) -> None:
    """More interactions with technical content should raise confidence monotonically."""
    interaction = _interaction("Explain this python algorithm", "Here is how it works")

    manager.update_from_interaction(interaction, [])
    first_confidence = manager.self_images["technical_helper"].confidence

    for _ in range(10):
        manager.update_from_interaction(interaction, [])

    later_confidence = manager.self_images["technical_helper"].confidence
    assert later_confidence > first_confidence


# ---------------------------------------------------------------------------
# 4. Multiple domains can coexist
# ---------------------------------------------------------------------------

def test_multiple_domains_coexist(manager: SelfModelManager) -> None:
    """A technical AND creative interaction can produce self-images for both domains."""
    manager.update_from_interaction(
        _interaction("Write a story about python programming", "Once upon a function..."),
        [],
    )
    images = manager.self_images
    # Both technical and creative signals are present in that sentence
    assert "technical_helper" in images or "creative_writer" in images
    assert len(images) >= 2


def test_distinct_interactions_build_separate_domains(manager: SelfModelManager) -> None:
    """Separate interactions targeting different domains each create their own self-image."""
    manager.update_from_interaction(
        _interaction("Help me debug this code", "Fixed it"), []
    )
    manager.update_from_interaction(
        _interaction("Write a short poem for me", "Roses are red..."), []
    )
    images = manager.self_images
    assert "technical_helper" in images
    assert "creative_writer" in images


# ---------------------------------------------------------------------------
# 5. get_active_self_images respects the limit
# ---------------------------------------------------------------------------

def test_get_active_self_images_respects_limit(manager: SelfModelManager) -> None:
    """get_active_self_images(limit=1) returns at most one result."""
    manager.update_from_interaction(
        _interaction("Debug my python code", "Fixed"), []
    )
    manager.update_from_interaction(
        _interaction("Write a creative story", "Once upon a time"), []
    )
    manager.update_from_interaction(
        _interaction("Explain this concept to me", "Sure"), []
    )
    active = manager.get_active_self_images(limit=1)
    assert len(active) == 1


def test_get_active_self_images_returns_at_most_limit(manager: SelfModelManager) -> None:
    """get_active_self_images with limit=2 returns no more than 2 images even with more domains."""
    interactions = [
        _interaction("python code debugging", "Fixed"),
        _interaction("write a creative story poem", "Once upon a time"),
        _interaction("explain the science concept", "Sure, the theory is"),
        _interaction("brainstorm new design ideas", "Let me think"),
    ]
    for i in interactions:
        manager.update_from_interaction(i, [])

    active = manager.get_active_self_images(limit=2)
    assert len(active) <= 2


# ---------------------------------------------------------------------------
# 6. get_active_self_images sorted by confidence (descending)
# ---------------------------------------------------------------------------

def test_get_active_self_images_sorted_by_confidence_descending(manager: SelfModelManager) -> None:
    """get_active_self_images returns images sorted highest confidence first."""
    # Build up technical_helper with many interactions so it has the highest confidence
    tech_interaction = _interaction("python code function algorithm", "Here is the solution")
    for _ in range(15):
        manager.update_from_interaction(tech_interaction, [])

    # One creative interaction gives creative_writer less evidence
    manager.update_from_interaction(
        _interaction("write a short story", "Once upon a time"), []
    )

    active = manager.get_active_self_images(limit=3)
    assert len(active) >= 2
    confidences = [img.confidence for img in active]
    assert confidences == sorted(confidences, reverse=True)


# ---------------------------------------------------------------------------
# 7. to_dict / from_dict round-trip
# ---------------------------------------------------------------------------

def test_to_dict_from_dict_round_trip_self_images(manager: SelfModelManager) -> None:
    """Serializing and deserializing preserves all self-image domain data."""
    manager.update_from_interaction(
        _interaction("I need help with python code", "Here is the fix"), []
    )
    original_images = manager.self_images

    restored = SelfModelManager.from_dict(manager.to_dict())

    assert set(restored.self_images.keys()) == set(original_images.keys())
    for domain, img in original_images.items():
        restored_img = restored.self_images[domain]
        assert restored_img.domain == img.domain
        assert restored_img.confidence == pytest.approx(img.confidence)
        assert restored_img.evidence_count == img.evidence_count


def test_to_dict_from_dict_round_trip_relationship_notes(manager: SelfModelManager) -> None:
    """Serializing and deserializing preserves relationship notes."""
    manager.update_from_interaction(
        _interaction("Hi", "Hello!"),
        [_fact("User's name is Elena")],
    )
    original_notes = manager.relationship_notes

    restored = SelfModelManager.from_dict(manager.to_dict())

    assert restored.relationship_notes == original_notes


def test_from_dict_empty_data_creates_empty_manager() -> None:
    """from_dict with an empty dict produces a manager with no images or notes."""
    manager = SelfModelManager.from_dict({})
    assert manager.self_images == {}
    assert manager.relationship_notes == {}


# ---------------------------------------------------------------------------
# 8. to_prompt_fragment with no images returns empty string
# ---------------------------------------------------------------------------

def test_prompt_fragment_empty_when_no_self_images(manager: SelfModelManager) -> None:
    """to_prompt_fragment returns an empty string when the soul has no self-images."""
    assert manager.to_prompt_fragment() == ""


# ---------------------------------------------------------------------------
# 9. to_prompt_fragment with images contains domain names
# ---------------------------------------------------------------------------

def test_prompt_fragment_contains_domain_name(manager: SelfModelManager) -> None:
    """to_prompt_fragment includes the active domain name in human-readable form."""
    manager.update_from_interaction(
        _interaction("Help debug my python code", "Fixed"), []
    )
    fragment = manager.to_prompt_fragment()
    # Domain "technical_helper" is rendered as "technical helper" (underscores → spaces)
    assert "technical helper" in fragment


def test_prompt_fragment_contains_self_understanding_header(manager: SelfModelManager) -> None:
    """to_prompt_fragment includes the ## Self-Understanding header when images exist."""
    manager.update_from_interaction(
        _interaction("Write a story for me", "Once upon a time"), []
    )
    fragment = manager.to_prompt_fragment()
    assert "## Self-Understanding" in fragment


def test_prompt_fragment_confidence_label_emerging_for_low_confidence(manager: SelfModelManager) -> None:
    """A domain with low evidence shows 'emerging' confidence label in the prompt."""
    # One interaction → evidence_count will be small → confidence < 0.4
    manager.update_from_interaction(
        _interaction("write a short poem", "Roses are red"), []
    )
    fragment = manager.to_prompt_fragment()
    assert "emerging" in fragment


# ---------------------------------------------------------------------------
# 10. relationship_notes extracted from facts
# ---------------------------------------------------------------------------

def test_relationship_notes_captures_user_name(manager: SelfModelManager) -> None:
    """A fact containing \"User's name is X\" is recorded in relationship_notes."""
    manager.update_from_interaction(
        _interaction("Hi", "Hello!"),
        [_fact("User's name is Marcus")],
    )
    assert "user" in manager.relationship_notes
    assert "Marcus" in manager.relationship_notes["user"]


def test_relationship_notes_captures_workplace(manager: SelfModelManager) -> None:
    """A fact containing \"User works at X\" is recorded in relationship_notes."""
    manager.update_from_interaction(
        _interaction("Hi", "Hello!"),
        [_fact("User works at Acme Corp")],
    )
    assert "user" in manager.relationship_notes
    assert "Acme Corp" in manager.relationship_notes["user"]


# ---------------------------------------------------------------------------
# 11. Confidence formula: many interactions → high confidence
# ---------------------------------------------------------------------------

def test_high_evidence_produces_high_confidence(manager: SelfModelManager) -> None:
    """After many technical interactions, technical_helper confidence exceeds 0.85."""
    interaction = _interaction("python code debug algorithm", "Here is the fix")
    # 50 iterations with 3+ keyword matches each → large evidence_count
    for _ in range(50):
        manager.update_from_interaction(interaction, [])

    img = manager.self_images["technical_helper"]
    assert img.confidence > 0.85


def test_confidence_never_exceeds_cap(manager: SelfModelManager) -> None:
    """No matter how many interactions occur, confidence is capped at 0.95."""
    interaction = _interaction("python code debug algorithm function class", "Done")
    for _ in range(500):
        manager.update_from_interaction(interaction, [])

    img = manager.self_images["technical_helper"]
    assert img.confidence <= 0.95


# ---------------------------------------------------------------------------
# 12. Confidence formula: few interactions → low confidence
# ---------------------------------------------------------------------------

def test_few_interactions_produce_low_confidence(manager: SelfModelManager) -> None:
    """After only one interaction, confidence for any domain stays below 0.4."""
    manager.update_from_interaction(
        _interaction("Help me with some python code", "Sure"), []
    )
    for img in manager.self_images.values():
        assert img.confidence < 0.4


def test_confidence_formula_matches_expected_value(manager: SelfModelManager) -> None:
    """The stored confidence exactly matches the formula for the accumulated evidence_count."""
    interaction = _interaction("python code debug", "Fixed")
    # Run a known number of times so we can compute expected evidence_count
    for _ in range(5):
        manager.update_from_interaction(interaction, [])

    img = manager.self_images["technical_helper"]
    expected = _expected_confidence(img.evidence_count)
    assert img.confidence == pytest.approx(expected, abs=1e-9)
