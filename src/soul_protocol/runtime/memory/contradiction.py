# memory/contradiction.py — Semantic contradiction detection for memory pipeline.
# Created: v0.4.0 — Heuristic and LLM-powered contradiction detection.
#   Heuristic mode uses embedding similarity + negation patterns + entity-attribute
#   conflict detection. LLM mode delegates to CognitiveEngine for top-5 similar
#   memories. When contradiction detected, old memory is marked superseded=True.

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from soul_protocol.runtime.memory.dedup import _jaccard_similarity
from soul_protocol.runtime.types import MemoryEntry

if TYPE_CHECKING:
    from soul_protocol.runtime.cognitive.engine import CognitiveEngine

logger = logging.getLogger(__name__)

# Negation patterns: words/phrases that flip meaning
_NEGATION_PAIRS: list[tuple[re.Pattern[str], re.Pattern[str]]] = [
    (re.compile(r"\bis\b", re.I), re.compile(r"\bis not\b|\bisn'?t\b", re.I)),
    (re.compile(r"\blikes?\b|\bloves?\b|\bprefers?\b", re.I),
     re.compile(r"\bhates?\b|\bdislikes?\b|\bdoesn'?t like\b", re.I)),
    (re.compile(r"\bworks? (?:at|for)\b", re.I),
     re.compile(r"\bleft\b|\bquit\b|\bno longer works?\b", re.I)),
    (re.compile(r"\bcan\b", re.I), re.compile(r"\bcan(?:no|'?)t\b", re.I)),
    (re.compile(r"\bdoes\b", re.I), re.compile(r"\bdoes(?:n'?t| not)\b", re.I)),
    (re.compile(r"\bhas\b", re.I), re.compile(r"\bhas(?:n'?t| not)\b|\bno longer has\b", re.I)),
    (re.compile(r"\bwill\b", re.I), re.compile(r"\bwon'?t\b|\bwill not\b", re.I)),
    (re.compile(r"\btrue\b", re.I), re.compile(r"\bfalse\b", re.I)),
    (re.compile(r"\byes\b", re.I), re.compile(r"\bno\b", re.I)),
]

