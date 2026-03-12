# embeddings/hash_embedder.py — Deterministic hash-based embedder for testing.
# Created: 2026-03-06 — Uses character n-gram hashing to produce pseudo-embeddings.
# Not semantically meaningful but deterministic and fast, ideal for testing the
# embedding pipeline without external dependencies.

from __future__ import annotations

import hashlib
import math
import struct


class HashEmbedder:
    """Deterministic hash-based embedder for testing.

    Uses hash functions to create pseudo-embeddings from character n-grams.
    The output is NOT semantically meaningful — similar texts won't necessarily
    produce similar vectors. However, the same input always produces the same
    output, making this ideal for testing the embedding pipeline.

    Args:
        dimensions: Size of the output vector. Default 64.
        ngram_size: Character n-gram size for hashing. Default 3.
    """

    def __init__(self, dimensions: int = 64, ngram_size: int = 3) -> None:
        self._dimensions = dimensions
        self._ngram_size = ngram_size

    @property
    def dimensions(self) -> int:
        """Dimensionality of the embedding vectors."""
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        """Embed a single text using character n-gram hashing.

        Creates a vector by:
        1. Extracting character n-grams from the lowercased text
        2. Hashing each n-gram to a bucket (dimension index)
        3. Accumulating hash-derived values into the vector
        4. L2-normalizing the result

        Args:
            text: The input text to embed.

        Returns:
            A normalized list of floats with length == self.dimensions.
        """
        vector = [0.0] * self._dimensions
        text_lower = text.lower().strip()

        if not text_lower:
            return vector

        # Extract character n-grams and hash them into buckets
        ngrams = self._extract_ngrams(text_lower)
        for ngram in ngrams:
            h = hashlib.md5(ngram.encode("utf-8")).digest()
            # Use first 4 bytes for bucket index, next 4 for value
            bucket = struct.unpack("<I", h[:4])[0] % self._dimensions
            value = struct.unpack("<i", h[4:8])[0] / (2**31)
            vector[bucket] += value

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts. Returns list of vectors."""
        return [self.embed(t) for t in texts]

    def _extract_ngrams(self, text: str) -> list[str]:
        """Extract character n-grams from text.

        Also includes whole words as additional features for slightly
        better bucket distribution.
        """
        ngrams: list[str] = []
        # Character n-grams
        for i in range(len(text) - self._ngram_size + 1):
            ngrams.append(text[i : i + self._ngram_size])
        # Whole words as bonus features
        words = text.split()
        ngrams.extend(words)
        return ngrams
