# spec/embeddings/__init__.py — Protocol-level embedding interfaces.
# Created: v0.4.0 — EmbeddingProvider protocol and similarity functions.
# These are part of the spec protocol layer — no opinionated implementations.
# Updated: Renamed core/ -> spec/, switched to relative imports.

from .protocol import EmbeddingProvider
from .similarity import cosine_similarity, dot_product, euclidean_distance

__all__ = [
    "EmbeddingProvider",
    "cosine_similarity",
    "euclidean_distance",
    "dot_product",
]
