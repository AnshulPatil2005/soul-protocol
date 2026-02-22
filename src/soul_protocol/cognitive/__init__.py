# cognitive/__init__.py — Public exports for the cognitive engine subsystem.
# Updated: v0.2.1 — Removed CognitiveProcessor and _parse_json from public API.
#   Only CognitiveEngine and HeuristicEngine are consumer-facing.

from __future__ import annotations

from soul_protocol.cognitive.engine import (
    CognitiveEngine,
    HeuristicEngine,
)

__all__ = [
    "CognitiveEngine",
    "HeuristicEngine",
]
