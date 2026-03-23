# adapters/anthropic.py — AnthropicEngine: CognitiveEngine backed by Anthropic's Claude.
# Created: feat/cognitive-adapters — optional adapter; requires `pip install soul-protocol[anthropic]`.
#   Soft import — raises a clear ImportError only when the class is instantiated, not on module load.

from __future__ import annotations

import os


class AnthropicEngine:
    """CognitiveEngine backed by Anthropic's Claude API.

    Usage::

        from soul_protocol.runtime.cognitive.adapters import AnthropicEngine
        from soul_protocol import Soul

        soul = await Soul.birth(name="Aria", engine=AnthropicEngine())

    Requires ``pip install soul-protocol[anthropic]`` (anthropic>=0.40.0).
    The API key is read from the ``ANTHROPIC_API_KEY`` environment variable by default.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-haiku-4-5-20251001",
    ) -> None:
        try:
            import anthropic  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "AnthropicEngine requires the 'anthropic' package. "
                "Install it with: pip install soul-protocol[anthropic]"
            ) from exc

        import anthropic as _anthropic

        self._model = model
        self._client = _anthropic.AsyncAnthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
        )

    async def think(self, prompt: str) -> str:
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        # Extract text from the first content block
        block = message.content[0]
        if hasattr(block, "text"):
            return block.text
        return str(block)
