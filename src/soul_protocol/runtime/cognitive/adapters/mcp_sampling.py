# adapters/mcp_sampling.py — MCPSamplingEngine: routes cognitive tasks to the host LLM via MCP sampling.
# Created: feat/mcp-sampling-engine — when soul-protocol runs as an MCP server inside Claude Code
#   or Claude Desktop, this engine routes cognitive tasks back to the host LLM via MCP sampling.
#   No API key needed — the host LLM pays. Falls back to HeuristicEngine if sampling is not
#   supported by the client (e.g. in test environments, or older MCP clients).

from __future__ import annotations

import logging

from soul_protocol.runtime.cognitive.engine import HeuristicEngine

logger = logging.getLogger(__name__)


class MCPSamplingEngine:
    """CognitiveEngine that uses MCP host sampling (no API key needed).

    When soul-protocol runs as an MCP server inside Claude Code or Claude Desktop,
    this engine routes cognitive tasks back to the host LLM via MCP sampling.
    The host LLM (Claude, GPT-4, etc.) processes the prompt and returns the result —
    no separate API key or billing account required.

    Falls back to HeuristicEngine if:
    - The MCP client doesn't support sampling (raises NotImplementedError)
    - Any other error occurs during the sampling call
    - ctx is None (defensive mode for tests / non-MCP usage)

    Usage (inside an MCP tool handler)::

        @mcp.tool
        async def my_tool(ctx: Context) -> str:
            from soul_protocol.runtime.cognitive.adapters.mcp_sampling import MCPSamplingEngine
            engine = MCPSamplingEngine(ctx)
            result = await engine.think("[TASK:sentiment] Analyze: I love this")
            return result

    The context ``ctx`` is a ``fastmcp.Context`` instance injected by FastMCP into
    tool handlers that declare it via type annotation.
    """

    def __init__(self, ctx: object | None) -> None:
        """
        Args:
            ctx: A ``fastmcp.Context`` instance available inside MCP tool handlers.
                 Pass ``None`` to force immediate HeuristicEngine fallback (useful in tests).
        """
        self._ctx = ctx
        self._fallback = HeuristicEngine()

    async def think(self, prompt: str) -> str:
        """Route a cognitive prompt to the host LLM via MCP sampling.

        Sends the prompt to the MCP client (Claude Code, Claude Desktop, etc.)
        which executes it through the host LLM. If sampling fails for any reason,
        falls back to the built-in HeuristicEngine so the soul keeps working.

        Args:
            prompt: The cognitive prompt (e.g. ``[TASK:sentiment] Analyze: ...``).

        Returns:
            The LLM response text, or a heuristic fallback result.
        """
        if self._ctx is None:
            logger.debug("MCPSamplingEngine: no context, using heuristic fallback")
            return await self._fallback.think(prompt)

        try:
            result = await self._ctx.sample(prompt)  # type: ignore[union-attr]
            # SamplingResult has a .text attribute (str | None) and .result
            text = result.text if hasattr(result, "text") else str(result)
            if text is None:
                # text can be None for structured results — fall back to string repr
                text = str(result.result) if hasattr(result, "result") else ""
            return text
        except NotImplementedError:
            logger.debug(
                "MCPSamplingEngine: host does not support sampling, using heuristic fallback"
            )
            return await self._fallback.think(prompt)
        except Exception as exc:
            logger.warning(
                "MCPSamplingEngine: sampling failed (%s), using heuristic fallback",
                type(exc).__name__,
            )
            return await self._fallback.think(prompt)
