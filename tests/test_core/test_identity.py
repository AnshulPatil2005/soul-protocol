# test_core/test_identity.py — Tests for the core Identity primitive.
# Created: 2026-03-06 — Covers basic construction, auto-id, arbitrary traits,
# and Pydantic model_dump / model_validate roundtrip.

from __future__ import annotations

from soul_protocol.core import Identity


def test_identity_basic():
    """Identity can be created with just a name."""
    identity = Identity(name="Aria")

    assert identity.name == "Aria"
    assert identity.traits == {}
    assert identity.created_at is not None


def test_identity_auto_id():
    """Identity auto-generates a 12-char hex id."""
    identity = Identity(name="Aria")

    assert len(identity.id) == 12
    assert all(c in "0123456789abcdef" for c in identity.id)


def test_identity_auto_id_is_unique():
    """Each Identity gets a unique auto-generated id."""
    a = Identity(name="Aria")
    b = Identity(name="Aria")

    assert a.id != b.id


def test_identity_traits():
    """Arbitrary traits dict is stored as-is."""
    traits = {"role": "assistant", "openness": 0.85, "tags": ["empathic"]}
    identity = Identity(name="Aria", traits=traits)

    assert identity.traits["role"] == "assistant"
    assert identity.traits["openness"] == 0.85
    assert identity.traits["tags"] == ["empathic"]


def test_identity_serialization():
    """model_dump / model_validate roundtrip preserves all fields."""
    identity = Identity(
        name="Aria",
        traits={"role": "guide", "level": 3},
    )

    raw = identity.model_dump()
    restored = Identity.model_validate(raw)

    assert restored.id == identity.id
    assert restored.name == identity.name
    assert restored.traits == identity.traits
    assert restored.created_at == identity.created_at


def test_identity_explicit_id():
    """An explicit id is preserved without auto-generation."""
    identity = Identity(name="Aria", id="abc123def456")

    assert identity.id == "abc123def456"
