# embeddings/tfidf_embedder.py — TF-IDF based embedder using only stdlib.
# Created: 2026-03-06 — Builds vocabulary from a corpus and creates sparse-ish
# vectors based on term frequency-inverse document frequency. Better than hash
# for actual similarity but requires fitting on a corpus first.

from __future__ import annotations

import math
import re


def _tokenize_text(text: str) -> list[str]:
    """Split text into lowercase tokens, keeping only alphanumeric words >= 2 chars."""
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 2]


class TFIDFEmbedder:
    """Simple TF-IDF based embedder using only stdlib.

    Builds a vocabulary from stored texts and creates sparse-ish vectors
    based on term frequency-inverse document frequency weighting.

    Unlike HashEmbedder, this produces semantically meaningful vectors —
    texts with similar word distributions will have similar embeddings.
    However, it requires calling fit() on a corpus before embedding.

    Args:
        dimensions: Maximum vocabulary size / vector dimensionality. Default 128.
    """

    def __init__(self, dimensions: int = 128) -> None:
        self._dimensions = dimensions
        self._vocabulary: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._doc_count: int = 0
        self._fitted = False

    @property
    def dimensions(self) -> int:
        """Dimensionality of the embedding vectors."""
        return self._dimensions

    @property
    def fitted(self) -> bool:
        """Whether the embedder has been fit on a corpus."""
        return self._fitted

    def fit(self, texts: list[str]) -> None:
        """Build vocabulary and IDF scores from a corpus.

        Selects the top `dimensions` terms by document frequency to form
        the vocabulary. Computes IDF as log(N / df) for each term.

        Args:
            texts: List of documents to build the vocabulary from.
        """
        self._doc_count = len(texts)
        if self._doc_count == 0:
            self._fitted = True
            return

        # Count document frequency for each term
        doc_freq: dict[str, int] = {}
        for text in texts:
            unique_tokens = set(_tokenize_text(text))
            for token in unique_tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        # Select top terms by document frequency, capped at dimensions
        sorted_terms = sorted(doc_freq.items(), key=lambda x: (-x[1], x[0]))
        top_terms = sorted_terms[: self._dimensions]

        # Build vocabulary mapping: term -> index
        self._vocabulary = {term: idx for idx, (term, _) in enumerate(top_terms)}

        # Compute IDF: log(N / df) with smoothing to avoid division by zero
        self._idf = {}
        for term, idx in self._vocabulary.items():
            df = doc_freq[term]
            self._idf[term] = math.log((1 + self._doc_count) / (1 + df)) + 1.0

        self._fitted = True

    def embed(self, text: str) -> list[float]:
        """Embed a single text using TF-IDF weighting.

        If not fitted, returns a zero vector. Terms not in the vocabulary
        are ignored.

        Args:
            text: The input text to embed.

        Returns:
            A normalized list of floats with length == self.dimensions.
        """
        vector = [0.0] * self._dimensions

        if not self._fitted or not self._vocabulary:
            return vector

        tokens = _tokenize_text(text)
        if not tokens:
            return vector

        # Compute term frequency
        tf: dict[str, float] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1.0

        # Normalize TF by document length
        max_tf = max(tf.values()) if tf else 1.0
        for token in tf:
            tf[token] = tf[token] / max_tf

        # Build TF-IDF vector
        for token, freq in tf.items():
            if token in self._vocabulary:
                idx = self._vocabulary[token]
                idf = self._idf.get(token, 1.0)
                vector[idx] = freq * idf

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts. Returns list of vectors."""
        return [self.embed(t) for t in texts]