# Entity-attribute patterns for extracting "X is Y" style assertions
_ENTITY_ATTR_RE = re.compile(
    r"(?:user(?:'s)?|their|the)\s+(\w[\w\s]{0,20}?)\s+is\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)


class ContradictionResult:
    """Result of a contradiction check between two memories."""

    __slots__ = ("is_contradiction", "old_memory_id", "new_content", "reason", "confidence")

    def __init__(
        self,
        is_contradiction: bool,
        old_memory_id: str = "",
        new_content: str = "",
        reason: str = "",
        confidence: float = 0.0,
    ) -> None:
        self.is_contradiction = is_contradiction
        self.old_memory_id = old_memory_id
        self.new_content = new_content
        self.reason = reason
        self.confidence = confidence


class ContradictionDetector:
    """Detects semantic contradictions between new and existing memories.

    Two modes:
    - Heuristic (no LLM): Uses token similarity to find similar memories,
      then checks for negation patterns or different values for the same
      entity-attribute pairs.
    - LLM mode: Asks CognitiveEngine to evaluate top-5 similar memories
      for contradictions.
    """

    def __init__(
        self,
        engine: CognitiveEngine | None = None,
        similarity_threshold: float = 0.3,
    ) -> None:
        """Initialize the contradiction detector.

        Args:
            engine: Optional CognitiveEngine for LLM-powered detection.
                When None, uses heuristic mode only.
            similarity_threshold: Minimum Jaccard similarity to consider
                two memories as potential contradictions (default 0.3).
        """
        self._engine = engine
        self._similarity_threshold = similarity_threshold

    def _find_similar(
        self, content: str, candidates: list[MemoryEntry], top_k: int = 5
    ) -> list[tuple[float, MemoryEntry]]:
        """Find the top-k most similar non-superseded memories."""
        scored: list[tuple[float, MemoryEntry]] = []
        for entry in candidates:
            if entry.superseded:
                continue
            if entry.superseded_by is not None:
                continue
            sim = _jaccard_similarity(content, entry.content)
            if sim >= self._similarity_threshold:
                scored.append((sim, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]

    def _check_negation(self, content_a: str, content_b: str) -> tuple[bool, str]:
        """Check if two pieces of content contain negation-flipped statements.

        Returns (is_negated, reason).
        """
        for pos_pattern, neg_pattern in _NEGATION_PAIRS:
            a_has_pos = bool(pos_pattern.search(content_a))
            a_has_neg = bool(neg_pattern.search(content_a))
            b_has_pos = bool(pos_pattern.search(content_b))
            b_has_neg = bool(neg_pattern.search(content_b))

            # One has positive form (without negation), other has negated form.
            # Note: the negated form may also match the positive pattern (e.g.,
            # "is not" contains "is"), so we check neg first as the more specific match.
            a_is_negated = a_has_neg
            b_is_negated = b_has_neg
            a_is_positive = a_has_pos and not a_has_neg
            b_is_positive = b_has_pos and not b_has_neg

            if a_is_positive and b_is_negated:
                return True, f"Negation detected: '{pos_pattern.pattern}' vs '{neg_pattern.pattern}'"
            if b_is_positive and a_is_negated:
                return True, f"Negation detected: '{pos_pattern.pattern}' vs '{neg_pattern.pattern}'"
        return False, ""

    def _check_entity_attribute_conflict(
        self, content_a: str, content_b: str
    ) -> tuple[bool, str]:
        """Check if two contents assert different values for the same entity attribute.

        E.g., "User's language is Python" vs "User's language is Rust".
        """
        attrs_a = _ENTITY_ATTR_RE.findall(content_a)
        attrs_b = _ENTITY_ATTR_RE.findall(content_b)

        for attr_a, val_a in attrs_a:
            attr_a_norm = attr_a.strip().lower()
            val_a_norm = val_a.strip().lower()
            for attr_b, val_b in attrs_b:
                attr_b_norm = attr_b.strip().lower()
                val_b_norm = val_b.strip().lower()
                if attr_a_norm == attr_b_norm and val_a_norm != val_b_norm:
                    return True, (
                        f"Entity-attribute conflict: '{attr_a_norm}' "
                        f"was '{val_a_norm}', now '{val_b_norm}'"
                    )
        return False, ""

    async def detect_heuristic(
        self, new_content: str, existing: list[MemoryEntry]
    ) -> list[ContradictionResult]:
        """Detect contradictions using heuristic methods (no LLM).

        Finds similar memories and checks for negation patterns or
        entity-attribute conflicts.

        Args:
            new_content: The content of the new memory to check.
            existing: List of existing memories to compare against.

        Returns:
            List of ContradictionResult for each detected contradiction.
        """
        similar = self._find_similar(new_content, existing)
        results: list[ContradictionResult] = []

        for sim_score, entry in similar:
            # Check negation
            is_neg, neg_reason = self._check_negation(new_content, entry.content)
            if is_neg:
                results.append(ContradictionResult(
                    is_contradiction=True,
                    old_memory_id=entry.id,
                    new_content=new_content,
                    reason=neg_reason,
                    confidence=min(sim_score + 0.2, 1.0),
                ))
                continue

            # Check entity-attribute conflict
            is_conflict, conflict_reason = self._check_entity_attribute_conflict(
                new_content, entry.content
            )
            if is_conflict:
                results.append(ContradictionResult(
                    is_contradiction=True,
                    old_memory_id=entry.id,
                    new_content=new_content,
                    reason=conflict_reason,
                    confidence=min(sim_score + 0.1, 1.0),
                ))

        return results

    async def detect_llm(
        self, new_content: str, existing: list[MemoryEntry]
    ) -> list[ContradictionResult]:
        """Detect contradictions using LLM (CognitiveEngine).

        Sends the top-5 similar memories to the engine and asks it to
        identify contradictions.

        Args:
            new_content: The content of the new memory to check.
            existing: List of existing memories to compare against.

        Returns:
            List of ContradictionResult for each detected contradiction.

        Raises:
            RuntimeError: If no CognitiveEngine is configured.
        """
        if self._engine is None:
            raise RuntimeError("LLM mode requires a CognitiveEngine")

        similar = self._find_similar(new_content, existing)
        if not similar:
            return []

        # Build prompt for the engine
        memories_text = "\n".join(
            f"[{i+1}] (id={entry.id}) {entry.content}"
            for i, (_, entry) in enumerate(similar)
        )
        prompt = (
            f"New memory: \"{new_content}\"\n\n"
            f"Existing memories:\n{memories_text}\n\n"
            "Which existing memories (if any) does the new memory contradict? "
            "A contradiction means the new information directly conflicts with "
            "or replaces the old information. Respond with ONLY the numbers "
            "of contradicted memories (e.g., '1, 3') or 'none' if no contradictions."
        )

        try:
            response = await self._engine.think(prompt)
            response_lower = response.strip().lower()

            if response_lower == "none" or not response_lower:
                return []

            # Parse the response for memory indices
            results: list[ContradictionResult] = []
            for match in re.finditer(r"\d+", response):
                idx = int(match.group()) - 1
                if 0 <= idx < len(similar):
                    sim_score, entry = similar[idx]
                    results.append(ContradictionResult(
                        is_contradiction=True,
                        old_memory_id=entry.id,
                        new_content=new_content,
                        reason=f"LLM detected contradiction: {response.strip()}",
                        confidence=min(sim_score + 0.3, 1.0),
                    ))
            return results
        except Exception:
            logger.warning("LLM contradiction detection failed, falling back to heuristic")
            return await self.detect_heuristic(new_content, existing)

    async def detect(
        self, new_content: str, existing: list[MemoryEntry]
    ) -> list[ContradictionResult]:
        """Detect contradictions using the best available method.

        Uses LLM mode if a CognitiveEngine is available, otherwise
        falls back to heuristic detection.

        Args:
            new_content: The content of the new memory to check.
            existing: List of existing memories to compare against.

        Returns:
            List of ContradictionResult for each detected contradiction.
        """
        if self._engine is not None:
            return await self.detect_llm(new_content, existing)
        return await self.detect_heuristic(new_content, existing)
