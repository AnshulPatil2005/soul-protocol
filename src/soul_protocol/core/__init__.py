# core/__init__.py — Protocol-level primitives for the Soul Protocol spec.
# Created: v0.4.0 — Core embedding interfaces (EmbeddingProvider, similarity functions).

from soul_protocol.core.embeddings import (
    EmbeddingProvider,
    cosine_similarity,
    dot_product,
    euclidean_distance,
)

__all__ = [
    "EmbeddingProvider",
    "cosine_similarity",
    "euclidean_distance",
    "dot_product",
]
