# test_crypto.py — Tests for encryption (Fernet + PBKDF2) utilities.
# Created: 2026-02-22 — Covers encrypt/decrypt roundtrip, wrong passphrase,
# and deterministic key derivation with fixed salt.

from __future__ import annotations

import pytest
from cryptography.fernet import InvalidToken

from soul_protocol.runtime.crypto.encrypt import decrypt_data, derive_key, encrypt_data


def test_encrypt_decrypt_roundtrip():
    """encrypt_data -> decrypt_data returns the original plaintext."""
    plaintext = b"Hello, Soul Protocol! This is secret data."
    passphrase = "strong-passphrase-42"

    encrypted = encrypt_data(plaintext, passphrase)
    assert encrypted != plaintext
    assert len(encrypted) > len(plaintext)

    decrypted = decrypt_data(encrypted, passphrase)
    assert decrypted == plaintext


def test_wrong_passphrase_fails():
    """Decrypting with the wrong passphrase raises InvalidToken."""
    plaintext = b"Secret soul data"
    encrypted = encrypt_data(plaintext, "correct-passphrase")

    with pytest.raises(InvalidToken):
        decrypt_data(encrypted, "wrong-passphrase")


def test_derive_key_deterministic():
    """Same passphrase + same salt always produces the same key."""
    salt = b"fixed-salt-16byt"  # exactly 16 bytes

    key1, salt1 = derive_key("my-passphrase", salt=salt)
    key2, salt2 = derive_key("my-passphrase", salt=salt)

    assert key1 == key2
    assert salt1 == salt2 == salt

    # Different passphrase with same salt produces a different key
    key3, _ = derive_key("different-passphrase", salt=salt)
    assert key3 != key1
