# embeddings/__init__.py — Embedding subsystem for vector-based memory search.
# Created: 2026-03-06 — Exports EmbeddingProvider protocol, built-in embedders,
# similarity functions, and VectorSearchStrategy.

from __future__ import annotations

from soul_protocol.embeddings.hash_embedder import HashEmbedder
from soul_protocol.embeddings.protocol import EmbeddingProvider
from soul_protocol.embeddings.similarity import cosine_similarity, dot_product, euclidean_distance
from soul_protocol.embeddings.tfidf_embedder import TFIDFEmbedder
from soul_protocol.embeddings.vector_strategy import VectorSearchStrategy

__all__ = [
    "EmbeddingProvider",
    "HashEmbedder",
    "TFIDFEmbedder",
    "VectorSearchStrategy",
    "cosine_similarity",
    "euclidean_distance",
    "dot_product",
]
