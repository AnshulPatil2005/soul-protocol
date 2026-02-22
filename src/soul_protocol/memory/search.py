# memory/search.py — Token-overlap relevance scoring for memory search.
# Created: 2026-02-22 — Replaces simple substring matching with token-based
# scoring. Provides tokenize() and relevance_score() used by all memory stores.

from __future__ import annotations


def tokenize(text: str) -> set[str]:
    """Split text into lowercase tokens, removing short words.

    Strips common punctuation from each word and discards any token
    shorter than 3 characters (articles, prepositions, etc.).

    Args:
        text: The input string to tokenize.

    Returns:
        A set of cleaned, lowercased tokens with len >= 3.
    """
    words = text.lower().split()
    return {w.strip(".,!?;:'\"()[]{}") for w in words if len(w) >= 3}


def relevance_score(query: str, content: str) -> float:
    """Score 0.0-1.0 based on token overlap between query and content.

    Measures what fraction of query tokens appear in the content.
    A score of 1.0 means every query token was found in the content.
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
    overlap = query_tokens & content_tokens
    return len(overlap) / len(query_tokens)
