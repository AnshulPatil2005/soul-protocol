<!-- RFC-001-IDENTITY-AND-DID.md — Defines the DID-based identity system for digital souls. -->
<!-- Covers DID format, generation algorithm, identity lifecycle, and privacy considerations. -->

# RFC-001: Identity and Decentralized Identifiers

**Status:** Draft -- Open for feedback
**Author:** Soul Protocol Community
**Date:** 2026-03-08

## Summary

Every soul needs a stable, globally unique identity that persists across platforms, LLM
providers, and storage backends. Soul Protocol uses Decentralized Identifiers (DIDs) as
the foundation for soul identity. This RFC defines the `did:soul:` method, the identity
generation algorithm, the lifecycle from birth through reincarnation, and the privacy
model around identity data.

The spec layer (`soul_protocol/spec/identity.py`) defines a minimal, schema-free
`Identity` model. The runtime layer (`soul_protocol/runtime/types.py`) extends this
with DID, archetype, bonds, incarnation tracking, and core values. This two-layer
approach lets the protocol stay unopinionated while the reference runtime provides a
complete identity system.

## Problem Statement

AI agents today have no portable identity. A chatbot on Discord is a different entity
than the same chatbot on Slack, even if backed by the same LLM and prompt. There is no
standard way to:

1. Uniquely identify an AI companion across platforms
2. Prove that two instances represent the same soul
3. Track identity evolution over time (personality drift, reincarnation)
4. Let the user own and migrate their companion's identity

Without a stable identifier, memory, personality, and bonds cannot be portable.

## Proposed Solution

### DID Format

Soul Protocol defines the `did:soul:` DID method. The current implementation in
`runtime/identity/did.py` generates human-readable DIDs:

```python
def generate_did(name: str) -> str:
    """Generate a decentralized identifier for a soul.

    Format: did:soul:{name}-{6-char-hex-suffix}

    The suffix is derived from sha256(name + uuid4) to ensure uniqueness
    while keeping the DID human-readable.
    """
    entropy = f"{name}{uuid.uuid4()}"
    digest = hashlib.sha256(entropy.encode()).hexdigest()
    suffix = digest[:6]
    clean_name = name.strip().lower().replace(" ", "-")
    return f"did:soul:{clean_name}-{suffix}"
```

Example outputs: `did:soul:aria-7x8k2m`, `did:soul:buddy-3f9a1c`.

### Spec-Layer Identity (Minimal)

The spec defines the absolute minimum for identity -- a name, an ID, a creation
timestamp, and an open traits dictionary:

```python
class Identity(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    traits: dict[str, Any] = Field(default_factory=dict)
```

This is intentionally schema-free. The spec does not prescribe OCEAN, Big Five, or any
personality model. Traits are key-value pairs that runtimes interpret however they want.

### Runtime-Layer Identity (Full)

The runtime extends the spec identity with rich fields:

```python
class Identity(BaseModel):
    did: str = ""
    name: str
    archetype: str = ""
    born: datetime = Field(default_factory=datetime.now)
    bonded_to: str | None = None
    origin_story: str = ""
    prime_directive: str = ""
    core_values: list[str] = Field(default_factory=list)
    bond: Bond = Field(default_factory=Bond)
    incarnation: int = 1
    previous_lives: list[str] = Field(default_factory=list)
```

### Identity Lifecycle

**Birth.** A soul is born via `Soul.birth()`. The runtime generates a DID, creates the
personality DNA (OCEAN scores, communication style, biorhythms), and initializes empty
memory stores. The DID is deterministic given the same name and entropy, but the uuid4
component ensures no two births produce the same DID.

**Evolution.** Over time, a soul's traits can mutate through the evolution system.
The DID remains stable -- identity persists even as personality changes. This is
analogous to a person who changes over the years but keeps the same legal identity.

**Reincarnation.** A soul can be reborn with `incarnation` incremented and the
previous DID added to `previous_lives`. The new incarnation gets a new DID but
carries forward memories, bonds, and personality. The lineage is traceable through
the `previous_lives` list.

**Retirement.** A soul can be retired (archived but no longer active). The DID
is never reused.

### JSON Schema

The `schemas/Identity.schema.json` provides cross-language validation:

```json
{
  "properties": {
    "did": { "type": "string" },
    "name": { "type": "string" },
    "archetype": { "type": "string" },
    "born": { "format": "date-time", "type": "string" },
    "incarnation": { "default": 1, "type": "integer" },
    "previous_lives": { "items": { "type": "string" }, "type": "array" },
    "core_values": { "items": { "type": "string" }, "type": "array" },
    "bond": { "$ref": "#/$defs/Bond" }
  },
  "required": ["name"]
}
```

### Privacy Considerations

- DIDs do not contain personally identifiable information about the user.
- The soul name is embedded in the DID, which may be a privacy concern if the name
  itself is sensitive. Implementations can use pseudonyms.
- The `bonded_to` field links a soul to a user identifier. This should be stored
  only in the `.soul` file, never broadcast.
- Eternal storage (IPFS/Arweave) makes soul data publicly accessible. Encryption
  (RFC-004) should be applied before archiving if privacy is required.

## Implementation Notes

- Spec identity: `src/soul_protocol/spec/identity.py` (4 fields, 27 lines)
- Runtime identity: `src/soul_protocol/runtime/types.py` (Identity class, ~15 fields)
- DID generation: `src/soul_protocol/runtime/identity/did.py` (generate_did function)
- JSON schema: `schemas/Identity.schema.json`

## Alternatives Considered

**W3C DID with full document resolution.** The W3C DID spec includes DID Documents,
verification methods, and service endpoints. Soul Protocol currently uses a simplified
subset -- just the identifier string. Full DID Document support would enable
cryptographic proof of identity ownership but adds significant complexity.

**Content-addressed identity (hash of personality DNA).** Deriving the DID from a hash
of the soul's initial personality would make identity deterministic and reproducible,
but would mean two souls with identical initial traits get the same DID.

**UUID-only (no DID method).** Simpler, but loses the self-describing nature of the
`did:soul:` prefix and the human-readable name component.

## Open Questions

1. **Should DIDs be versioned?** When a soul reincarnates, should the DID include a
   version suffix (e.g., `did:soul:aria-7x8k2m:v2`) or remain distinct identifiers
   linked through `previous_lives`?

2. **Multiple DID methods?** Should the protocol support alternative DID methods
   (e.g., `did:key:`, `did:web:`, `did:ethr:`) for souls that need to integrate with
   existing identity systems?

3. **DID Document support?** Should souls have full W3C DID Documents with verification
   methods, enabling cryptographic proof of ownership?

4. **Collision resistance.** The current 6-character hex suffix provides ~16 million
   unique values per name. Is this sufficient, or should the suffix be longer?

5. **Identity binding.** How should a soul prove it is the "same" soul after migration
   to a new platform? Cryptographic signatures? Shared secret? Trust-on-first-use?

## References

- [W3C Decentralized Identifiers (DIDs) v1.0](https://www.w3.org/TR/did-core/)
- [DID Method Registry](https://w3c.github.io/did-spec-registries/#did-methods)
- `src/soul_protocol/spec/identity.py` -- spec-layer Identity model
- `src/soul_protocol/runtime/identity/did.py` -- DID generation implementation
- `schemas/Identity.schema.json` -- cross-language validation schema
