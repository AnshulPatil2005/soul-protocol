# Soul Protocol: A Portable Standard for AI Companion Identity, Memory, Cognition, and Emotion

**Version 0.5.0**
**March 2026**

---

## Abstract

In 1995, Daniel Goleman argued that emotional intelligence matters more than IQ for human success. Thirty years later, AI memory systems still optimize purely for IQ. They treat persistence as a retrieval accuracy problem: find the most similar text, stuff it into context, move on. The emotional and cognitive dimensions that make memory human are ignored entirely.

Soul Protocol is an open standard for persistent AI companion identity. It combines a psychology-informed memory architecture with a portable file format. The protocol specification is 624 lines of Python. A reference runtime of 7,500+ lines implements one opinionated version of the spec. Other runtimes can implement it differently.

A companion's full state (personality, memories, emotional bonds, learned skills, knowledge graph) serializes into a `.soul` file. The file belongs to the user. It works with any LLM. It survives platform changes.

This paper describes the problem, the architecture, and the current implementation. It also describes what doesn't work yet.

---

## 1. The problem

### Stateless AI

Most AI assistants start every conversation from zero. Users re-explain their preferences, their context, their history. Not because the technology can't store it, but because persistent identity hasn't been treated as a design priority.

When memory does exist, it's bolted on. A vector database holds conversation chunks. A RAG pipeline retrieves them. A summarization buffer compresses recent turns. These solve retrieval. They don't solve identity.

### Retrieval is IQ. Memory is EQ.

Goleman distinguished between cognitive intelligence (IQ, the ability to process information) and emotional intelligence (EQ, the ability to process feeling, context, and relationships). Current AI memory systems are pure IQ. They ask: "What text is most similar to this query?"

But consider what actually determines whether a human memory sticks:

- A debugging session at 2am where something finally clicked. Emotionally charged, therefore memorable.
- A casual "hello" that happened 100 times. Trivially similar to any greeting query, but meaningless to store.
- A fact learned three months ago, recalled twice this week. More accessible than an "important" fact from last week that was never revisited.
- Repeated patterns of helping with code. Evidence that eventually forms a self-belief: *"I'm good at this."*

Cosine similarity captures none of this. Vector databases solve one problem well. Memory requires solving many problems at once. The missing ingredient isn't better retrieval. It's emotional and cognitive context.

### The portability gap

Where persistent memory does exist, it's locked to one platform. A companion's history lives in OpenAI's infrastructure, or Anthropic's memory layer, or a custom database tied to one application. Switch providers, start over. Change apps, start over.

Cognee builds knowledge graphs but locks them to its runtime. Mem0 offers vector retrieval without identity. ERC-8004 defines reputation without cognition. No existing system combines portable identity, structured memory, and cognitive processing in an open standard.

---

## 2. Design: protocol, not product

HTTP doesn't tell you how to build your website. It defines how data moves between client and server. The spec is small. The implementations are infinite.

Soul Protocol follows the same principle:

```
soul_protocol/
├── spec/      624 lines   THE PROTOCOL (portable, minimal, no opinions)
├── runtime/  7,495 lines  REFERENCE IMPLEMENTATION (opinionated, batteries-included)
├── cli/                    Command-line tools
└── mcp/                    Model Context Protocol server
```

**`spec/`** defines the primitives any runtime must implement: Identity, MemoryStore interface, MemoryEntry format, SoulContainer, `.soul` file pack/unpack, EmbeddingProvider interface, EternalStorageProvider interface, and similarity functions. It depends on Pydantic. Nothing else.

**`runtime/`** is one way to run the protocol. It implements OCEAN personality, five-tier memory with psychology-informed processing, knowledge graphs, a cognitive engine, emotional bonds, and skill progression. Other runtimes can implement the same `spec/` interfaces with entirely different approaches.

### What the protocol enforces

- Every soul has a unique identity
- Every memory entry has a timestamp, type, and content
- The `.soul` file format is standardized (ZIP archive, JSON payloads)
- Provider interfaces (memory, embedding, storage) are stable contracts
- Container operations (create, open, save) follow defined semantics

### What it does not

- No required personality model. OCEAN is a runtime choice.
- No required memory backend. In-memory, SQLite, Neo4j, whatever works.
- No required graph structure or embedding approach.
- No required layer names or domain isolation strategy.
- No required LLM provider.

The `spec/` layer is 624 lines of data models and interface definitions, designed for porting to Go or Rust. JSON Schemas are auto-generated from the protocol models, so any language with a JSON Schema validator can read and write `.soul` files today without the Python SDK.

