# identity/did.py — DID generation for digital souls using the did:soul: method
# Created: 2026-02-22 — Generates deterministic-random DIDs from name + uuid4 entropy

from __future__ import annotations

import hashlib
import uuid


def generate_did(name: str) -> str:
    """Generate a decentralized identifier for a soul.

    Format: did:soul:{name}-{6-char-hex-suffix}

    The suffix is derived from sha256(name + uuid4) to ensure uniqueness
    while keeping the DID human-readable.

    Args:
        name: The soul's name (used as the readable prefix).

    Returns:
        A DID string like "did:soul:aria-7x8k2m".
    """
    entropy = f"{name}{uuid.uuid4()}"
    digest = hashlib.sha256(entropy.encode()).hexdigest()
    suffix = digest[:6]

    # Lowercase and strip whitespace from the name for a clean identifier
    clean_name = name.strip().lower().replace(" ", "-")

    return f"did:soul:{clean_name}-{suffix}"
