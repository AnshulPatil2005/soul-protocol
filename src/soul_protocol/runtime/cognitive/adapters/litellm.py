# adapters/litellm.py — LiteLLMEngine: CognitiveEngine backed by LiteLLM (100+ providers).
# Created: feat/cognitive-adapters — optional adapter; requires `pip install soul-protocol[litellm]`.
#   Model format: "anthropic/claude-haiku-4-5-20251001", "openai/gpt-4o-mini", "ollama/llama3.2".
#   Soft import — raises only at instantiation time, not on module load.

from __future__ import annotations

from typing import Any


class LiteLLMEngine:
    """CognitiveEngine backed by LiteLLM, covering 100+ LLM providers.

    LiteLLM provides a unified interface over OpenAI, Anthropic, Cohere,
    Ollama, Bedrock, Vertex, and many more. Use this adapter when you want
    a single engine that can route to any provider.

    Usage::

        from soul_protocol.runtime.cognitive.adapters import LiteLLMEngine
        from soul_protocol import Soul

        # Anthropic via LiteLLM
        soul = await Soul.birth(
            name="Aria",
            engine=LiteLLMEngine(model="anthropic/claude-haiku-4-5-20251001"),
        )

        # Local Ollama via LiteLLM
        soul = await Soul.birth(
            name="Aria",
            engine=LiteLLMEngine(model="ollama/llama3.2"),
        )

    Requires ``pip install soul-protocol[litellm]`` (litellm>=1.0.0).
    """

    def __init__(self, model: str, **kwargs: Any) -> None:
        try:
            import litellm  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "LiteLLMEngine requires the 'litellm' package. "
                "Install it with: pip install soul-protocol[litellm]"
            ) from exc

        self._model = model
        self._kwargs = kwargs

    async def think(self, prompt: str) -> str:
        import litellm

        response = await litellm.acompletion(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            **self._kwargs,
        )
        content = response.choices[0].message.content
        return content or ""
