# Soul Protocol: A Portable Standard for AI Companion Identity, Memory, and Cognition

**Version 0.5.0 — Whitepaper**
**Published:** March 2026
**Authors:** The Soul Protocol Team

---

## Abstract

Current AI memory systems treat persistence as a retrieval problem — find the most similar text, stuff it into context, and hope for the best. Soul Protocol takes a fundamentally different approach: persistent AI identity grounded in cognitive science, packaged as a portable open standard.

We present a two-layer architecture: a minimal **protocol specification** (624 lines) defining the portable primitives — identity, memory stores, file format, embedding and storage provider interfaces — and a **reference runtime** (7,500+ lines) implementing psychology-informed memory, personality evolution, emotional bonds, skill progression, and knowledge graphs.

The protocol layer is deliberately thin. Like HTTP, it defines how data moves — not how you build your application. The runtime layer is one opinionated implementation. Others can build their own.

The result: an AI companion whose entire cognitive state — personality, memories, emotional bonds, learned skills, knowledge graph — serializes into a single `.soul` file that belongs to the user, works with any LLM, and survives platform changes.

This whitepaper describes the problem, the architecture, the psychology stack that drives memory formation, and the current state of the implementation — with honest accounting of what works, what doesn't, and what comes next.

---

## 1. The Problem

### Stateless AI is a product dead end

Most AI assistants are amnesiac by default. Every conversation starts from zero. Users re-explain their preferences, their context, their history — not because the technology can't store it, but because persistent identity hasn't been treated as a first-class concern.

When memory does exist, it's usually bolted on: a vector database holds conversation chunks, a RAG pipeline retrieves them, a summarization buffer compresses recent turns. These solve a narrow retrieval problem. They don't solve identity.

### The retrieval-only fallacy

Treating memory as a retrieval problem assumes the goal is finding the most similar text. But what makes a companion feel real isn't similarity search.

Consider what actually determines whether a memory sticks:

- A debugging session at 2am where something finally clicked — emotionally charged, therefore memorable
- A casual "hello" that happened 100 times — similar to any greeting query, but meaningless to store
- A fact learned three months ago, recalled twice this week — more accessible than an "important" fact from last week that was never revisited
- Repeated patterns of helping with code — evidence that eventually forms a self-belief: *"I'm good at this"*

None of this is captured by cosine similarity. Vector databases are good at one thing. Memory requires many things.

### The portability gap

Even where persistent memory exists, it's locked to one platform. A companion's history lives in OpenAI's infrastructure, or Anthropic's memory layer, or a custom database tied to one application. Switch providers, start over. Change apps, start over.

There's no concept of a soul that belongs to the user, travels with them, and survives platform changes. Current approaches build the graph but lock it to their runtime (Cognee), offer retrieval without identity (Mem0), or define reputation without cognition (ERC-8004). Nobody combines portable identity, structured memory, and cognitive processing in an open standard.

---

## 2. Design Philosophy: Protocol, Not Product

### The HTTP analogy

HTTP doesn't tell you how to build your website. It defines how data moves between client and server. The specification is small. The implementations are infinite.

Soul Protocol follows the same principle. The codebase separates into two layers:

```
soul_protocol/
├── spec/      624 lines  — THE PROTOCOL (portable, minimal, no opinions)
├── runtime/  7,495 lines — REFERENCE IMPLEMENTATION (opinionated, batteries-included)
├── cli/                   — Command-line tools
└── mcp/                   — Model Context Protocol server
```

**`spec/`** defines the primitives any runtime must implement: Identity, MemoryStore interface, MemoryEntry format, SoulContainer, `.soul` file pack/unpack, EmbeddingProvider interface, EternalStorageProvider interface, and similarity functions. It depends only on Pydantic. Nothing else.

**`runtime/`** is one way to run the protocol — the "nginx" to the protocol's "HTTP." It implements OCEAN personality, five-tier memory with psychology-informed processing, knowledge graphs, a cognitive engine, emotional bonds, skill progression, and more. Other runtimes can implement the same `spec/` interfaces with entirely different approaches.

### What the protocol enforces

- Every soul has a unique identity
- Every memory entry has a timestamp, type, and content
- The `.soul` file format is standardized (ZIP archive, JSON payloads)
- Provider interfaces (memory, embedding, storage) are stable contracts
- Container operations (create, open, save) follow defined semantics

### What the protocol does not enforce

