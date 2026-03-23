# spec/learning.py — LearningEvent model for formalized lessons from experience.
# Created: 2026-03-22 — Thin spec model (Pydantic only). Captures lessons extracted
#   from success/failure during evaluation. Links to interactions, domains, and skills.
#   Tracks confidence and applied_count for reinforcement learning patterns.
# Added to dev: fix/add-learning-spec-module — module was referenced by spec/__init__.py
#   (introduced in feat/memory-visibility-templates) but the file itself lives in
#   feat/graph-learning-events (PR #115). Adding it here to unblock the import.

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class LearningEvent(BaseModel):
    """A formalized lesson learned from experience.

    Not just what happened (episodic) or what it knows (semantic),
    but insights extracted from evaluating success and failure.
    Stored in procedural memory and linked to skills for XP grants.
    """

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    trigger_interaction_id: str | None = None  # What caused this learning
    lesson: str  # The actual insight
    domain: str = "general"  # Maps to evaluation rubric domains
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    skill_id: str | None = None  # Links to skill for XP
    evaluation_score: float | None = None  # From Evaluator
    created_at: datetime = Field(default_factory=datetime.now)
    applied_count: int = 0  # How many times this lesson was recalled and used

    def apply(self) -> None:
        """Record that this lesson was recalled and applied."""
        self.applied_count += 1

    def reinforce(self, amount: float = 0.1) -> None:
        """Increase confidence when the lesson proves useful.

        Confidence is capped at 1.0.
        """
        self.confidence = min(1.0, self.confidence + amount)

    def weaken(self, amount: float = 0.1) -> None:
        """Decrease confidence when the lesson proves wrong.

        Confidence is floored at 0.0.
        """
        self.confidence = max(0.0, self.confidence - amount)
