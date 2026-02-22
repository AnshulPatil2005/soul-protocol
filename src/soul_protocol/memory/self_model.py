# memory/self_model.py — Klein's self-concept model for digital souls.
# Created: v0.2.0 — The soul learns who it is from accumulated experience.
#   Tracks self-images (domain-specific identity facets) and relationship notes.
#   Heuristic domain detection from extracted facts and interaction content.

from __future__ import annotations

from soul_protocol.memory.search import tokenize
from soul_protocol.types import Interaction, MemoryEntry, SelfImage


# ---------------------------------------------------------------------------
# Domain detection: keyword → self-image domain mapping
# ---------------------------------------------------------------------------

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "technical_helper": [
        "python", "javascript", "code", "programming", "debug", "error",
        "api", "database", "server", "deploy", "git", "docker",
        "algorithm", "function", "class", "variable", "testing",
        "fastapi", "django", "react", "typescript", "rust",
    ],
    "creative_writer": [
        "write", "story", "poem", "creative", "fiction", "narrative",
        "character", "plot", "blog", "essay", "article", "content",
        "copywriting", "draft", "edit", "prose",
    ],
    "knowledge_guide": [
        "explain", "teach", "learn", "understand", "concept", "theory",
        "research", "study", "science", "history", "philosophy",
        "education", "tutorial", "guide", "documentation",
    ],
    "problem_solver": [
        "solve", "fix", "issue", "problem", "solution", "help",
        "troubleshoot", "diagnose", "analyze", "investigate",
        "debug", "resolve", "broken",
    ],
    "creative_collaborator": [
        "brainstorm", "idea", "design", "prototype", "sketch",
        "innovation", "experiment", "iterate", "collaborate",
        "vision", "concept", "create",
    ],
    "emotional_companion": [
        "feel", "emotion", "support", "listen", "care", "empathy",
        "comfort", "friend", "companion", "talk", "vent", "advice",
        "stress", "anxious", "happy", "sad",
    ],
}


class SelfModelManager:
    """Tracks the soul's evolving self-concept (Klein's self-model).

    The soul learns who it is by observing what it does. Over time, patterns
    emerge: "I help with code a lot → I am a technical helper."

    This is not programmed — it's discovered from experience.
    """

    def __init__(self) -> None:
        self._self_images: dict[str, SelfImage] = {}
        self._relationship_notes: dict[str, str] = {}

    @property
    def self_images(self) -> dict[str, SelfImage]:
        """All self-images the soul has developed."""
        return dict(self._self_images)

    @property
    def relationship_notes(self) -> dict[str, str]:
        """What the soul knows about key people/entities."""
        return dict(self._relationship_notes)

    def update_from_interaction(
        self,
        interaction: Interaction,
        extracted_facts: list[MemoryEntry],
    ) -> None:
        """Update self-concept based on an observed interaction.

        Scans the interaction content and extracted facts for domain keywords.
        Each match increments the evidence for that self-image domain.

        Args:
            interaction: The interaction that was observed.
            extracted_facts: Facts extracted from this interaction.
        """
        combined = f"{interaction.user_input} {interaction.agent_output}"
        tokens = tokenize(combined)

        # Also include tokens from extracted facts
        for fact in extracted_facts:
            tokens |= tokenize(fact.content)

        # Score each domain by keyword matches
        for domain, keywords in DOMAIN_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in tokens)
            if matches > 0:
                self._update_domain(domain, matches)

        # Extract relationship notes from facts
        for fact in extracted_facts:
            content_lower = fact.content.lower()
            if "user's name is" in content_lower:
                name = fact.content.split("is")[-1].strip()
                self._relationship_notes["user"] = f"Name: {name}"
            elif "user works at" in content_lower:
                workplace = fact.content.split("at")[-1].strip()
                existing = self._relationship_notes.get("user", "")
                if "Works at" not in existing:
                    self._relationship_notes["user"] = (
                        f"{existing}; Works at: {workplace}" if existing else f"Works at: {workplace}"
                    )

    def _update_domain(self, domain: str, match_count: int) -> None:
        """Increment evidence for a self-image domain.

        Confidence grows with evidence but has diminishing returns —
        the soul becomes more certain over time but never fully certain.

        Args:
            domain: The self-image domain (e.g., "technical_helper").
            match_count: How many keyword matches were found.
        """
        if domain not in self._self_images:
            self._self_images[domain] = SelfImage(
                domain=domain,
                confidence=0.1,
                evidence_count=0,
            )

        img = self._self_images[domain]
        img.evidence_count += match_count

        # Confidence formula: diminishing returns curve
        # Starts at 0.1, approaches 0.95 as evidence grows
        img.confidence = min(0.95, 0.1 + 0.85 * (1 - 1 / (1 + img.evidence_count * 0.1)))

    def get_active_self_images(self, limit: int = 3) -> list[SelfImage]:
        """Return the top self-images by confidence.

        Args:
            limit: Maximum number of self-images to return.

        Returns:
            List of SelfImage sorted by confidence descending.
        """
        images = sorted(
            self._self_images.values(),
            key=lambda img: (-img.confidence, -img.evidence_count),
        )
        return images[:limit]

    def to_dict(self) -> dict:
        """Serialize the self-model to a plain dict.

        Returns:
            Dict with self_images and relationship_notes.
        """
        return {
            "self_images": {
                domain: img.model_dump()
                for domain, img in self._self_images.items()
            },
            "relationship_notes": dict(self._relationship_notes),
        }

    @classmethod
    def from_dict(cls, data: dict) -> SelfModelManager:
        """Deserialize a self-model from a plain dict.

        Args:
            data: Dict as produced by to_dict().

        Returns:
            A fully reconstituted SelfModelManager.
        """
        manager = cls()

        for domain, img_data in data.get("self_images", {}).items():
            manager._self_images[domain] = SelfImage.model_validate(img_data)

        manager._relationship_notes = dict(data.get("relationship_notes", {}))

        return manager

    def to_prompt_fragment(self) -> str:
        """Generate a prompt fragment describing the soul's self-concept.

        Suitable for inclusion in system prompts.

        Returns:
            A human-readable string describing active self-images,
            or empty string if no self-images exist.
        """
        active = self.get_active_self_images(limit=3)
        if not active:
            return ""

        lines = ["## Self-Understanding", ""]
        for img in active:
            confidence_label = (
                "high" if img.confidence >= 0.7
                else "growing" if img.confidence >= 0.4
                else "emerging"
            )
            domain_display = img.domain.replace("_", " ")
            lines.append(
                f"- {domain_display} ({confidence_label} confidence, "
                f"{img.evidence_count} supporting interactions)"
            )

        return "\n".join(lines)
