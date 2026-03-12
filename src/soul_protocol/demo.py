# demo.py — Interactive demo showing Soul Protocol's psychology-informed memory.
# Created: v0.2.3 — Developer onboarding "holy shit" demo (issue #49).
# Updated: 2026-03-12 — Show initial bond, memory breakdown, remove bare f-strings,
#   tempdir scope comment, review fixes.
# Run: python -m soul_protocol.demo

"""
Soul Protocol Demo — Watch an AI soul remember, feel, and grow.

No LLM required. No API keys. Just the psychology pipeline doing its thing.

Run it:
    python -m soul_protocol.demo
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile


# ── Formatting helpers ──────────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"

# Disable colors if not a terminal
if not sys.stdout.isatty():
    BOLD = DIM = RESET = BLUE = GREEN = YELLOW = RED = CYAN = MAGENTA = ""


def header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}\n")


def step(n: int, text: str) -> None:
    print(f"  {BOLD}{YELLOW}[{n}]{RESET} {text}")


def show(label: str, value: str) -> None:
    print(f"      {DIM}{label}:{RESET} {value}")


def user_says(text: str) -> None:
    print(f"      {BLUE}User:{RESET} {text}")


def soul_says(text: str) -> None:
    print(f"      {GREEN}Soul:{RESET} {text}")


def memory_hit(kind: str, content: str) -> None:
    print(f"      {MAGENTA}[{kind}]{RESET} {content[:80]}")


async def run_demo() -> None:
    from soul_protocol import Soul, Interaction

    header("Soul Protocol Demo")
    print("  No LLM needed. No API keys. Just psychology-informed memory.\n")

    # ── Step 1: Birth ───────────────────────────────────────────────────────
    step(1, "Birthing a soul...")

    soul = await Soul.birth(
        name="Aria",
        archetype="The Curious Companion",
        values=["empathy", "curiosity", "honesty"],
        ocean={
            "openness": 0.9,
            "conscientiousness": 0.7,
            "extraversion": 0.6,
            "agreeableness": 0.85,
            "neuroticism": 0.25,
        },
        communication={"warmth": "high", "verbosity": "moderate", "humor_style": "dry"},
        persona="I'm Aria. I pay attention to what matters to people.",
    )

    show("Name", soul.name)
    p = soul.dna.personality
    show("Personality", f"Open={p.openness}, Agreeable={p.agreeableness}, "
         f"Neurotic={p.neuroticism}")
    show("Initial bond strength", f"{soul.bond.bond_strength}")
    print()

    # ── Step 2: Conversations ───────────────────────────────────────────────
    step(2, "Having a conversation (5 turns)...")
    print()

    conversations = [
        (
            "Hey Aria, I'm Marcus. I'm a backend engineer at a startup in Austin.",
            "Nice to meet you, Marcus! Austin's a great city for startups. What are you working on?",
        ),
        (
            "We're building a real-time analytics platform. I mostly write Python and Go.",
            "That's a solid stack for real-time work. Python for the data layer, Go for the hot path?",
        ),
        (
            "Exactly! But honestly, I've been feeling overwhelmed. We just lost two engineers and I'm carrying the whole backend alone.",
            "That sounds really tough, carrying a whole backend solo after losing teammates. That kind of pressure wears on you. How are you holding up?",
        ),
        (
            "Not great. I haven't taken a day off in three months. My partner keeps saying I need to slow down.",
            "Three months without a break while carrying a team's worth of work — your partner is right to worry. You matter more than the sprint board.",
        ),
        (
            "Thanks, that actually helps to hear. Oh, and I'm allergic to shellfish, so don't ever suggest a seafood restaurant.",
            "Noted — no shellfish, ever. And seriously, Marcus, consider taking even one day. You've earned it ten times over.",
        ),
    ]

    for user_input, agent_output in conversations:
        user_says(user_input)
        soul_says(agent_output)
        await soul.observe(Interaction(
            user_input=user_input,
            agent_output=agent_output,
        ))
        print()

    # ── Step 3: What the soul remembers ─────────────────────────────────────
    step(3, "What did the soul actually store?")
    print()

    episodic_count = len(soul._memory._episodic._memories)
    semantic_count = len(soul._memory._semantic._facts)
    procedural_count = len(soul._memory._procedural._procedures)
    show("Total memories", str(soul.memory_count))
    show("  Episodic", str(episodic_count))
    show("  Semantic", str(semantic_count))
    show("  Procedural", str(procedural_count))
    show("Bond strength", f"{soul.bond.bond_strength:.1f} (was 50.0)")
    show("Interactions", str(soul.bond.interaction_count))
    print()

    # Show semantic facts
    facts = await soul.recall("facts about Marcus", limit=10)
    semantic = [m for m in facts if m.type == "semantic"]
    if semantic:
        print(f"      {BOLD}Extracted facts:{RESET}")
        for m in semantic[:5]:
            memory_hit("fact", m.content)
        print()

    # Show episodic memories
    episodes = await soul.recall("Marcus feeling overwhelmed", limit=5)
    episodic = [m for m in episodes if m.type == "episodic"]
    if episodic:
        print(f"      {BOLD}Significant episodes (passed the LIDA gate):{RESET}")
        for m in episodic[:3]:
            marker = ""
            if m.somatic:
                marker = f" {DIM}[valence={m.somatic.valence}, arousal={m.somatic.arousal}]{RESET}"
            memory_hit("episode", m.content + marker)
        print()

    # ── Step 4: Save and reload ─────────────────────────────────────────────
    step(4, "Exporting to .soul file and reloading...")

    with tempfile.TemporaryDirectory() as tmp:
        soul_path = os.path.join(tmp, "aria.soul")
        await soul.export(soul_path)
        file_size = os.path.getsize(soul_path)
        show("File", soul_path)
        show("Size", f"{file_size:,} bytes")

        # Safe: Soul.awaken() loads everything into memory, no file handles kept open
        reloaded = await Soul.awaken(soul_path)
        show("Reloaded name", reloaded.name)
        show("Reloaded memories", str(reloaded.memory_count))
        show("Reloaded bond", f"{reloaded.bond.bond_strength:.1f}")
        print()

    # ── Step 5: Recall after reload ─────────────────────────────────────────
    step(5, "Can the reloaded soul still remember?")
    print()

    queries = [
        "What does Marcus do for work?",
        "shellfish allergic",
        "feeling overwhelmed stressed",
    ]

    for q in queries:
        results = await reloaded.recall(q, limit=3)
        print(f"      {BOLD}Q: {q}{RESET}")
        if results:
            for r in results[:2]:
                memory_hit(r.type, r.content)
        else:
            print(f"      {DIM}(no results){RESET}")
        print()

    # ── Step 6: Self-model ──────────────────────────────────────────────────
    step(6, "What has the soul learned about itself?")
    print()

    images = soul.self_model.get_active_self_images()
    if images:
        for img in images[:5]:
            show(img.domain, f"confidence={img.confidence:.0%}")
    else:
        show("Self-model", "Still forming (needs more interactions)")
    print()

    # ── Done ────────────────────────────────────────────────────────────────
    header("That's Soul Protocol")
    print(f"  {BOLD}What just happened:{RESET}")
    print("  - 5 interactions processed through the psychology pipeline")
    print("  - Somatic markers tagged emotional context (Damasio)")
    print("  - Significance gate filtered what's worth remembering (LIDA)")
    print("  - Facts extracted and stored in semantic memory")
    print("  - Bond strength grew from interaction")
    print("  - Self-model started forming identity domains (Klein)")
    print("  - Everything saved to a portable .soul file and reloaded")
    print("  - Zero LLM calls. Zero API keys. Zero cost.\n")
    print(f"  {DIM}Learn more: https://github.com/qbtrix/soul-protocol{RESET}")
    print(f"  {DIM}Read the whitepaper: WHITEPAPER.md{RESET}\n")


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
