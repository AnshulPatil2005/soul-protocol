# adapters/openai.py — OpenAIEngine: CognitiveEngine backed by OpenAI (or any OpenAI-compatible API).
# Created: feat/cognitive-adapters — optional adapter; requires `pip install soul-protocol[openai]`.
#   The base_url parameter makes this compatible with local models (Ollama OpenAI mode, vLLM, etc.)
#   Soft import — raises only at instantiation time, not on module load.

from __future__ import annotations

import os


class OpenAIEngine:
    """CognitiveEngine backed by OpenAI (or any OpenAI-compatible endpoint).

    Usage::

        from soul_protocol.runtime.cognitive.adapters import OpenAIEngine
        from soul_protocol import Soul

        # OpenAI
        soul = await Soul.birth(name="Aria", engine=OpenAIEngine())

        # Local Ollama via OpenAI-compatible endpoint
        engine = OpenAIEngine(
            model="llama3.2",
            base_url="http://localhost:11434/v1",
            api_key="ollama",  # Ollama ignores this but the client requires a value
        )

    Requires ``pip install soul-protocol[openai]`` (openai>=1.0.0).
    The API key is read from the ``OPENAI_API_KEY`` environment variable by default.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
    ) -> None:
        try:
            import openai  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "OpenAIEngine requires the 'openai' package. "
                "Install it with: pip install soul-protocol[openai]"
            ) from exc

        import openai as _openai

        self._model = model
        client_kwargs: dict = {
            "api_key": api_key or os.environ.get("OPENAI_API_KEY"),
        }
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = _openai.AsyncOpenAI(**client_kwargs)

    async def think(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""
