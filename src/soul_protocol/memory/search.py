# memory/search.py — Token-overlap relevance scoring for memory search.
# Updated: 2026-03-02 — Fixed tokenizer to split on /, _, -, . in addition to
#   whitespace so file paths and identifiers are searchable by component (issue #11).
#   Added synonym/alias expansion layer for improved recall on common programming
#   terms like database/sql/db, javascript/js, python/py, etc. (issue #10).
# Updated: 2026-02-25 — Improved tokenize() to strip non-alpha characters from
#   within tokens (not just edges), preventing code snippets from creating junk
#   domain names like "os.environ.get('key". Added _ALPHA_RE for robust cleaning.
# Created: 2026-02-22 — Replaces simple substring matching with token-based
# scoring. Provides tokenize() and relevance_score() used by all memory stores.

from __future__ import annotations

import re

# Keep only alphabetic characters — strips digits, punctuation, code artifacts
_ALPHA_RE = re.compile(r"[^a-z]+")

# Split on whitespace plus common identifier/path separators: / _ - .
_SPLIT_RE = re.compile(r"[\s/_.\\-]+")

# ---------------------------------------------------------------------------
# Synonym / alias groups for improved recall (issue #10)
# ---------------------------------------------------------------------------
# Each tuple is a group of related terms. When any member appears in a token
# set, all other members are added so that token-overlap can match synonyms.
# Keep this small and focused on common programming/tech terms.

_SYNONYM_GROUPS: list[tuple[str, ...]] = [
    ("database", "sql", "postgresql", "postgres", "mysql", "sqlite", "mongo", "mongodb"),
    ("javascript", "typescript"),
    ("python", "pip"),
    ("frontend", "client", "browser"),
    ("backend", "server"),
    ("api", "rest", "endpoint"),
    ("test", "testing", "pytest", "unittest"),
    ("deploy", "deployment", "shipping"),
    ("container", "docker", "kubernetes"),
    ("auth", "authentication", "login"),
    ("config", "configuration", "settings"),
    ("error", "exception", "bug"),
    ("async", "asynchronous", "await"),
    ("func", "function", "method"),
    ("repo", "repository", "git"),
    ("dependency", "dependencies", "package", "packages"),
    ("http", "https", "request", "response"),
    ("cli", "command", "terminal"),
]

# Build a lookup: token → frozenset of all synonyms (including itself)
_SYNONYM_MAP: dict[str, frozenset[str]] = {}
for _group in _SYNONYM_GROUPS:
    _fset = frozenset(_group)
    for _term in _group:
        # A term may appear in multiple groups — merge them
        if _term in _SYNONYM_MAP:
            _fset = _fset | _SYNONYM_MAP[_term]
    # Re-assign the merged set to every term in the merged group
    for _term in _fset:
        _SYNONYM_MAP[_term] = _fset


def _expand_synonyms(tokens: set[str]) -> set[str]:
    """Expand a token set with synonyms from ``_SYNONYM_MAP``.

    For each token that appears in the synonym map, all members of its
    synonym group are added to the returned set.  Tokens without synonyms
    pass through unchanged.

    Args:
        tokens: The original token set.

    Returns:
        A new set containing the originals plus any synonym expansions.
    """
    expanded = set(tokens)
    for tok in tokens:
        group = _SYNONYM_MAP.get(tok)
        if group is not None:
            expanded |= group
    return expanded


def tokenize(text: str) -> set[str]:
    """Split text into lowercase alphabetic tokens, removing short words.

    Splits on whitespace **and** common separators (``/``, ``_``, ``-``,
    ``.``) so that file paths like ``app/routes/handler.py`` and snake_case
    identifiers like ``user_session_token`` produce individual searchable
    tokens.

    Strips all non-alphabetic characters (punctuation, digits, code syntax)
    and discards any resulting token shorter than 3 characters.

    Args:
        text: The input string to tokenize.

    Returns:
        A set of cleaned, lowercased alpha-only tokens with len >= 3.
    """
    # Split on whitespace + path/identifier separators, then strip non-alpha
    words = (_ALPHA_RE.sub("", w) for w in _SPLIT_RE.split(text.lower()))
    return {w for w in words if len(w) >= 3}


def relevance_score(query: str, content: str) -> float:
    """Score 0.0-1.0 based on token overlap between query and content.

    Measures what fraction of query tokens appear in the content, after
    expanding both sides with programming-domain synonyms.  A score of
    1.0 means every query token (or a synonym) was found in the content.
    A score of 0.0 means no overlap at all.

    Args:
        query: The search query string.
        content: The content string to score against.

    Returns:
        Float between 0.0 and 1.0 representing relevance.
    """
    query_tokens = tokenize(query)
    content_tokens = tokenize(content)
    if not query_tokens:
        return 0.0
    expanded_content = _expand_synonyms(content_tokens)
    overlap = query_tokens & expanded_content
    return len(overlap) / len(query_tokens)