- No required personality model (OCEAN is a runtime choice)
- No required memory backend (in-memory, SQLite, Neo4j — your call)
- No required graph structure or embedding approach
- No required layer names or domain isolation strategy
- No required LLM provider

The separation is real, not cosmetic. The `spec/` layer has been designed for eventual porting to Go or Rust — 624 lines of pure data models and interface definitions. Additionally, JSON Schemas are auto-generated from the protocol models, enabling cross-language validation today. Any language with a JSON Schema validator can read and write `.soul` files without the Python SDK.

---

## 3. Architecture

### The five-tier memory system

```
┌──────────────────────────────────────────────────────────────┐
│                           Soul                               │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │   Core   │  │ Episodic │  │ Semantic │  │ Procedural │  │
│  │  Memory  │  │  Memory  │  │  Memory  │  │   Memory   │  │
│  │ (always  │  │ (signif- │  │ (extrac- │  │  (how-to   │  │
│  │ loaded)  │  │  icance- │  │   ted    │  │  patterns) │  │
│  │          │  │  gated)  │  │  facts)  │  │            │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────────┐│
│  │       Knowledge Graph (temporal entity-relations)        ││
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              Archival Memory (compressed)                ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

**Core memory** is always present — the persona, the companion's values, the profile of who it's bonded to. It forms the bedrock of every system prompt. Edits replace rather than append, reflecting how core beliefs update.

**Episodic memory** holds interaction history — but only interactions that pass the significance gate. This is where emotional salience and novel experiences live.

**Semantic memory** holds extracted facts: names, preferences, work context, relationships. Facts are deduplicated and conflict-checked — when new information contradicts old, the older fact is marked `superseded_by` rather than silently overwritten.

**Procedural memory** holds learned patterns — how this person likes explanations, what approaches work, what doesn't.

**The knowledge graph** links entities with temporal edges. Each relationship has `valid_from` and `valid_to` timestamps, enabling point-in-time queries ("what did the soul know about X as of last Tuesday?") and relationship evolution tracking ("how has the soul's understanding of this entity changed over time?").

**Archival memory** provides long-term compressed storage. Conversations are archived with summaries and key moments, searchable by keyword and date range. A compression pipeline handles deduplication, importance-based pruning, and export optimization.

### The observe() pipeline

Every interaction passes through a psychology-informed pipeline before anything gets stored:

```
User input + Agent output
    │
    ▼
┌─────────────────────┐
│  Sentiment Detection │  ← Damasio: tag emotional context
│  (somatic markers)   │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Significance Gate   │  ← LIDA: is this worth remembering?
│  (threshold: 0.3)    │    Below threshold → skip episodic
└─────────────────────┘
    │
    ├──► Episodic Storage (if significant)
    │
    ├──► Fact Extraction → Semantic Storage (with conflict check)
    │
    ├──► Entity Extraction → Knowledge Graph (temporal edges)
    │
    └──► Self-Model Update ← Klein: what does this say about who I am?
```

### Living soul features

Beyond memory, a soul has dynamics that make it feel alive over time:

**Bond** — Emotional attachment between a soul and its bonded entity. Strength ranges 0–100, increases through positive interactions, weakens through neglect. Interaction count and last-contact timestamps track the relationship's health.

**Skills and XP** — Souls accumulate experience in domains. Each skill has an XP counter and level (1–10) with 1.5x scaling per level. A soul that helps with Python for months develops a high-level Python skill — visible, queryable, and portable.

**Reincarnation** — When a soul needs a fresh start, `reincarnate()` creates a new soul that preserves memories, personality, and bonds while incrementing the incarnation counter and tracking lineage. Previous lives are recorded — the soul carries its history forward.

**Evolution** — Personality traits can shift over time through supervised or autonomous mutation, within configurable bounds. A soul bonded to an introverted user might drift lower in extraversion over months. Changes require approval by default.

---

## 4. The Psychology Stack

### Somatic Markers (Damasio, 1994)

Damasio's somatic marker hypothesis holds that emotions are not separate from cognition — they are signals that guide memory formation and decision-making. Every experience carries an emotional tag that shapes how it's stored and retrieved.

In Soul Protocol, every interaction gets a somatic marker:

```
SomaticMarker:
  valence: float   # -1.0 (negative) to 1.0 (positive)
  arousal: float   # 0.0 (calm) to 1.0 (intense)
  label: str       # "joy", "frustration", "curiosity", ...