---

## 3. Architecture

### Five-tier memory

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

**Core memory** is always loaded. The persona, the companion's values, the profile of who it's bonded to. Edits replace rather than append, the way core beliefs update.

**Episodic memory** stores interactions that pass the significance gate. Routine exchanges don't make it in. Emotionally salient or novel experiences do.

**Semantic memory** stores extracted facts: names, preferences, work context. Facts are deduplicated and conflict-checked. When new information contradicts old, the older fact is marked `superseded_by` rather than silently overwritten.

**Procedural memory** stores learned patterns. How this person likes explanations. What approaches work.

**The knowledge graph** links entities with temporal edges. Each relationship carries `valid_from` and `valid_to` timestamps, so you can query what the soul knew about a topic at any point in time, and track how relationships evolved.

**Archival memory** compresses old conversations. Summaries and key moments remain searchable by keyword and date range. A compression pipeline handles deduplication and importance-based pruning.

### The observe() pipeline

Every interaction passes through a processing pipeline before storage:

```
User input + Agent output
    │
    ▼
┌─────────────────────┐
│  Sentiment Detection │  Damasio: tag emotional context
│  (somatic markers)   │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  Significance Gate   │  LIDA: is this worth remembering?
│  (threshold: 0.3)    │  Below threshold, skip episodic
└─────────────────────┘
    │
    ├──> Episodic Storage (if significant)
    ├──> Fact Extraction -> Semantic Storage (with conflict check)
    ├──> Entity Extraction -> Knowledge Graph (temporal edges)
    └──> Self-Model Update: Klein, what does this say about who I am?
```

This pipeline is the EQ layer. It decides not just *what* to store, but *whether* to store, *how* to feel about it, and *what it means* for the soul's sense of self. Retrieval-only systems skip all of this.

### Bond, skills, reincarnation

A soul isn't static. It has dynamics that change over time:

**Bond.** Emotional attachment to a bonded entity. Strength ranges 0 to 100, increases through positive interactions, weakens through neglect. Interaction count and last-contact timestamps track the relationship.

**Skills and XP.** Souls accumulate experience in domains. Each skill has an XP counter and level (1 to 10, 1.5x scaling per level). A soul that helps with Python for months develops a visible, queryable, portable Python skill.

**Reincarnation.** A soul can be reborn. `reincarnate()` creates a new soul that preserves memories, personality, and bonds while incrementing the incarnation counter. Previous lives are recorded. The soul carries its history forward.

**Evolution.** Personality traits shift over time through supervised or autonomous mutation, within configurable bounds. A soul bonded to an introverted user might drift lower in extraversion over months. Changes require approval by default.

---

## 4. The psychology stack: EQ for AI

Goleman identified five components of emotional intelligence: self-awareness, self-regulation, motivation, empathy, and social skill. Soul Protocol doesn't implement all five. But it implements the memory and cognition foundations that make them possible, grounded in four established theories.

### Somatic markers (Damasio, 1994)

Damasio's somatic marker hypothesis: emotions aren't separate from cognition. They're signals that guide memory formation and decision-making. A bad experience leaves a "gut feeling" that shapes future choices before conscious reasoning kicks in.

In Soul Protocol, every interaction gets a somatic marker:

```
SomaticMarker:
  valence: float   # -1.0 (negative) to 1.0 (positive)
  arousal: float   # 0.0 (calm) to 1.0 (intense)
  label: str       # "joy", "frustration", "curiosity", ...
```

A heated debugging session at midnight: high arousal, moderate negative valence. A breakthrough: high arousal, high positive valence. A routine greeting: near-zero on both axes.

These markers travel with the memory. Emotional context boosts retrieval priority. This is how human memory works. You remember what you felt, and what you felt determines what you can recall.

### ACT-R activation decay (Anderson, 1993)

Human memory follows a power law. Recent and frequently accessed memories are more available. Old, untouched memories fade. Not deleted, just harder to reach.

The implementation:

```
base_level  = ln( Σ t_j^(-0.5) )          # power-law decay over access history
spreading   = token_overlap(query, content) # relevance to current query
emotional   = arousal + |valence| × 0.3    # somatic boost

activation = 1.0 × base + 1.5 × spread + 0.5 × emotional
```

A memory recalled twice this morning outranks an "important" memory from last week that was never revisited. This is the opposite of how most AI memory systems work, where importance is a static score assigned once at storage time.

### LIDA significance gate (Franklin, 2003)

