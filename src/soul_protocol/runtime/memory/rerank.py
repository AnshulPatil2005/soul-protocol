# rerank.py — Smart memory reranking via lightweight LLM call.
# Created: 2026-04-01 — Uses CognitiveEngine to rerank candidate memories by
#   relevance to query context. Falls back to heuristic order on failure.

"""Smart memory reranking — uses a lightweight LLM call to select the most
relevant memories from a candidate set. Replaces heuristic-only ranking with
context-aware selection when a CognitiveEngine is available."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from soul_protocol.runtime.cognitive.engine import CognitiveEngine
    from soul_protocol.spec.memory import MemoryEntry

logger = logging.getLogger(__name__)

_RERANK_PROMPT = """\
Given this context, select the {limit} most relevant memories from the list below.
Return ONLY the memory numbers, comma-separated, most relevant first.
Example: 3,1,7,2,5

Context: {query}

Memories:
{candidates}

Selected (top {limit}):"""


async def rerank_memories(
    candidates: list[MemoryEntry],
    query: str,
    engine: CognitiveEngine,
    limit: int = 5,
) -> list[MemoryEntry]:
    """Rerank candidate memories using an LLM call.

    Args:
        candidates: Pre-filtered memories from heuristic recall (typically 3x limit)
        query: The user's query / current context
        engine: CognitiveEngine for the LLM call
        limit: How many memories to return

    Returns:
        Top-N memories ranked by LLM relevance judgment.
        Falls back to original order if LLM call fails.
    """
    if len(candidates) <= limit:
        return candidates

    # Format candidates as numbered list
    formatted = []
    for i, mem in enumerate(candidates, 1):
        # Truncate long memories to keep prompt small
        content = mem.content[:200].replace("\n", " ")
        formatted.append(f"{i}. [{mem.layer}] {content}")

    candidates_text = "\n".join(formatted)

    prompt = _RERANK_PROMPT.format(
        limit=limit,
        query=query[:500],  # Cap query length
        candidates=candidates_text,
    )

    try:
        response = await engine.think(prompt)
        # Parse comma-separated indices
        indices = _parse_indices(response, max_index=len(candidates))
        if indices:
            reranked = [candidates[i - 1] for i in indices[:limit]]
            logger.debug(
                "Smart rerank selected %d/%d memories",
                len(reranked),
                len(candidates),
            )
            return reranked
    except Exception as e:
        logger.warning(
            "Smart rerank failed, falling back to heuristic order: %s", e
        )

    # Fallback: return first N from heuristic ordering
    return candidates[:limit]


def _parse_indices(response: str, max_index: int) -> list[int]:
    """Parse comma-separated indices from LLM response. Robust to formatting noise."""
    numbers = re.findall(r"\d+", response)
    indices: list[int] = []
    seen: set[int] = set()
    for n in numbers:
        idx = int(n)
        if 1 <= idx <= max_index and idx not in seen:
            indices.append(idx)
            seen.add(idx)
    return indices