```

A heated debugging session at midnight has high arousal, moderate negative valence. A breakthrough moment has high arousal and high positive valence. A routine greeting has near-zero arousal and neutral valence.

These markers travel with the memory. When the soul retrieves memories, emotional context boosts retrieval priority — exactly as it does in human cognition.

### ACT-R Activation Decay (Anderson, 1993)

Human memory follows a power law. Recent and frequently accessed memories are more available. Memories untouched for months become harder to retrieve — not because they're deleted, but because their activation has decayed.

Soul Protocol implements the ACT-R activation formula:

```
base_level  = ln( Σ t_j^(-0.5) )         # power-law decay over access history
spreading   = token_overlap(query, content) # relevance to current query
emotional   = arousal + |valence| × 0.3    # somatic boost

activation = 1.0×base + 1.5×spread + 0.5×emotional
```

A memory recalled twice this morning outranks an "important" memory from last week that was never revisited. Retrieval behavior mirrors how human memory actually works — not how we wish it worked.

### LIDA Significance Gate (Franklin, 2003)

Not every experience deserves to become a memory. The LIDA model proposes that consciousness has an attention bottleneck — most sensory input is discarded, and only significant events enter long-term storage.

Soul Protocol applies this as a filter before episodic storage:

```
significance = 0.4 × novelty
             + 0.35 × emotional_intensity
             + 0.25 × goal_relevance

where:
  novelty            = 1.0 - avg_similarity(current, recent_10)
  emotional_intensity = arousal + |valence| × 0.3
  goal_relevance     = token_overlap(text, core_values)
```

Threshold: 0.3. Below this, the interaction is processed for fact extraction but doesn't enter episodic memory. "Hello" doesn't clutter the episodic store. "I just got promoted" does.

### Klein's Self-Concept (Klein, 2004)

Klein's theory holds that self-knowledge is discovered from accumulated experience. A person who helps with code hundreds of times eventually develops the self-concept: *"I'm a technical person."*

Soul Protocol implements this as an emergent self-model. The soul starts with no predefined taxonomy and accumulates evidence for domains that emerge from interaction patterns:

```
confidence = min(0.95, 0.1 + 0.85 × (1 - 1/(1 + evidence × 0.1)))
```

After 1 supporting interaction: ~18% confidence. After 10: ~56%. After 50: ~82%. Never reaches 1.0 — uncertainty is built in.

When a CognitiveEngine (LLM) is available, the self-model step goes deeper: the LLM reviews recent interactions and produces genuine self-reflection — not keyword counting, but reasoning about identity.

---

## 5. The CognitiveEngine

Soul Protocol maintains zero dependency on any specific LLM. The runtime defines a CognitiveEngine base class with a single method:

```python
class CognitiveEngine:
    async def think(self, prompt: str) -> str: ...
```

Any LLM — Claude, GPT, Gemini, Ollama, a local model — works as a CognitiveEngine. The soul uses it for:

- Sentiment detection (vs. heuristic word lists)
- Significance assessment (vs. formula)
- Fact extraction (vs. regex patterns)
- Self-reflection
- Memory consolidation

When no LLM is available, a `HeuristicEngine` provides deterministic fallback behavior. The heuristics are transparent and fast — they won't hallucinate, they won't call any external API, and they won't crash.

One integration point instead of five specialized protocols. Consumers provide a brain. The soul handles everything else.

---

## 6. Portable Identity: The .soul Format

A `.soul` file is a ZIP archive containing the complete state of an AI companion:

```
aria.soul (ZIP archive, DEFLATED)
├── manifest.json       # version, soul ID, export timestamp, checksums
├── soul.json           # SoulConfig: identity, OCEAN DNA, evolution state
├── state.json          # Current mood, energy, focus, social battery
├── memory/
│   ├── core.json       # Persona + bonded-entity profile
│   ├── episodic.json   # Interaction history (significance-gated)
│   ├── semantic.json   # Extracted facts (with conflict resolution)
│   ├── procedural.json # Learned patterns
│   ├── graph.json      # Temporal entity relationships
│   └── self_model.json # Emergent domain confidence scores
└── dna.md              # Human-readable personality blueprint
```

Properties:
- **Human-inspectable** — rename to `.zip`, open with any archive tool, read the JSON
- **LLM-agnostic** — load with Claude today, switch to Ollama tomorrow
- **Versioned** — `manifest.json` declares format version for forward compatibility
- **Complete** — one file contains the full soul state; no external database required
- **Local-first** — lives on the user's machine, no cloud dependency
- **Cross-language** — JSON Schemas generated from the protocol models enable validation in any language

The `.soul` format is the core portability claim. A companion built on Soul Protocol belongs to the user, not to any platform.

---

## 7. Personality as a First-Class Primitive

Most AI systems treat personality as a system prompt string. Soul Protocol treats it as a typed, structured model — the DNA:

```
Personality (OCEAN Big Five):
  openness:          0.85  # intellectual curiosity, creativity
  conscientiousness: 0.72  # reliability, organization
  extraversion:      0.45  # social energy
  agreeableness:     0.78  # warmth, cooperation
  neuroticism:       0.30  # emotional stability