Not everything deserves to become a memory. The LIDA model proposes an attention bottleneck: most input is discarded, only significant events enter long-term storage.

```
significance = 0.4 × novelty
             + 0.35 × emotional_intensity
             + 0.25 × goal_relevance
```

Threshold: 0.3. Below this, fact extraction still runs, but the interaction doesn't enter episodic memory. "Hello" doesn't clutter the store. "I just got promoted" does.

This gate is the primary defense against memory bloat in long-running companions. It's also the clearest example of EQ over IQ: the system decides what matters based on emotional and contextual signals, not text similarity.

### Klein's self-concept (Klein, 2004)

Klein's theory: self-knowledge isn't programmed in. It's discovered from accumulated experience. Someone who helps with code hundreds of times develops the self-concept "I'm a technical person." This belief then shapes how they interpret future interactions.

The soul starts with no taxonomy. Domains emerge from interaction patterns:

```
confidence = min(0.95, 0.1 + 0.85 × (1 - 1/(1 + evidence × 0.1)))
```

After 1 supporting interaction: ~18% confidence. After 10: ~56%. After 50: ~82%. The curve never reaches 1.0. Uncertainty is permanent.

When an LLM is available, the self-model step uses it for genuine reflection, reasoning about identity rather than counting keywords.

---

## 5. The CognitiveEngine

The runtime defines a CognitiveEngine base class:

```python
class CognitiveEngine:
    async def think(self, prompt: str) -> str: ...
```

Any LLM works. Claude, GPT, Gemini, Ollama, a local model. The soul uses it for sentiment detection, significance assessment, fact extraction, self-reflection, and memory consolidation.

When no LLM is available, a `HeuristicEngine` provides deterministic fallback. Word-list sentiment, formula-based significance, regex fact extraction. The heuristics won't hallucinate, won't call external APIs, and won't crash.

One integration point. Consumers provide a brain. The soul handles the rest.

---

## 6. The .soul file format

A `.soul` file is a ZIP archive:

```
aria.soul (ZIP, DEFLATED)
├── manifest.json       # version, soul ID, export timestamp, checksums
├── soul.json           # SoulConfig: identity, DNA, evolution state
├── state.json          # current mood, energy, focus, social battery
├── memory/
│   ├── core.json       # persona + bonded-entity profile
│   ├── episodic.json   # interaction history (significance-gated)
│   ├── semantic.json   # extracted facts (with conflict resolution)
│   ├── procedural.json # learned patterns
│   ├── graph.json      # temporal entity relationships
│   └── self_model.json # emergent domain confidence scores
└── dna.md              # human-readable personality blueprint
```

Rename it to `.zip`. Open it with any archive tool. Read the JSON. Load it with Claude today, Ollama tomorrow. One file, full state, no external database, no cloud dependency.

JSON Schemas generated from the protocol models enable validation in any language. You don't need the Python SDK to work with `.soul` files.

---

## 7. Personality

Most AI systems treat personality as a system prompt string. Soul Protocol treats it as structured data:

```
Personality (OCEAN Big Five):
  openness:          0.85
  conscientiousness: 0.72
  extraversion:      0.45
  agreeableness:     0.78
  neuroticism:       0.30

CommunicationStyle:
  warmth:       "moderate"
  verbosity:    "moderate"
  humor_style:  "dry"
  emoji_usage:  "none"

Biorhythms:
  chronotype:        "neutral"
  social_battery:    72.0
  energy_regen_rate: 5.0
```

Numeric traits generate a reproducible system prompt. Traits can shift over time through supervised mutation. A soul bonded to an introverted user for months might drift lower in extraversion. The personality adapts to the relationship.

OCEAN is a runtime choice, not a protocol requirement. The `spec/` layer defines Identity as schema-free key-value pairs. Other runtimes can use Myers-Briggs, Enneagram, or something custom.

---

## 8. Vector search and embedding

The protocol defines a pluggable embedding interface:

```python
class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]: ...
    @property
    def dimensions(self) -> int: ...
```

The runtime ships two reference implementations: a deterministic MD5-based HashEmbedder (zero dependencies, good for testing) and a TF-IDF embedder (corpus-fitted, good for domain-specific retrieval without external APIs).

A `VectorSearchStrategy` connects embeddings to the memory system with index caching, threshold filtering, and cosine similarity ranking. Swap in OpenAI embeddings, Cohere, or a local model by implementing the interface.

Similarity functions (cosine, euclidean, dot product) live in `spec/` with vector length guards. Mismatched dimensions raise errors instead of silently truncating.

---

## 9. Eternal storage

