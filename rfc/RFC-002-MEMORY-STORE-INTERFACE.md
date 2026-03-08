<!-- RFC-002-MEMORY-STORE-INTERFACE.md — Defines the MemoryStore protocol, 5-tier memory -->
<!-- architecture, ACT-R activation decay, query interface, and EmbeddingProvider protocol. -->

# RFC-002: Memory Store Interface

**Status:** Draft -- Open for feedback
**Author:** Soul Protocol Community
**Date:** 2026-03-08

## Summary

Memory is the foundation of persistent AI identity. Soul Protocol defines a `MemoryStore`
protocol at the spec layer with five operations (store, recall, search, delete, layers),
and a five-tier memory architecture at the runtime layer (core, episodic, semantic,
procedural, knowledge graph). Retrieval uses ACT-R activation-based scoring that
combines recency, frequency, query relevance, and emotional intensity. This RFC
documents the interface contracts, the tier structure, the activation formula, and
the pluggable `EmbeddingProvider` for vector search.

## Problem Statement

Most AI memory systems treat persistence as a retrieval problem: embed everything,
find the most similar text, stuff it into context. This misses what makes memory
feel real:

1. Not everything should be remembered (significance gating)
2. Memories should decay naturally (recency and frequency effects)
3. Emotional experiences should be more easily recalled (somatic markers)
4. Different kinds of knowledge need different storage patterns (facts vs. events vs. procedures)
5. Memory stores must be swappable (in-memory for testing, SQLite for production, vector DB for scale)

## Proposed Solution

### MemoryStore Protocol (Spec Layer)

The spec defines the minimal interface any memory backend must implement:

```python
@runtime_checkable
class MemoryStore(Protocol):
    """Interface for any memory backend."""

    def store(self, layer: str, entry: MemoryEntry) -> str:
        """Store a memory entry in the given layer. Returns the entry ID."""
        ...

    def recall(self, layer: str, *, limit: int = 10) -> list[MemoryEntry]:
        """Recall recent memories from a layer, newest first."""
        ...

    def search(self, query: str, *, limit: int = 10) -> list[MemoryEntry]:
        """Search across all layers by content. Returns best matches."""
        ...

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID. Returns True if found and deleted."""
        ...

    def layers(self) -> list[str]:
        """List all layer names that contain at least one memory."""
        ...
```

Key design decisions:
- **Layers are free-form strings**, not enums. Runtimes define their own namespaces.
- **Five operations only.** Store, recall, search, delete, list layers. No update -- memories are immutable (superseded, not modified).
- **`runtime_checkable`** so implementations can be verified with `isinstance()`.

### MemoryEntry (Spec Layer)

The atomic unit of memory:

```python
class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = ""
    layer: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
```

The runtime extends this with somatic markers, significance scores, access timestamps,
importance ratings, and supersession tracking.

### DictMemoryStore (Reference Implementation)

The spec ships a `DictMemoryStore` as the reference backend -- a simple dict keyed by
layer name with token-overlap search scoring:

```python
class DictMemoryStore:
    def store(self, layer: str, entry: MemoryEntry) -> str: ...
    def recall(self, layer: str, *, limit: int = 10) -> list[MemoryEntry]: ...
    def search(self, query: str, *, limit: int = 10) -> list[MemoryEntry]: ...
    def delete(self, memory_id: str) -> bool: ...
    def layers(self) -> list[str]: ...
    def count(self, layer: str | None = None) -> int: ...
    def all_entries(self) -> list[MemoryEntry]: ...
```

### Five-Tier Memory Architecture (Runtime)

The runtime organizes memory into five tiers, each with distinct semantics:

| Tier | Layer Name | Purpose | Cap |
|------|-----------|---------|-----|
| **Core** | `core` | Always-in-context persona + bonded-entity profile (~500 tokens each) | 2 entries |
| **Episodic** | `episodic` | Significant interaction events with somatic markers | 10,000 |
| **Semantic** | `semantic` | Extracted facts with confidence scores, conflict resolution | 1,000 |
| **Procedural** | `procedural` | Learned patterns and how-to knowledge | Uncapped |
| **Knowledge Graph** | `graph` | Entity-relationship triples with temporal edges | Uncapped |

