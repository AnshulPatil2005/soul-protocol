# core/embeddings/protocol.py — EmbeddingProvider protocol for pluggable embedding backends.
# Created: v0.4.0 — Moved from embeddings/protocol.py to core/ as a protocol-level primitive.
# This is the canonical definition. The engine-level embeddings/protocol.py re-exports from here.

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Interface for any embedding backend.

    All embedding providers must implement this protocol to be usable
    with VectorSearchStrategy and other vector-based components.

    The protocol is runtime-checkable, so you can use isinstance() to
    verify compliance at runtime.
    """

    @property
    def dimensions(self) -> int:
        """Dimensionality of the embedding vectors."""
        ...

    def embed(self, text: str) -> list[float]:
        """Embed a single text string into a vector.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.
            Length must equal self.dimensions.
        """
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts into vectors.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors, one per input text.
            Each vector's length must equal self.dimensions.
        """
        ...