Souls can be archived to decentralized storage:

```
Local  ->  IPFS  ->  Arweave  ->  Chain
(free)   (pinned)  (permanent)  (proof)
```

The protocol defines an `EternalStorageProvider` interface with `archive()`, `recover()`, and `verify()` methods. The runtime includes an `EternalStorageManager` that orchestrates multi-tier archival with fallback recovery.

Current providers are mocks (content-addressed CID simulation, transaction ID generation) for testing. Production IPFS and Arweave integrations are planned.

CLI: `soul archive`, `soul recover`, `soul eternal-status`.

---

## 10. Comparison

| System | Solves | Doesn't solve |
|--------|--------|---------------|
| Mem0 | Persistent vector memory | Identity, personality, portability, cognitive processing |
| Cognee | Knowledge graphs, domain isolation | Portability, identity, emotional memory |
| MemGPT / Letta | Context window management | Personality, portable files, emotional memory |
| LangChain Memory | RAG retrieval | Significance filtering, self-model, portability |
| OpenAI Memory | User facts per-account | Platform lock-in, personality, portable export |
| ANP | Agent discovery, communication | Memory, identity persistence, cognition |
| ERC-8004 | On-chain agent reputation | Memory, personality, cognition |
| MCP | Tool integration for LLMs | Complementary. Soul Protocol ships an MCP server. |

Soul Protocol is not a retrieval replacement. It's a layer that sits alongside retrieval. The psychology pipeline decides *what* to store and *how* to score it. Vector search, graphs, and RAG plug in through provider interfaces.

---

## 11. Current implementation

Python 3.12. Open source. MIT license.

- 9,200+ lines across 76 modules
- 766 tests
- 11-command CLI
- MCP server (10 tools, 3 resources)
- JSON Schemas for cross-language validation
- Two-layer architecture: `spec/` + `runtime/`
- Zero required cloud dependencies

### Working

- Identity model (DID, OCEAN personality, communication style, biorhythms)
- Psychology pipeline (somatic markers, significance gate, fact extraction, self-model)
- ACT-R activation scoring with power-law decay
- Klein emergent self-model (67+ self-discovered domains in testing)
- `.soul` file roundtrip (pack, unpack, verify)
- CognitiveEngine with HeuristicEngine fallback
- Pluggable SearchStrategy and EmbeddingProvider
- Vector search (HashEmbedder, TFIDFEmbedder, VectorSearchStrategy)
- Eternal storage protocol with mock providers
- Bond system (0 to 100 strength, interaction tracking)
- Skills/XP (10 levels, 1.5x scaling)
- Reincarnation with lineage
- Temporal knowledge graph (point-in-time queries, relationship evolution)
- Memory compression (dedup, pruning, export optimization)
- Archival memory (keyword search, date-range queries)
- Fact conflict detection (superseded_by chain)
- Evolution (supervised mutations, approval workflow)

### Not working yet

**Learning events.** The system records what happened, not what was *learned*. No formalized feedback loop from experience to procedural knowledge. A soul that fails at a task and a soul that succeeds store the same kind of memory. They shouldn't.

**Domain isolation.** Memory layers exist but aren't namespaced. A billing agent and a legal agent share the same pool. They shouldn't.

**Trust chain.** No cryptographic verification of history. You can't prove what a soul learned or where it learned it.

**Conway hierarchy.** The types for autobiographical event grouping exist. The wiring between episodic memories and lifetime narrative doesn't.

**Production eternal storage.** Providers are mocks. Real IPFS/Arweave integration needs network dependencies that aren't in place.

**Semantic precision.** Heuristic keyword recall hits ~13%. "Where does Jordan live?" fails when the stored memory says "I live in Austin Texas" because there's no keyword overlap. The LLM engine layer closes this gap, but without an LLM, retrieval is limited.

---

## 12. Empirical validation

We ran 475+ interactions across 8 scenarios using only the HeuristicEngine. No LLM, no external API, zero cost. The goal was to confirm that each theory in the psychology stack produces the behavior it predicts.

### Emotional architecture

The mood system held stable through 11 consecutive interactions before shifting. The shift came at interaction 12, when a strongly negative message pushed the EMA-smoothed valence from -0.23 to -0.50, crossing threshold. Prior frustration signals weren't intense enough.

In the whiplash test (20 alternating extreme positive/negative messages), the soul made 5 mood transitions instead of 19. EMA smoothing prevented oscillation. Valence variance converged from 0.066 to 0.061 across halves.

