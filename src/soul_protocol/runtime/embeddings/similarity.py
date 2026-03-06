# embeddings/similarity.py — Re-exports similarity functions from spec.
# Updated: v0.4.0 — The canonical definitions live in spec/embeddings/similarity.py.
# Updated: runtime restructure — import path changed from core → spec.

from soul_protocol.spec.embeddings.similarity import (
    cosine_similarity,
    dot_product,
    euclidean_distance,
)

__all__ = ["cosine_similarity", "euclidean_distance", "dot_product"]
