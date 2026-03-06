# exceptions.py — Custom exception classes for soul-protocol.
# Created: v0.3.2 — SoulFileNotFoundError, SoulCorruptError, SoulExportError,
#   SoulRetireError for proper error handling in awaken(), export(), retire().

from __future__ import annotations


class SoulProtocolError(Exception):
    """Base exception for all soul-protocol errors."""


class SoulFileNotFoundError(SoulProtocolError):
    """Raised when a soul file does not exist at the given path."""

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"No soul file at {path}")


class SoulCorruptError(SoulProtocolError):
    """Raised when a .soul archive is invalid or corrupted."""

    def __init__(self, path: str, reason: str = "") -> None:
        self.path = path
        self.reason = reason
        detail = f" — {reason}" if reason else ""
        super().__init__(f"Invalid .soul archive at {path}{detail}")


class SoulExportError(SoulProtocolError):
    """Raised when exporting a soul fails (disk full, permissions, etc.)."""

    def __init__(self, path: str, reason: str = "") -> None:
        self.path = path
        self.reason = reason
        detail = f" — {reason}" if reason else ""
        super().__init__(f"Failed to export soul to {path}{detail}")


class SoulRetireError(SoulProtocolError):
    """Raised when retiring a soul fails because memory preservation failed."""

    def __init__(self, reason: str = "") -> None:
        self.reason = reason
        super().__init__(f"Cannot retire soul: failed to save memories — {reason}")
