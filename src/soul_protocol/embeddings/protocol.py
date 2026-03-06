# embeddings/protocol.py — Re-exports EmbeddingProvider from core for convenience.
# Updated: v0.4.0 — The canonical definition lives in core/embeddings/protocol.py.

from soul_protocol.core.embeddings.protocol import EmbeddingProvider

__all__ = ["EmbeddingProvider"]
