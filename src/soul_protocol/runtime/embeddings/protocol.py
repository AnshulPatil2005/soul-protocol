# embeddings/protocol.py — Re-exports EmbeddingProvider from spec for convenience.
# Updated: v0.4.0 — The canonical definition lives in spec/embeddings/protocol.py.
# Updated: runtime restructure — import path changed from core → spec.

from soul_protocol.spec.embeddings.protocol import EmbeddingProvider

__all__ = ["EmbeddingProvider"]
