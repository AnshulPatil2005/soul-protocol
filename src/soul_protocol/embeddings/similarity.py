# embeddings/similarity.py — Vector similarity functions using only stdlib.
# Created: 2026-03-06 — Provides cosine_similarity and euclidean_distance for
# comparing embedding vectors without requiring numpy.

from __future__ import annotations

import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Returns a value between -1.0 and 1.0, where 1.0 means identical
    direction, 0.0 means orthogonal, and -1.0 means opposite direction.

    For normalized vectors, this equals the dot product.

    Args:
        a: First vector.
        b: Second vector (must have same length as a).

    Returns:
        Cosine similarity score. Returns 0.0 if either vector has zero norm.
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def euclidean_distance(a: list[float], b: list[float]) -> float:
    """Compute Euclidean distance between two vectors.

    Returns a non-negative float. Smaller values mean more similar vectors.

    Args:
        a: First vector.
        b: Second vector (must have same length as a).

    Returns:
        Euclidean distance between the two vectors.
    """
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def dot_product(a: list[float], b: list[float]) -> float:
    """Compute dot product between two vectors.

    For normalized vectors, this equals cosine similarity.

    Args:
        a: First vector.
        b: Second vector (must have same length as a).

    Returns:
        Dot product of the two vectors.
    """
    return sum(x * y for x, y in zip(a, b))