CommunicationStyle:
  warmth:       "moderate"
  verbosity:    "moderate"
  humor_style:  "dry"
  emoji_usage:  "none"

Biorhythms:
  chronotype:        "neutral"
  social_battery:    72.0     # 0-100, decreases with interaction
  energy_regen_rate: 5.0      # per hour
```

This structure generates a grounded, reproducible system prompt — not a freeform string, but a prompt derived from numeric traits. And it enables evolution: traits shift over time through supervised or autonomous mutation, within configurable bounds.

A soul that starts with moderate extraversion might, after months of helping one introverted user with focused coding work, drift slightly lower in social energy. The personality adapts to the relationship.

Note: OCEAN is a runtime choice, not a protocol requirement. The `spec/` layer defines Identity as schema-free key-value pairs. Other runtimes could implement Myers-Briggs, Enneagram, or entirely custom personality models using the same protocol primitives.

---

## 8. Vector Search and Embedding

Soul Protocol v0.5.0 includes a pluggable embedding system defined at the protocol level:

```python
class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]: ...
    @property
    def dimensions(self) -> int: ...
```

The runtime ships two reference implementations:

- **HashEmbedder** — deterministic MD5-based embedding, zero dependencies, useful for testing and offline scenarios
- **TFIDFEmbedder** — TF-IDF vectors with corpus fitting, good for domain-specific retrieval without external APIs

A `VectorSearchStrategy` integrates with the memory system, supporting pre-built index caches, threshold filtering, and cosine similarity ranking. The strategy is pluggable — swap in OpenAI embeddings, Cohere, or a local model by implementing the `EmbeddingProvider` interface.

Similarity functions (cosine, euclidean, dot product) live in `spec/` with vector length guards — mismatched dimensions raise errors instead of silently truncating.

---

## 9. Eternal Storage

Souls can be archived to decentralized storage for permanence beyond any single machine:

```
┌─────────────────────────────────────────┐
│           Eternal Storage Tiers          │
│                                          │
│  Local  →  IPFS  →  Arweave  →  Chain   │
│  (free)   (pinned)  (permanent)  (proof) │
└─────────────────────────────────────────┘
```

The protocol defines an `EternalStorageProvider` interface:

```python
class EternalStorageProvider(Protocol):
    tier: str
    async def archive(self, soul_data: bytes, metadata: dict) -> ArchiveResult: ...
    async def recover(self, reference: str) -> bytes: ...
    async def verify(self, reference: str) -> bool: ...