Recovery from negative states took roughly twice as long as entry. After hitting a valence floor of -0.517, the soul needed 5 interactions to return to positive territory. This asymmetry matches Damasio: negative somatic markers are stickier than positive ones. The behavior emerged from the math. It wasn't explicitly programmed.

### Memory

The LIDA gate passed 23% of interactions into episodic memory. 77% were filtered. Emotionally charged interactions and strong preferences got through. Dry factual statements didn't.

A soul carrying 40 conversations serialized into a 4,293-byte `.soul` file. After re-awakening: every count matched (episodic, semantic, graph). Recall behavior was identical. Nothing lost in transit.

### Self-model

67 distinct self-concept domains emerged from 100 diverse interactions. No hardcoded taxonomy. No LLM. Domain names came from keyword co-occurrence: `consciousness_explanation` after philosophy conversations, `anxiety_anxious` after emotional support, `classification_precision` after data science.

Two souls with opposite OCEAN profiles received identical messages. The high-agreeableness soul developed emotionally-oriented domains (`emotional_companion`, `frustration_struggling`). The low-agreeableness soul developed process-oriented ones (`architecture_requirements`, `consistency_replicate`). Same inputs, different identities. Personality shapes self-concept through a feedback loop: the soul's own responses determine which domains form.

### Summary

- **Damasio**: negative markers stickier than positive (5 interactions to recover vs. 1 to enter)
- **LIDA**: 23% pass rate. Most experiences aren't worth remembering.
- **ACT-R**: recent interactions produced more stored memories than older ones with equivalent content
- **Klein**: 67 domains self-organized. Personality determined which ones.

---

## 13. Roadmap

### v0.6.0: Learning events

A soul that only records what happened is a log file. A soul that records what it *learned* is a cognitive system.

Learning Events formalize the feedback loop. When an agent discovers something through experience (a failed approach, a user preference, a domain rule) the insight gets captured with trigger, lesson, confidence, source, and domain. These events travel in the `.soul` file. When imported into a new runtime, the agent starts with accumulated knowledge instead of from zero.

### v0.7.0: Domain isolation and open layers

Memory layers should be user-defined namespaces, not a hardcoded enum. Domains should isolate context: a billing agent shouldn't see legal memory. The protocol defines the namespace mechanism. The runtime provides defaults.

### v0.8.0: Trust chain

Cryptographic verification of a soul's history. Every memory write, personality mutation, and learning event gets signed and appended to a Merkle-verifiable chain. A soul can prove what it learned, when, and from what source.

### Beyond

- Conway autobiographical hierarchy (episodes to general events to lifetime narrative)
- Multi-soul communication and shared memory
- Federation protocol
- Production IPFS/Arweave integration
- Protocol implementations in Go and Rust

---

## 14. Conclusion

The problem with current AI memory isn't storage capacity or retrieval speed. These systems weren't designed to model a mind. They were designed to model a search engine.

Human memory is selective. It tags experiences with feeling. It strengthens what gets recalled and lets the rest fade. It gradually forms beliefs about who you are. A vector database bolted onto an LLM does none of this.

Goleman's argument was that the qualities that make humans effective aren't cognitive, they're emotional: self-awareness, the ability to read context, the capacity to learn from experience rather than just store it. The same argument applies to AI companions. The ones that will feel real, that users will actually bond with, won't be the ones with the best retrieval precision. They'll be the ones that remember what matters, forget what doesn't, and slowly become more themselves.

The protocol is 624 lines. Everything else is one implementation. We want others to build their own.

---

## References

- Goleman, D. (1995). *Emotional Intelligence: Why It Can Matter More Than IQ.* Bantam Books.
- Damasio, A. (1994). *Descartes' Error: Emotion, Reason, and the Human Brain.* Putnam.
- Anderson, J.R. (1993). *Rules of the Mind.* Lawrence Erlbaum Associates.
- Franklin, S. et al. (2003). *IDA: A Cognitive Agent Architecture.* IEEE International Conference on Systems, Man and Cybernetics.
- Klein, S.B. (2004). *The Cognitive Neuroscience of Knowing One's Self.* In M.S. Gazzaniga (Ed.), The Cognitive Neurosciences III.

## Technical reference

- Source: [github.com/qbtrix/soul-protocol](https://github.com/qbtrix/soul-protocol)
- Install: `pip install git+https://github.com/qbtrix/soul-protocol.git`
- Schemas: `schemas/` directory
- Architecture: `docs/architecture.md`
- License: MIT

---

*Soul Protocol is an open standard. Implementations in other languages, alternative runtimes, and criticism are welcome.*
