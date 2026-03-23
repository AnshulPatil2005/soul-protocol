# adapters/_callable.py — CallableEngine: wraps any sync or async callable as a CognitiveEngine.
# Created: feat/cognitive-adapters — internal adapter so app builders can pass a plain lambda
#   or async function to Soul.birth(engine=...) instead of implementing the full protocol.

from __future__ import annotations

import asyncio
from collections.abc import Callable


class CallableEngine:
    """Wraps a plain callable (sync or async) as a CognitiveEngine.

    Lets app builders pass a simple function to Soul without implementing
    the full CognitiveEngine protocol:

        soul = await Soul.birth(name="Aria", engine=lambda p: my_llm.complete(p))

    Both sync and async callables are supported.
    """

    def __init__(self, fn: Callable) -> None:
        self._fn = fn
        self._is_async = asyncio.iscoroutinefunction(fn)

    async def think(self, prompt: str) -> str:
        if self._is_async:
            return await self._fn(prompt)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fn, prompt)
