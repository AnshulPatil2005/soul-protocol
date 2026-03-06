# embeddings/similarity.py — Re-exports similarity functions from core.
# Updated: v0.4.0 — The canonical definitions live in core/embeddings/similarity.py.

from soul_protocol.core.embeddings.similarity import (
    cosine_similarity,
    dot_product,
    euclidean_distance,
)

__all__ = ["cosine_similarity", "euclidean_distance", "dot_product"]
