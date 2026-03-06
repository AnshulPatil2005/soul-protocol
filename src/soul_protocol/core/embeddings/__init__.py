# core/embeddings/__init__.py — Protocol-level embedding interfaces.
# Created: v0.4.0 — EmbeddingProvider protocol and similarity functions.
# These are part of the core protocol spec — no opinionated implementations.

from soul_protocol.core.embeddings.protocol import EmbeddingProvider
from soul_protocol.core.embeddings.similarity import cosine_similarity, dot_product, euclidean_distance

__all__ = [
    "EmbeddingProvider",
    "cosine_similarity",
    "euclidean_distance",
    "dot_product",
]
