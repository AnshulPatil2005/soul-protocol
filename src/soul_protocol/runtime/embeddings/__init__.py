# embeddings/__init__.py — Embedding subsystem for vector-based memory search.
# Updated: runtime restructure — fixed absolute import paths to soul_protocol.runtime.
# Created: 2026-03-06 — Exports EmbeddingProvider protocol, built-in embedders,
# similarity functions, and VectorSearchStrategy.

from __future__ import annotations

from soul_protocol.runtime.embeddings.hash_embedder import HashEmbedder
from soul_protocol.runtime.embeddings.protocol import EmbeddingProvider
from soul_protocol.runtime.embeddings.similarity import cosine_similarity, dot_product, euclidean_distance
from soul_protocol.runtime.embeddings.tfidf_embedder import TFIDFEmbedder
from soul_protocol.runtime.embeddings.vector_strategy import VectorSearchStrategy

__all__ = [
    "EmbeddingProvider",
    "HashEmbedder",
    "TFIDFEmbedder",
    "VectorSearchStrategy",
    "cosine_similarity",
    "euclidean_distance",
    "dot_product",
]
