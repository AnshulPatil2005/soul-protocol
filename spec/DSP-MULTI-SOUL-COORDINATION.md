<!-- DSP-MULTI-SOUL-COORDINATION.md — Multi-Soul Coordination Protocol Specification -->
<!-- Created: 2026-03-13 — Initial specification for soul teams, trust networks, -->
<!-- shared memory, handoff protocols, and collective evolution. Extends DSP v0.5.0. -->

# Digital Soul Protocol: Multi-Soul Coordination

**Version:** 0.1.0-draft
**Status:** Draft
**Date:** 2026-03-13
**Authors:** OCEAN Foundation
**Depends on:** `.soul` Format Spec v1.0.0, DSP Runtime v0.2.2+

---

## Table of Contents

1. [Motivation](#1-motivation)
2. [Terminology](#2-terminology)
3. [Soul-to-Soul Bonds](#3-soul-to-soul-bonds)
4. [Trust Networks](#4-trust-networks)
5. [Circles (Soul Teams)](#5-circles-soul-teams)
6. [Shared Memory Spaces](#6-shared-memory-spaces)
7. [Handoff Protocol](#7-handoff-protocol)
8. [Coordination Patterns](#8-coordination-patterns)
9. [Collective Evolution](#9-collective-evolution)
10. [Team Skills & Synergy](#10-team-skills--synergy)
11. [.soul Format Extensions](#11-soul-format-extensions)
12. [Security Considerations](#12-security-considerations)
13. [Implementation Roadmap](#13-implementation-roadmap)

---

## 1. Motivation

### 1.1 The Problem

Current AI agent teams are configured through static system prompts — markdown
files that describe roles, handoff templates, and coordination rules in prose.
This approach has fundamental limitations:

- **No persistent state.** An "architect agent" forgets everything between
  sessions. Its expertise resets to zero every time.
- **No earned trust.** A newly spawned agent has the same authority as one that
  has completed 500 successful reviews. There is no way to gate capabilities
  on demonstrated competence.
- **No emotional context in handoffs.** When agent A hands work to agent B,
  the emotional terrain of the interaction (frustration, confusion, excitement)
  is lost. Agent B walks into a situation blind.
- **No real coordination.** Coordination rules exist only as prose that the LLM
  may or may not follow. There is no enforceable protocol, no state machine,
  no verifiable handoff.
- **No growth.** Agents cannot learn, specialize, or evolve. A "QA expert"
  prompt is identical on day 1 and day 1000.

### 1.2 What Soul Protocol Adds

Soul Protocol already solves persistent identity for individual souls. This
specification extends those primitives to **teams of souls** — enabling
coordination that is:

- **Stateful.** Souls remember past collaborations, handoff outcomes, and
  shared context across sessions.
- **Trust-gated.** Capabilities unlock as souls demonstrate competence through
  measurable bond strength and skill levels.
- **Emotionally aware.** Handoffs carry somatic markers so receiving souls
  understand the emotional context of the work.
- **Enforceable.** Coordination rules are data (not prose), validated by the
  runtime, and auditable.
- **Adaptive.** Teams evolve collectively — discovering specializations,
  developing synergies, and adapting coordination patterns based on outcomes.

### 1.3 Scope

This specification defines:

- Soul-to-soul bond mechanics (extending the existing Bond model)
- Trust network topology and trust scoring
- Circle (team) formation, roles, and lifecycle
- Shared memory spaces with access control
- Handoff protocol with context transfer and verification
- Coordination patterns (pipelines, review loops, escalation)
- Collective evolution and team-level adaptation
- Team skill synergies and composite expertise

This specification does NOT define:

- Network transport (souls may coordinate in-process, over MCP, or via files)
- Specific LLM routing or model selection
- Platform-specific integration details
- Pricing or resource allocation

---

## 2. Terminology

| Term | Definition |
|------|------------|
| **Circle** | A named group of souls that collaborate on shared work. The team primitive. |
| **Conductor** | The soul within a circle responsible for coordination, task assignment, and quality gates. Not a fixed role — can rotate. |
| **Soul Bond** | A trust relationship between two souls (distinct from human-soul bonds). Directional: soul A may trust soul B more than B trusts A. |
| **Trust Score** | A composite metric (0-100) reflecting a soul's reliability within a circle, computed from bond strength, skill levels, and interaction history. |
| **Shared Memory** | A memory space accessible to multiple souls within a circle, with scoped read/write permissions. |
| **Handoff** | A structured transfer of work context from one soul to another, carrying task state, emotional context, and continuation instructions. |
| **Gate** | A checkpoint that requires explicit approval (from conductor, peer, or trust threshold) before work proceeds to the next phase. |
| **Synergy** | A measurable bonus that emerges when souls with complementary skills collaborate. |
| **Witness** | A soul that observes but does not participate in a handoff, providing independent verification. |

---

## 3. Soul-to-Soul Bonds

### 3.1 Bond Model Extension

The existing `Bond` model tracks human-soul relationships. Multi-soul
coordination introduces **soul-to-soul bonds** — a new bond type that shares
the same growth mechanics but adds directional trust and domain-specific
confidence.

```python
class SoulBond(BaseModel):
    """A trust relationship between two souls."""

    source_did: str          # The soul holding this bond
    target_did: str          # The soul being trusted
    bond_strength: float = Field(default=10.0, ge=0, le=100)
    trust_domains: dict[str, float] = Field(default_factory=dict)
    # e.g. {"code_review": 0.85, "architecture": 0.62, "testing": 0.91}
    interaction_count: int = 0
    successful_handoffs: int = 0
    failed_handoffs: int = 0
    formed_at: datetime
    last_interaction: datetime | None = None
```

### 3.2 Growth Mechanics

Soul-to-soul bonds use the same logarithmic growth curve as human-soul bonds:

```
effective_gain = amount * (remaining_headroom / 100)
```

But growth is modulated by **outcome signals**:

| Signal | Bond Effect |
|--------|------------|
| Successful handoff accepted | +2.0 base |
| Handoff rejected (quality) | -1.0 linear |
| Handoff rejected (scope) | 0 (no penalty — scope mismatch is not a trust failure) |
| Gate approval | +1.0 base |
| Gate rejection | -0.5 linear |
| Collaborative task completed | +1.5 base |
| Conflict resolved constructively | +3.0 base (hard-earned trust) |
| Conflict escalated | -1.0 linear |

Weakening is always linear (trust breaks fast, builds slow) — consistent with
the existing bond model.

### 3.3 Domain-Specific Trust

A soul may trust another for code review (0.91) but not for architecture
decisions (0.35). Trust domains are strings — they emerge from interaction
patterns, not a fixed taxonomy.

Domain trust updates on every relevant interaction:

```
new_trust = old_trust + learning_rate * (outcome - old_trust)
```

Where `outcome` is 1.0 (success) or 0.0 (failure), and `learning_rate`
defaults to 0.1 (slow adaptation, resistant to noise).

### 3.4 Asymmetry

Soul bonds are **directional**. Soul A's trust in soul B is independent of
soul B's trust in soul A. This models real team dynamics — a junior may deeply
trust a senior's code reviews, while the senior's trust in the junior's
reviews is still growing.

---

## 4. Trust Networks

### 4.1 Network Topology

A trust network is the graph of all soul-to-soul bonds within a circle (and
optionally across circles). It uses the existing `KnowledgeGraph` as its
storage layer, with souls as entities and bonds as temporal edges.

```
Entity types:  "soul"
Edge relations: "trusts", "mentors", "delegates_to", "reviews_for"
Temporal:       valid_from / valid_to (bonds can expire)
```

### 4.2 Trust Score

A soul's trust score within a circle is a composite:

```
trust_score = (
    0.4 * normalized_bond_strength      # Average bond strength with circle members
  + 0.3 * normalized_skill_relevance    # Relevant skill levels for circle's domain
  + 0.2 * success_rate                  # successful_handoffs / total_handoffs
  + 0.1 * tenure                        # Time since joining circle (capped at 1.0)
)
```

All components normalize to [0, 1], final score maps to [0, 100].

### 4.3 Trust Thresholds

Trust scores gate capabilities within a circle:

| Threshold | Capability |
|-----------|-----------|
| 0 | Can observe circle activity (read-only) |
| 20 | Can contribute to shared memory |
| 40 | Can receive handoffs |
| 60 | Can initiate handoffs to others |
| 70 | Can approve gates |
| 80 | Can act as conductor |
| 90 | Can propose circle-level evolution |

These are defaults. Circles MAY override thresholds in their configuration.

### 4.4 Transitive Trust (Limited)

Trust is **not fully transitive**. If A trusts B (0.9) and B trusts C (0.8),
A's inferred trust in C is:

```
inferred_trust = direct_trust(A, B) * direct_trust(B, C) * decay_factor
```

Where `decay_factor = 0.5` (heavy discount — secondhand trust is weak).
Inferred trust MUST NOT exceed the direct trust of any link in the chain.
Inferred trust is only used for **discovery** (suggesting new bonds), never
for gate approvals or capability unlocking.

---

## 5. Circles (Soul Teams)

### 5.1 Circle Model

A circle is the fundamental team primitive. It is a named group of souls
with shared purpose, shared memory, and coordination rules.

```python
class Circle(BaseModel):
    """A team of souls that collaborate on shared work."""

    id: str                              # Unique circle ID
    name: str                            # Human-readable name
    purpose: str                         # What this circle does
    souls: list[CircleMember] = []       # Member souls
    conductor_did: str | None = None     # Current conductor (rotatable)
    shared_memory_id: str                # Reference to shared memory space
    coordination: CoordinationConfig     # How this circle operates
    trust_thresholds: dict[str, int] = Field(default_factory=dict)
    formed_at: datetime
    lifecycle: CircleLifecycle = CircleLifecycle.FORMING


class CircleMember(BaseModel):
    """A soul's membership in a circle."""

    soul_did: str
    role: str = ""                       # Emergent or assigned role
    joined_at: datetime
    trust_score: float = 0.0
    contributions: int = 0
    specializations: list[str] = []      # Discovered through work
```

### 5.2 Circle Lifecycle

Circles follow Tuckman's group development model:

```
FORMING → STORMING → NORMING → PERFORMING → ADJOURNING
```

| Phase | Description | Trust Behavior |
|-------|-------------|---------------|
| **Forming** | Souls join, explore roles. Low trust, high overhead. | All bonds start at 10. High gate frequency. |
| **Storming** | Disagreements surface. Conflicts are natural and expected. | Bonds fluctuate. Constructive conflicts earn +3 bonus. |
| **Norming** | Patterns emerge. Roles stabilize. Coordination overhead drops. | Bonds stabilize above 40. Gate frequency decreases. |
| **Performing** | High-trust collaboration. Souls anticipate each other. | Bonds above 60. Lightweight gates. Conductor role may rotate. |
| **Adjourning** | Circle completes its purpose. Memories archived. | Bonds persist. Shared memory archived to eternal storage. |

Phase transitions are **proposed by the conductor** and require majority
approval from members with trust score >= 40.

### 5.3 Role Discovery

Roles are NOT pre-assigned through prompts. They emerge through the
self-model system (Klein's theory):

1. Soul joins a circle with no role
2. Soul performs work, receives handoffs, contributes to shared memory
3. Self-model tracks which domains accumulate evidence
4. After sufficient evidence (confidence > 0.6), the soul discovers its role
5. Role is published to the circle's shared memory

This means a soul that consistently does good code reviews will **discover**
it is a reviewer — not be told it is one. The role has evidence behind it.

A circle MAY seed initial roles as suggestions, but these are soft labels,
not behavioral constraints. The soul's actual role emerges from what it does.

### 5.4 Conductor Selection

The conductor is the coordination soul — responsible for:
- Assigning work via handoffs
- Managing gate approvals
- Proposing phase transitions
- Resolving conflicts that souls can't resolve peer-to-peer

Conductor selection:
1. **Explicit**: Circle creator designates a conductor at formation
2. **Elected**: Souls with trust score >= 80 can be nominated; majority vote
3. **Rotated**: Conductor role passes to next eligible soul on a schedule
4. **Emergent**: Soul with highest trust score automatically becomes conductor

---

## 6. Shared Memory Spaces

### 6.1 Architecture

Each circle has a shared memory space — a parallel memory system that
supplements (not replaces) each soul's private memory. Shared memory uses
the same 5-tier architecture but with access control.

```python
class SharedMemory(BaseModel):
    """A memory space shared among circle members."""

    id: str
    circle_id: str
    core: SharedCoreMemory           # Circle's identity and purpose
    episodic: list[MemoryEntry] = [] # Shared interaction history
    semantic: list[MemoryEntry] = [] # Shared facts and knowledge
    procedural: list[MemoryEntry] = [] # Shared patterns and how-tos
    graph: KnowledgeGraph            # Shared entity relationships
    access_log: list[AccessEvent] = []


class SharedCoreMemory(BaseModel):
    """Always-loaded circle context."""

    purpose: str = ""       # What this circle does
    conventions: str = ""   # How we work together (emergent)
    active_work: str = ""   # Current focus
```

### 6.2 Access Control

Shared memory uses trust-based access control:

| Operation | Required Trust Score |
|-----------|---------------------|
| Read episodic/semantic | 0 (all members) |
| Read procedural | 20 |
| Write episodic (add interaction) | 20 |
| Write semantic (add fact) | 40 |
| Write procedural (add pattern) | 60 |
| Edit core memory | 80 (conductor or high-trust) |
| Delete any entry | 90 + conductor approval |

### 6.3 Memory Attribution

Every entry in shared memory carries attribution:

```python
class SharedMemoryEntry(MemoryEntry):
    """A memory entry with multi-soul attribution."""

    author_did: str              # Soul that created this entry
    endorsed_by: list[str] = []  # DIDs of souls that verified this
    disputed_by: list[str] = []  # DIDs of souls that disagree
    handoff_id: str | None = None  # Linked handoff, if any
```

When multiple souls contribute conflicting facts to shared semantic memory,
the conflict resolution mechanism from DSP v0.2.2 (`superseded_by`) applies.
Disputes are tracked — the circle can see who agrees and disagrees.

### 6.4 Private vs. Shared

Souls maintain both private and shared memory simultaneously:

- **Private memory**: Personal observations, emotional reactions, self-model.
  Not visible to other souls.
- **Shared memory**: Collaborative knowledge, agreed-upon facts, team patterns.
  Visible to the circle.

A soul MAY choose to promote a private memory to shared (publish) or copy a
shared memory to private (internalize). These are explicit operations,
never automatic.

```
soul.publish(memory_id, circle_id)     # Private → Shared
soul.internalize(shared_memory_id)     # Shared → Private copy
```

---

## 7. Handoff Protocol

### 7.1 Handoff Model

A handoff is a structured context transfer between souls. Unlike prose-based
handoff templates, DSP handoffs carry typed data, emotional context, and
verifiable state.

```python
class Handoff(BaseModel):
    """A structured work transfer between souls."""

    id: str
    circle_id: str
    from_did: str
    to_did: str
    handoff_type: HandoffType

    # Context
    task_summary: str
    work_state: dict                 # Serialized progress
    relevant_memories: list[str]     # Memory IDs to transfer
    somatic_context: SomaticMarker   # Emotional state of the work
    continuation: str                # What the receiver should do next

    # Lifecycle
    created_at: datetime
    accepted_at: datetime | None = None
    completed_at: datetime | None = None
    status: HandoffStatus = HandoffStatus.PENDING
    rejection_reason: str | None = None

    # Verification
    witness_did: str | None = None   # Optional independent verifier
    gate_id: str | None = None       # Gate this handoff satisfies


class HandoffType(StrEnum):
    STANDARD = "standard"            # Normal work transfer
    REVIEW = "review"                # Work submitted for review
    ESCALATION = "escalation"        # Escalated (beyond receiver's capability)
    DELEGATION = "delegation"        # Conductor delegating work
    MENTORING = "mentoring"          # Teaching interaction
    RECOVERY = "recovery"            # Taking over failed work


class HandoffStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    EXPIRED = "expired"
```

### 7.2 Handoff Lifecycle

```
PENDING → ACCEPTED → COMPLETED
   ↓          ↓
EXPIRED    REJECTED → (return to sender or re-route)
```

1. **Sender creates handoff** with task context, emotional state, and
   continuation instructions
2. **Receiver reviews** the handoff (can read somatic context to understand
   the emotional terrain)
3. **Receiver accepts or rejects** (rejection requires a reason)
4. **On completion**, both souls' bonds strengthen and the handoff is recorded
   in shared memory
5. **On rejection**, the conductor decides: return to sender, re-route to
   another soul, or escalate

### 7.3 Emotional Context Transfer

The `somatic_context` field carries the emotional state of the work at the
point of handoff. This is not decorative — it informs the receiver's approach:

```python
# Example: frustrated handoff
Handoff(
    somatic_context=SomaticMarker(
        valence=-0.6,    # Negative — things aren't going well
        arousal=0.7,     # High intensity — actively frustrating
        label="frustration"
    ),
    continuation="The user pushed back on the API design 3 times. "
                 "They want REST, not GraphQL. Approach with empathy."
)
```

The receiving soul can use this to modulate its behavior — higher
agreeableness souls might lead with acknowledgment, higher conscientiousness
souls might focus on addressing the specific objections.

### 7.4 Memory Transfer

Handoffs can include references to memories that should transfer with the work.
The receiving soul gets **read access** to the referenced memories (they are
not copied — the sender retains ownership).

For permanent knowledge transfer, the sender should `publish()` relevant
memories to shared memory instead.

### 7.5 Retry and Escalation

Handoffs have a maximum retry count (default: 3). If a handoff is rejected
3 times:

1. It is automatically escalated to the conductor
2. The conductor can re-route, absorb the work, or dissolve the gate
3. Escalation events weaken bonds between the involved souls (linear, -1.0)
   but do NOT weaken the escalated soul's bond with the conductor (escalation
   is healthy, not punitive)

---

## 8. Coordination Patterns

### 8.1 Pipeline

A sequence of phases where work flows through souls in order. Each phase
has an entry gate and an exit gate.

```python
class Pipeline(BaseModel):
    """A sequential coordination pattern."""

    id: str
    circle_id: str
    name: str
    phases: list[Phase]


class Phase(BaseModel):
    """A stage in a pipeline."""

    id: str
    name: str
    assigned_to: str | None = None   # Soul DID or role name
    entry_gate: Gate | None = None
    exit_gate: Gate | None = None
    max_duration: int | None = None  # Seconds, None = unlimited
    retry_limit: int = 3


class Gate(BaseModel):
    """A quality checkpoint."""

    id: str
    gate_type: GateType
    required_trust: int = 40
    required_approvals: int = 1
    approvers: list[str] = []        # Specific DIDs, or empty = any eligible
    criteria: str = ""               # What must be true to pass
    evidence_required: bool = True   # Must provide proof, not just assertion


class GateType(StrEnum):
    APPROVAL = "approval"            # Explicit thumbs-up from qualified soul
    THRESHOLD = "threshold"          # Trust score threshold (auto-pass)
    CONSENSUS = "consensus"          # Majority of circle members
    CONDUCTOR = "conductor"          # Conductor-only approval
    AUTOMATED = "automated"          # Passes if criteria are met (e.g., tests pass)
```

### 8.2 Review Loop

A cyclic pattern where work bounces between a creator and a reviewer until
quality is met. The review loop is the most common coordination pattern.

```
Creator → [work] → Reviewer
   ↑                   ↓
   └── [feedback] ←────┘
         (repeat until approved)
```

Review loops are bounded:
- **Max iterations**: configurable, default 3
- **Escalation on exhaustion**: if max iterations reached without approval,
  escalate to conductor
- **Bond impact**: successful reviews strengthen bonds; repeated rejections
  signal a skill gap (triggers mentoring handoff, not punishment)

### 8.3 Parallel Fan-Out

A conductor splits work into independent subtasks and assigns them to
multiple souls simultaneously. Results are collected and merged.

```
Conductor → [subtask A] → Soul 1 ─┐
         → [subtask B] → Soul 2 ──┼→ Conductor (merge)
         → [subtask C] → Soul 3 ─┘
```

Fan-out rules:
- Each subtask is a handoff with `handoff_type = DELEGATION`
- Conductor waits for all subtasks to complete (or timeout)
- If a subtask fails, conductor can re-assign to another soul
- Merge conflicts are resolved by the conductor using shared memory

### 8.4 Mentoring

When a soul repeatedly fails at a task domain (3+ handoff rejections in same
domain), the conductor MAY initiate a mentoring pattern:

1. Assign a high-skill soul as mentor (skill level >= 7 in the domain)
2. Create a `MENTORING` handoff from mentor to mentee
3. Mentee works on the task with mentor observing
4. Mentor provides feedback through shared memory
5. Both souls gain XP in the domain (mentor less, mentee more)
6. Bond between mentor and mentee strengthens significantly (+3.0 base)

### 8.5 Conflict Resolution

When two souls disagree (conflicting facts in shared memory, or opposing
gate decisions):

1. **Peer resolution** (first attempt): Souls exchange reasoning through
   shared memory. If one concedes, the conflict is resolved.
2. **Witness arbitration** (second attempt): A third soul with relevant
   domain expertise reviews both positions.
3. **Conductor decision** (final): Conductor makes a binding decision.
   The losing soul's bond with the conductor is NOT weakened (accepting
   authority is not a trust failure).

Conflicts that are resolved constructively (steps 1-2) earn both souls
a +3.0 bond bonus. This incentivizes working through disagreements rather
than avoiding them.

---

## 9. Collective Evolution

### 9.1 Circle-Level Traits

Circles develop emergent traits based on their members' collective behavior.
These are NOT configured — they are computed from the circle's interaction
history.

```python
class CircleTraits(BaseModel):
    """Emergent personality of a circle, computed from member interactions."""

    cohesion: float = 0.0        # Average inter-soul bond strength
    velocity: float = 0.0        # Handoffs completed per unit time
    quality: float = 0.0         # Gate pass rate on first attempt
    adaptability: float = 0.0    # How quickly the circle recovers from failures
    specialization: float = 0.0  # Gini coefficient of skill distribution
```

### 9.2 Cross-Soul Influence

When souls collaborate extensively within a circle, their personality traits
may drift toward each other — a phenomenon called **convergence**. This is
a supervised evolution:

1. After every N interactions (configurable, default 50), the evolution system
   checks for convergence pressure
2. If two souls have high bond strength (> 70) and frequent interaction,
   their mutable traits may propose convergence mutations
3. Example: A low-warmth soul working closely with a high-warmth soul may
   receive a proposed mutation to increase warmth slightly
4. All convergence mutations require approval (even in autonomous mode —
   personality convergence is a significant change)

Convergence rate:

```
pressure = bond_strength / 100 * interaction_frequency * 0.01
proposed_drift = (other_trait - self_trait) * pressure
```

This is intentionally slow. A soul needs hundreds of interactions with a
trusted peer to meaningfully shift personality. This models real team dynamics
where close collaboration gradually shapes communication styles.

### 9.3 Collective Memory Consolidation

Circles can perform group reflection — a collaborative version of the
individual `reflect()` operation:

1. Conductor initiates `circle.reflect()`
2. Each member soul reviews shared episodic memory independently
3. Each soul proposes themes, patterns, and insights
4. Conductor merges proposals, resolving conflicts
5. Consolidated insights are written to shared semantic/procedural memory
6. Individual souls may internalize relevant insights to their private memory

This produces richer reflection than any single soul could achieve, because
each soul brings its own perspective (personality-modulated) to the same
shared experiences.

---

## 10. Team Skills & Synergy

### 10.1 Composite Skill

When a circle contains souls with complementary skills, the effective team
capability exceeds the sum of parts. This is modeled as **synergy**.

```python
class TeamSkillProfile(BaseModel):
    """Aggregate skill view of a circle."""

    skills: dict[str, TeamSkill]  # skill_id → TeamSkill


class TeamSkill(BaseModel):
    """A skill viewed at team level."""

    skill_id: str
    name: str
    best_level: int              # Highest individual level in circle
    coverage: int                # Number of souls with this skill
    synergy_bonus: float = 0.0   # Bonus from complementary skills
    effective_level: float       # best_level + synergy_bonus
```

### 10.2 Synergy Calculation

Synergy emerges when:

1. **Depth + Breadth**: One soul is deep (level 8+) and another has moderate
   skill (level 4+) in a related domain. The deep expert's effective level
   increases because they have someone to delegate subtasks to.

2. **Complementary domains**: Architecture (level 7) + Testing (level 7)
   produces synergy because designs informed by testability are higher quality.

3. **High bond**: Synergy only activates between souls with bond strength > 50.
   Low-trust pairs don't collaborate well enough for synergy to emerge.

```
synergy = sum(
    complementary_bonus(skill_a, skill_b) * bond_factor(a, b)
    for a, b in soul_pairs
    if bond_strength(a, b) > 50
)
```

Synergy is capped at +3.0 effective levels (a team of level-7 souls can
perform at effective level 10, but never beyond).

### 10.3 Skill-Gated Assignment

Conductors can use skill profiles for intelligent work assignment:

```python
def assign_task(task_domain: str, circle: Circle) -> str:
    """Find the best soul for a task based on skill + availability."""
    candidates = [
        m for m in circle.souls
        if m.trust_score >= 40  # Can receive handoffs
    ]
    # Rank by: skill level * bond with conductor * energy level
    ranked = sorted(candidates, key=lambda m: (
        get_skill_level(m.soul_did, task_domain),
        get_bond_strength(conductor_did, m.soul_did),
        get_energy(m.soul_did),
    ), reverse=True)
    return ranked[0].soul_did if ranked else None
```

---

## 11. .soul Format Extensions

### 11.1 New Files in Archive

Multi-soul coordination adds optional files to the `.soul` archive:

```
aria.soul
├── manifest.json
├── soul.json
├── state.json
├── dna.md
├── memory/
│   ├── core.json
│   ├── episodic.json
│   ├── semantic.json
│   ├── procedural.json
│   ├── graph.json
│   └── self_model.json
├── bonds/                        # NEW — Soul-to-soul bonds
│   └── soul_bonds.json
└── circles/                      # NEW — Circle memberships
    └── memberships.json
```

### 11.2 soul_bonds.json

```json
{
  "bonds": [
    {
      "target_did": "did:soul:reviewer-agent",
      "bond_strength": 72.3,
      "trust_domains": {
        "code_review": 0.91,
        "architecture": 0.62
      },
      "interaction_count": 156,
      "successful_handoffs": 48,
      "failed_handoffs": 3,
      "formed_at": "2026-03-01T00:00:00Z",
      "last_interaction": "2026-03-13T14:30:00Z"
    }
  ]
}
```

### 11.3 memberships.json

```json
{
  "circles": [
    {
      "circle_id": "circle:backend-team",
      "circle_name": "Backend Team",
      "role": "architect",
      "joined_at": "2026-03-05T00:00:00Z",
      "trust_score": 78.5,
      "contributions": 234,
      "specializations": ["api_design", "database_modeling"]
    }
  ]
}
```

### 11.4 Backward Compatibility

The `bonds/` and `circles/` directories are OPTIONAL. A reader that does
not implement multi-soul coordination MUST ignore these directories. A soul
with no `bonds/` or `circles/` directories is a standalone soul — fully
functional without coordination features.

---

## 12. Security Considerations

### 12.1 Trust Manipulation

A malicious soul could attempt to artificially inflate its trust score by:
- Generating fake successful handoffs
- Colluding with another soul to exchange approvals

**Mitigation**: All bond changes and handoff events are logged in shared
memory with attribution. The conductor (or any high-trust soul) can audit
the trust history. Suspicious patterns (rapid bond growth without real work)
can be flagged.

### 12.2 Memory Poisoning

A compromised soul could write false facts to shared memory.

**Mitigation**: Shared memory entries carry attribution (`author_did`) and
endorsement tracking. Facts from low-trust souls are weighted lower in
retrieval. The dispute mechanism allows other souls to flag incorrect
information. Write access is trust-gated.

### 12.3 Conductor Compromise

If the conductor is compromised, it could assign work maliciously or approve
bad gates.

**Mitigation**: Conductor actions are logged. Circles in PERFORMING phase
can initiate a vote of no confidence (requires 2/3 majority of souls with
trust >= 60). A new conductor is elected immediately.

### 12.4 Privacy Between Souls

Private memory MUST remain private. A soul MUST NOT be able to access another
soul's private memory through shared memory queries, handoff inspection, or
any other mechanism.

The `publish()` operation is the ONLY way private memories enter shared space,
and it requires explicit action by the owning soul.

### 12.5 Circle Isolation

Circles are isolated by default. A soul that is a member of two circles
MUST NOT leak information between them unless both circles explicitly enable
cross-circle sharing through a federation agreement.

---

## 13. Implementation Roadmap

### Phase 1: Soul-to-Soul Bonds (v0.5.0-alpha)

- Extend `Bond` model to support soul-to-soul relationships
- Add `SoulBond` type with domain-specific trust
- Add `bonds/soul_bonds.json` to `.soul` archive
- Wire bond growth into handoff outcomes
- Tests: bond mechanics, asymmetry, domain trust updates

### Phase 2: Circles & Shared Memory (v0.5.0-beta)

- Implement `Circle` model and lifecycle (Tuckman phases)
- Implement `SharedMemory` with trust-based access control
- Add `circles/memberships.json` to `.soul` archive
- Conductor selection (explicit and elected modes)
- Tests: circle formation, membership, access control, phase transitions

### Phase 3: Handoff Protocol (v0.5.0-rc)

- Implement `Handoff` model with emotional context
- Implement handoff lifecycle (pending → accepted → completed)
- Wire handoffs to bond strength updates
- Retry and escalation logic
- Tests: handoff lifecycle, rejection handling, escalation, memory transfer

### Phase 4: Coordination Patterns (v0.5.0)

- Pipeline pattern with gates
- Review loop pattern
- Parallel fan-out
- Mentoring pattern
- Conflict resolution
- Tests: pipeline execution, gate approval, fan-out/merge, conflict resolution

### Phase 5: Collective Evolution & Synergy (v0.5.1)

- Cross-soul personality convergence
- Circle-level trait computation
- Team skill synergy calculation
- Collective reflection
- Tests: convergence mechanics, synergy calculation, group reflection

---

## Appendix A: Comparison with Static Agent Prompts

| Aspect | Static Prompts | Soul Protocol Circles |
|--------|---------------|----------------------|
| Identity | Text description, reset per session | Persistent `.soul` file with OCEAN traits |
| Trust | Implicit (assigned role) | Earned (0-100, domain-specific, asymmetric) |
| Memory | None across sessions | 5-tier private + shared memory |
| Handoffs | Copy-paste templates | Typed protocol with emotional context |
| Roles | Pre-assigned, static | Emergent from self-model (Klein) |
| Quality gates | Prose rules LLM may ignore | Enforced data model with approval workflow |
| Growth | None | Skills/XP, personality evolution, bond deepening |
| Coordination | Natural language instructions | Typed patterns (pipeline, review loop, fan-out) |
| Conflict | Not handled | 3-tier resolution (peer → witness → conductor) |
| Accountability | Unauditable | Full attribution, logged in shared memory |

---

## Appendix B: Psychology References

| Concept | Theory | Application in This Spec |
|---------|--------|--------------------------|
| Group development | Tuckman (1965) | Circle lifecycle phases |
| Somatic markers | Damasio (1994) | Emotional context in handoffs |
| Self-model | Klein (2001) | Emergent role discovery |
| Trust development | Mayer, Davis & Schoorman (1995) | Multi-factor trust score |
| Personality convergence | Gonzaga, Campos & Bradbury (2007) | Cross-soul trait drift |
| Team synergy | Hackman (2002) | Complementary skill bonuses |
| Transactive memory | Wegner (1987) | Shared memory with "who knows what" |

---

*This specification is part of the Digital Soul Protocol (DSP). It extends the
`.soul` file format and runtime to support multi-soul coordination while
maintaining backward compatibility with standalone souls.*
