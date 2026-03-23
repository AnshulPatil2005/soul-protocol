# embeddings/ollama_embeddings.py — Ollama embedding provider.
# Created: 2026-03-22 — Local semantic embeddings via Ollama.
# Default model: nomic-embed-text. No API key needed — fully local.
# Configurable base_url for custom Ollama instances.

from __future__ import annotations

import math


class OllamaEmbeddingProvider:
    """Embedding provider using a local Ollama instance.

    Produces semantic embeddings by calling a locally-running Ollama server.
    No API key required — everything runs on your machine.

    Args:
        model: Ollama model name. Default: ``nomic-embed-text``.
        base_url: Ollama server URL. Default: ``http://localhost:11434``
            (Ollama's default).
        dimensions: Expected vector dimensionality. If ``None``, determined
            automatically from the first embed() call.
    """

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        dimensions: int | None = None,
    ) -> None:
        self._model = model
        self._base_url = base_url
        self._client: object | None = None
        self._dimensions: int | None = dimensions

    def _get_client(self) -> object:
        """Lazily create the Ollama client on first use."""
        if self._client is not None:
            return self._client

        try:
            from ollama import Client
        except ImportError:
            raise ImportError(
                "ollama is required for OllamaEmbeddingProvider. "
                "Install it with: pip install 'soul-protocol[embeddings-ollama]'"
            ) from None

        self._client = Client(host=self._base_url)
        return self._client

    @property
    def dimensions(self) -> int:
        """Dimensionality of the embedding vectors."""
        if self._dimensions is not None:
            return self._dimensions
        # Probe to learn dimensionality
        vec = self._embed_single("probe")
        self._dimensions = len(vec)
        return self._dimensions

    def _embed_single(self, text: str) -> list[float]:
        """Embed a single text via the Ollama API.

        Args:
            text: The input text to embed.

        Returns:
            Raw embedding vector as a list of floats.
        """
        client = self._get_client()
        response = client.embed(model=self._model, input=text)

        # ollama.embed returns {"embeddings": [[...]]}
        embedding = response["embeddings"][0]

        if self._dimensions is None:
            self._dimensions = len(embedding)

        return list(embedding)

    def _normalize(self, vector: list[float]) -> list[float]:
        """L2-normalize a vector."""
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            return [x / norm for x in vector]
        return vector

    def embed(self, text: str) -> list[float]:
        """Embed a single text string via Ollama.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats with length == self.dimensions.
        """
        return self._embed_single(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts.

        Ollama processes each text individually, so this iterates
        over the inputs. Keeps the interface consistent with batch-capable
        providers.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        if not texts:
            return []

        # Use Ollama's batch support if available (embed with list input)
        client = self._get_client()
        try:
            response = client.embed(model=self._model, input=texts)
            embeddings = response["embeddings"]
            if self._dimensions is None and embeddings:
                self._dimensions = len(embeddings[0])
            return [list(e) for e in embeddings]
        except (TypeError, KeyError):
            # Fallback: embed one by one
            return [self._embed_single(t) for t in texts]