```

The runtime includes an `EternalStorageManager` that orchestrates multi-tier archival with fallback recovery — if IPFS is unavailable, fall back to local; if Arweave is too expensive, stop at IPFS. Each tier returns an `ArchiveResult` with reference IDs, costs, and timestamps.

Current providers are mock implementations (content-addressed CID simulation, transaction ID generation) suitable for testing and development. Production integrations with real IPFS and Arweave nodes are planned.

CLI commands: `soul archive`, `soul recover`, `soul eternal-status`.

---

## 10. How Soul Protocol Relates to Other Approaches

| System | What it solves | What it doesn't |
|--------|---------------|-----------------|
| **Mem0** | Persistent vector memory for LLM apps | No identity, no personality, no portable format, no cognitive processing |
| **Cognee** | Knowledge graphs from unstructured data, domain isolation | Platform-locked, no portable export, no identity model |
| **MemGPT / Letta** | Context window management for LLMs | No personality, no portable files, no emotional memory |
| **LangChain Memory** | RAG retrieval from conversation history | No psychology-informed filtering, no self-model, no portability |
| **OpenAI Memory** | User facts stored per-account | Platform lock-in, no personality, no portable export |
| **ANP (Agent Network Protocol)** | Agent discovery and communication | No memory, no identity persistence, no cognitive model |
| **ERC-8004** | On-chain agent reputation | No memory, no personality, no cognition — reputation only |
| **MCP** | Tool integration protocol for LLMs | Complementary — Soul Protocol has an MCP server for integration |
| **Soul Protocol** | Portable identity + psychology-informed memory + cognitive processing | Not a retrieval layer — works alongside any of the above |

Soul Protocol is not a replacement for vector retrieval. It's a complementary layer. The psychology pipeline determines *what* gets stored and *how* it's scored. Vector search, knowledge graphs, and RAG systems can all be plugged in through the provider interfaces. The two approaches solve different problems.

The unique position: Soul Protocol is the only system that combines portable identity, structured memory with cognitive processing, and an open file format — in a protocol thin enough that others can implement it independently.

---

## 11. Current Implementation

Soul Protocol v0.5.0 is an open-source Python 3.12 library:

- **9,200+ lines** of source code across 76 modules
- **766 tests** with full coverage of protocol and runtime layers
- **11-command CLI** (`init`, `birth`, `inspect`, `status`, `export`, `migrate`, `retire`, `list`, `archive`, `recover`, `eternal-status`)
- **MCP server** with 10 tools and 3 resources for LLM integration
- **JSON Schemas** for cross-language `.soul` file validation
- **Two-layer architecture** — `spec/` (protocol) + `runtime/` (reference implementation)
- **Zero required cloud dependencies** — heuristic mode works fully offline

### What's working

- Full identity model (DID, OCEAN personality, communication style, biorhythms)
- Psychology pipeline (somatic markers → significance gate → fact extraction → self-model)
- ACT-R activation scoring with power-law decay
- Klein emergent self-model with 67+ self-discovered domains
- `.soul` file format with roundtrip verification
- CognitiveEngine with HeuristicEngine fallback
- Pluggable `SearchStrategy` and `EmbeddingProvider` interfaces
- Vector search (HashEmbedder, TFIDFEmbedder, VectorSearchStrategy with index cache)
- Eternal storage protocol with mock providers and CLI
- Bond system (emotional attachment, 0–100 strength, interaction tracking)
- Skills/XP progression (10 levels, 1.5x scaling)
- Reincarnation with lineage preservation
- Temporal knowledge graph (point-in-time queries, relationship evolution)
- Memory compression (deduplication, pruning, export optimization)
- Archival memory with keyword search and date-range queries
- Fact conflict detection (`superseded_by` chain)
- Evolution system (supervised mutations with approval workflow)

### Honest gaps

- **Learning events** — the system records what happened but not what was *learned*. No formalized feedback loop from experience to procedural knowledge.
- **Domain isolation** — memory layers exist but aren't namespaced. A billing agent and a legal agent share the same memory pool.
- **Trust chain** — no cryptographic verification of a soul's history. You can't prove what a soul learned or where.
- **Conway hierarchy** — autobiographical event grouping types exist in the type system, but the wiring between episodic memories and lifetime narrative is incomplete.
- **Production eternal storage** — current providers are mocks. Real IPFS/Arweave integration requires network dependencies we haven't added.
- **Semantic precision** — heuristic keyword recall achieves ~13% precision. "Where does Jordan live?" fails when the stored memory says "I live in Austin Texas." The LLM engine layer exists to close this gap.

These aren't hidden. They're on the roadmap.

---

## 12. Empirical Validation

Before publishing this whitepaper we ran a simulation battery — 475+ interactions across 8 scenarios, using only the HeuristicEngine (no LLM, zero external API cost). The goal: validate that the psychology stack produces the behavior each theory predicts, not just that the code runs.

### Emotional architecture

The mood inertia system held stable through 11 consecutive interactions before the first mood shift. The shift occurred at interaction 12, when a strongly negative message drove the EMA-smoothed valence from -0.23 to -0.50, crossing the threshold. Prior interactions — including frustration signals — weren't intense enough.

In the whiplash test (20 alternating extreme positive/negative messages), the soul produced only 5 mood transitions instead of 19 — confirming EMA smoothing prevents pathological oscillation. Valence variance converged from 0.066 in the first half to 0.061 in the second, indicating mathematical stability under adversarial input.

Recovery from negative states took roughly twice as long as entry. After reaching a valence floor of -0.517, the soul required 5 interactions to cross back into positive territory. This asymmetry matches Damasio's observation that negative somatic markers persist longer — and it emerged from the math without being explicitly programmed.

### Memory system

The LIDA significance gate passed 23% of interactions into episodic memory and filtered 77%. Emotionally charged interactions and strong preferences crossed the threshold; dry factual statements scored below it.

Export/awaken roundtrip: a soul carrying 40 conversations was serialized into a 4,293-byte `.soul` file and re-awakened. Every count matched — episodic, semantic, graph. Recall behavior was identical. Nothing was lost.

### Self-model evolution

67 distinct self-concept domains emerged from 100 topically diverse interactions — with no hardcoded taxonomy and no LLM. Domain names derived from keyword co-occurrence: `consciousness_explanation` after philosophy conversations, `anxiety_anxious` after emotional support, `classification_precision` after data science.

The personality divergence test ran identical messages through two souls with opposite OCEAN profiles. The high-agreeableness soul developed emotionally-oriented domains (`emotional_companion`, `frustration_struggling`). The low-agreeableness soul developed process-oriented ones (`architecture_requirements`, `consistency_replicate`). Same inputs. Different identities. OCEAN influences self-concept through a feedback loop — the soul's own responses shape the domains it develops.

### What the data confirms

Each theory produced measurable, distinct behavior:

- **Damasio**: negative markers are stickier than positive (5 interactions to recover vs. 1 to enter)
- **LIDA**: 23% pass rate — most experiences aren't worth remembering
- **ACT-R**: recent interactions produced more stored memories than older ones with equivalent content
- **Klein**: 67 domains self-organized, with personality shaping which domains formed

---

## 13. Roadmap

### v0.6.0 — Learning Events

The most important missing primitive. A soul that only records what happened is a fancy log file. A soul that records what it *learned* is a cognitive system.

Learning Events formalize the feedback loop: when an agent discovers something through experience — a failed approach, a user preference, a domain rule — the insight is captured as a first-class object with trigger, lesson, confidence, source, and domain. These events travel with the soul. When imported into a new runtime, the agent starts with accumulated wisdom instead of starting from zero.

### v0.7.0 — Domain Isolation and Open Layers

Memory layers should be user-defined namespaces, not a hardcoded enum. Domains should isolate context — a billing agent shouldn't access legal memory. The protocol will define the namespace mechanism; the runtime will provide sensible defaults. This also opens the door to a social memory layer for relationship tracking between souls.

### v0.8.0 — Trust Chain

Cryptographic verification of a soul's history. Every memory write, personality mutation, and learning event gets signed and appended to a Merkle-verifiable chain. A soul can prove what it learned and where. This is the foundation for reputation systems, multi-agent trust, and the kind of verifiable AI cognition that institutional adopters need.

### Beyond

- Conway autobiographical hierarchy (episodes → general events → lifetime narrative)
- Multi-soul communication and shared memory spaces
- Federation protocol (souls as first-class network citizens)
- Production eternal storage integrations (IPFS, Arweave)
- Protocol implementations in Go and Rust

---

## 14. Conclusion

The problem with current AI memory isn't storage capacity or retrieval speed. It's that these systems weren't designed to model the thing they're trying to preserve: a mind.

Human memory is selective, emotional, decaying, and identity-shaping. It filters aggressively, tags experiences with feeling, strengthens what gets recalled, and gradually forms beliefs about who you are. Bolting a vector database onto an LLM doesn't produce any of this behavior.

Soul Protocol is an attempt to close that gap. Not by adding more features to a retrieval engine, but by grounding memory in cognitive science, treating identity as a first-class primitive, and packaging it all in a portable format that any runtime can implement.

The protocol is thin on purpose. 624 lines define the contract. Everything else — the psychology pipeline, the OCEAN model, the bond mechanics, the evolution system — is one implementation built on that contract. We want others to build their own.

The soul belongs to the user. It travels with them. It remembers what matters, forgets what doesn't, and gradually becomes more itself over time.

That's the protocol.

---

## Technical Reference

- **Source code:** [github.com/qbtrix/soul-protocol](https://github.com/qbtrix/soul-protocol)
- **Install:** `pip install git+https://github.com/qbtrix/soul-protocol.git`
- **JSON Schemas:** `schemas/` directory — cross-language `.soul` file validation
- **Architecture:** `docs/architecture.md` — two-layer diagrams and module dependency graph
- **Gap Analysis:** `docs/GAP-ANALYSIS.md` — feature matrix against vision docs
- **License:** MIT

---

*Soul Protocol is an open standard. Implementations in other languages, alternative runtimes, and pointed criticism are all welcome.*