Additionally, the runtime tracks a **self-model** (Klein's self-concept domains) and
**general events** (Conway hierarchy theme clusters) that sit alongside the five tiers.

### ACT-R Activation Decay

Retrieval scoring uses Anderson's ACT-R model, implemented in
`runtime/memory/activation.py`:

```python
# Base-level activation: B_i = ln(sum(t_j^(-d)))
# where t_j = seconds since access j, d = 0.5 (decay rate)

DECAY_RATE: float = 0.5
W_BASE: float = 1.0      # base-level activation weight
W_SPREAD: float = 1.5    # spreading activation weight
W_EMOTION: float = 0.5   # emotional boost weight
NOISE_SCALE: float = 0.1 # stochastic noise magnitude
```

The total activation for a memory combines four components:

```python
def compute_activation(entry, query, now=None, noise=True, strategy=None) -> float:
    # 1. Base-level: ACT-R power-law decay over access timestamps
    base = base_level_activation(entry.access_timestamps, now)

    # 2. Spreading: query relevance via token overlap or pluggable strategy
    spread = spreading_activation(query, entry.content, strategy=strategy)

    # 3. Emotional: arousal + |valence| from somatic markers (Damasio)
    emo = emotional_boost(entry.somatic)

    # 4. Combine with weights + optional Gaussian noise
    activation = (W_BASE * base) + (W_SPREAD * spread) + (W_EMOTION * emo)
    if noise:
        activation += random.gauss(0, NOISE_SCALE)
    return activation
```

This means a memory recalled twice today outranks an "important" memory from last week
that was never revisited -- matching human recall patterns.

### EmbeddingProvider Protocol (Spec Layer)

For vector-based search, the spec defines a pluggable embedding interface:

```python
@runtime_checkable
class EmbeddingProvider(Protocol):
    @property
    def dimensions(self) -> int:
        """Dimensionality of the embedding vectors."""
        ...

    def embed(self, text: str) -> list[float]:
        """Embed a single text string into a vector."""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts into vectors."""
        ...
```

The spec also provides pure-math similarity functions (no external dependencies):

- `cosine_similarity(a, b) -> float`
- `euclidean_distance(a, b) -> float`
- `dot_product(a, b) -> float`

The runtime ships `HashEmbedder` (locality-sensitive hashing) and `TFIDFEmbedder`
as built-in providers. Production deployments can plug in OpenAI, Cohere, or local
embedding models.

### SearchStrategy Protocol

The `SearchStrategy` protocol allows pluggable scoring for spreading activation:

```python
class SearchStrategy(Protocol):
    def score(self, query: str, content: str) -> float: ...
```

`VectorSearchStrategy` implements this using any `EmbeddingProvider`, bridging the
embedding interface into the activation scoring pipeline.

## Implementation Notes

- Spec memory primitives: `src/soul_protocol/spec/memory.py`
- Spec embedding protocol: `src/soul_protocol/spec/embeddings/protocol.py`
- Spec similarity functions: `src/soul_protocol/spec/embeddings/similarity.py`
- Runtime activation scoring: `src/soul_protocol/runtime/memory/activation.py`
- Runtime memory manager: `src/soul_protocol/runtime/memory/manager.py`
- Runtime recall engine: `src/soul_protocol/runtime/memory/recall.py`
- Runtime tier implementations: `runtime/memory/core.py`, `episodic.py`, `semantic.py`, `procedural.py`, `graph.py`

## Alternatives Considered

**Single flat memory store.** Simpler, but loses the semantic distinction between
facts, events, and procedures. Different tiers have different retention policies,
search strategies, and capacity limits.

**Async MemoryStore protocol.** The current protocol uses synchronous methods. An
async protocol would be more natural for database-backed stores, but would force
async on simple in-memory implementations. The runtime wraps sync stores in async
where needed.

**Mandatory vector search.** Requiring embeddings would improve search quality but
would force a dependency on embedding models. The current approach makes embeddings
optional -- token overlap works for small workloads.

## Open Questions

1. **Additional memory tiers?** Should the protocol define a working memory tier
   (volatile, current conversation) or an archival tier (compressed long-term storage)?
   Both are mentioned in the architecture doc as "not implemented."

2. **Custom decay functions?** Should consumers be able to provide their own decay
   function instead of the fixed ACT-R power-law? Use cases: faster forgetting for
   ephemeral agents, slower decay for knowledge-focused agents.

3. **Async MemoryStore?** Should the spec-layer protocol use `async def` for all
   operations, or provide both sync and async variants?

4. **Memory capacity management.** When episodic memory hits 10,000 entries, what
   happens? Currently the oldest/lowest-activation entries are dropped. Should this
   be configurable? Should dropped memories be archived rather than deleted?

5. **Cross-soul memory sharing.** Can two souls share a memory store? Use cases:
   shared knowledge base, collaborative learning. What are the isolation requirements?

## References

- Anderson, J.R. (2007). *How Can the Human Mind Occur in the Physical Universe?* -- ACT-R theory
- Damasio, A. (1994). *Descartes' Error* -- Somatic marker hypothesis
- Franklin, S. et al. (2016). *LIDA: A Systems-level Architecture for Cognition, Emotion, and Learning* -- Significance gating
- `src/soul_protocol/spec/memory.py` -- MemoryStore protocol definition
- `src/soul_protocol/spec/embeddings/protocol.py` -- EmbeddingProvider protocol
- `schemas/MemoryEntry.schema.json` -- cross-language validation schema
