<!--
  SPEC.md — Soul Protocol, the standard.
  Created: 2026-04-19 (feat/0.3.3-prune-retrieval-infra) — companion to the
  0.3.3 retrieval prune. This doc describes what Soul Protocol IS, as a
  standard, independent of our Python reference implementation. Anyone
  implementing Soul Protocol in another language (or a custom runtime)
  reads this file.

  Runtime implementation details — algorithms, SQLite schemas, async
  strategies, test patterns — belong in docs/architecture.md, not here.
-->

# Soul Protocol — The Standard

> Soul Protocol is a portable, open standard for persistent AI identity, memory, and retrieval. This document is language-agnostic. It describes what Soul Protocol is, independent of how our Python reference implementation happens to build it.

Version: **0.3.3** (spec) · Status: **draft, breaking-change-free since 0.3**

If you are **building on top of our Python implementation**, start with [README.md](../README.md) and [docs/architecture.md](./architecture.md). If you are **implementing Soul Protocol in another language** (Rust, Go, TypeScript, etc.) or a custom runtime, this document is the authoritative contract.

---

## 1 · What Soul Protocol is

Three concerns bundled into one standard:

1. **Identity** — every soul has a DID, a persona, OCEAN personality traits, values, and an evolution history.
2. **Memory** — five tiers (core, episodic, semantic, procedural, graph) with psychology-informed activation semantics.
3. **Event substrate** — an append-only journal that records every consequential change to a soul or an org, scope-stamped and tamper-evident.

A **.soul file** carries (1) and the relevant memory slice of (2) — it is a zip archive that any Soul Protocol implementation can read, write, and export from. An **org journal** carries (3) — a single SQLite database (or equivalent) that sits alongside one or more souls.

Everything else the reference implementation ships — psychology pipeline algorithms, retrieval orchestration, MCP server, CLI, web UI — is a *consumer* of this standard, not part of it.

---

## 2 · The `.soul` file format

A `.soul` file is a ZIP archive with a fixed directory layout. Any implementation must be able to read and write this layout.

```
<name>.soul/
├── identity.json         — Identity (below)
├── dna.json              — DNA (personality traits + communication style + biorhythms)
├── memory/
│   ├── core.jsonl        — MemoryEntry records, tier=core
│   ├── episodic.jsonl    — MemoryEntry records, tier=episodic
│   ├── semantic.jsonl    — MemoryEntry records, tier=semantic
│   ├── procedural.jsonl  — MemoryEntry records, tier=procedural
│   └── graph.jsonl       — MemoryEntry records, tier=graph (entity relationships)
├── skills/
│   └── <skill_name>.md   — Procedural capabilities with XP tracking
├── bonds/
│   └── <bond_id>.json    — Relationship state (BondTarget records)
├── evolution.jsonl       — Append-only history of personality / trait mutations
└── manifest.json         — Container-level metadata (schema_version, created_at, owner)
```

**Invariants a conforming implementation must honor:**

- All timestamps in files are ISO-8601 with timezone offset (UTC recommended). Naive datetimes are invalid.
- JSONL files use one record per line, UTF-8, LF line endings, trailing newline optional.
- `manifest.json` includes `schema_version: "0.3.3"` (or the version the file was written against).
- A reader encountering a `schema_version` newer than it supports must fail loud, not silently drop fields.
- File-level mutations are additive within a version: new fields may appear but existing fields do not disappear or change meaning without a major version bump.

See `soul_protocol.spec.soul_file` in the reference impl for `pack_soul()` / `unpack_soul()` / `unpack_to_container()` — the codec surface any implementation must reproduce.

---

## 3 · Identity

```
Identity {
  did:         str     # "did:soul:<slug>" — stable across exports
  name:        str
  persona:     str     # short description agents inject into their own prompts
  values:      [str]   # free-form value strings, e.g. ["sovereignty", "accessibility"]
  created_at:  datetime
}
```

`did` is the canonical handle. It must be stable across `.soul` export / import cycles. The slug portion is locally unique within an org.

---

## 4 · Memory

### 4.1 · The five tiers

A `MemoryEntry` belongs to exactly one tier. The tiers are:

| Tier | Meaning | When to write |
|---|---|---|
| `core` | Identity-level facts always in context ("who am I") | Rarely — these are load-bearing |
| `episodic` | Events that happened ("what occurred at time T") | Most interactions |
| `semantic` | General knowledge ("what I know") | Facts the soul should recall, not events |
| `procedural` | How-to knowledge, recipes, procedures | Skills, learned patterns |
| `graph` | Entity relationships (soul→entity→entity edges) | Links between people, orgs, concepts |

### 4.2 · MemoryEntry

```
MemoryEntry {
  id:           UUID
  tier:         Literal["core", "episodic", "semantic", "procedural", "graph"]
  content:      str
  importance:   float        # 0.0..10.0, caller-assigned baseline
  scope:        [str]        # DSP scope patterns — see §7
  visibility:   MemoryVisibility   # "private" | "shared" | "public"
  created_at:   datetime
  emotion:      str | None   # optional emotional tag
  access_count: int          # incremented on recall
  last_accessed_at: datetime | None
  metadata:     dict[str, Any]
}
```

### 4.3 · Psychology-informed activation (outputs, not algorithms)

When an implementation writes a memory, it must compute and record (directly or via metadata):

- **Somatic marker** — emotional valence of the write event. The reference impl uses Damasio's somatic-marker theory; other impls may derive this differently. Required: a scalar the recall phase can use.
- **Activation** — starts at 1.0 on write, decays over time. The reference impl uses ACT-R's decay; other impls may use different decay curves. Required: activation decreases monotonically absent re-access.
- **Significance** — a gate that filters "trivial" memories from expensive downstream operations (dream consolidation, graph edges). The reference impl uses LIDA-style global workspace scoring; other impls may use simpler heuristics. Required: memories have a boolean or scalar "significant enough" flag.

These are spec *outputs*, not spec *algorithms*. A Rust implementation does not need to port Damasio/ACT-R/LIDA line-for-line. It needs to produce comparable outputs so merged souls behave consistently across implementations.

### 4.4 · Recall contract

```
recall(query: str, *, limit: int, min_importance: float = 0) -> list[MemoryEntry]
```

- Results ordered by descending relevance × activation × importance (relative weighting up to implementation).
- `access_count` and `last_accessed_at` updated on every return.
- Filtering by `scope` (caller's scope context) applied before limit and ranking.

---

## 5 · DNA (personality)

```
DNA {
  ocean:               OCEAN     # openness, conscientiousness, extraversion, agreeableness, neuroticism (0..1)
  communication_style: CommunicationStyle  # verbosity, formality, humor, directness (0..1)
  biorhythms:          Biorhythms | None   # circadian preferences
  values:              [str]
  emotional_baseline:  Mood
}
```

DNA is the slow-moving part of identity. It is mutated through the **evolution** subsystem — see §6.

---

## 6 · Evolution

Evolution is how souls change over time without losing portability. Every mutation is an append-only `EvolutionEvent` recorded in `evolution.jsonl`.

```
EvolutionEvent {
  id:          UUID
  ts:          datetime
  kind:        Literal["trait_mutation", "skill_level_up", "bond_deepened", ...]
  before:      dict            # previous state of the mutated field
  after:       dict            # new state
  trigger:     str             # free-form cause description
  importance:  float
}
```

An implementation may apply its own triggers, thresholds, and mutation strategies. What it must not do is mutate DNA, skills, or bonds silently — every change is recorded here.

---

## 7 · Scope grammar

Soul Protocol uses a dotted, wildcard-capable scope string.

```
<segment>         ::= [a-z0-9_-]+
<scope>           ::= <segment> ( ":" <segment> )* ( ":*" )?
<example>         ::= "org:sales:leads"
                  ::= "org:sales:*"
                  ::= "user:alice"
                  ::= "fleet:hospitality:front-desk"
```

**Matching rule:** scope A matches scope B if A == B, or if one is a prefix of the other where the longer side ends in `*`. Wildcard-grant + specific-requester matches. Specific-grant + wildcard-requester matches. Disjoint scopes do not match.

All writes to the journal carry a non-empty `scope` list. All reads filter by caller scope context before aggregation.

---

## 8 · The Journal

### 8.1 · Append-only, hash-chained, UTC-stamped

The org journal is the substrate that every Soul Protocol consumer (pocketpaw, future Rust runtimes, third-party agents) writes to for consequential events.

```
EventEntry {
  id:              UUID
  ts:              datetime             # tz-aware UTC
  actor:           Actor                # kind + id + scope_context
  action:          str                  # dot-separated, past-tense, e.g. "memory.semantic.added"
  scope:           [str]                # MUST be non-empty
  causation_id:    UUID | None          # which event caused this one
  correlation_id:  UUID | None          # groups related events (a request, an install, etc.)
  payload:         dict | DataRef       # JSON-serializable; no Pydantic/class values
  prev_hash:       bytes | None         # hash link to previous entry
  sig:             bytes | None         # optional signature
  seq:             int                  # auto-incremented on append
}

Actor {
  kind:          str                    # "user" | "system" | "service"
  id:            str                    # stable identifier, e.g. "user:alice", "system:widget-graduation"
  scope_context: [str]                  # caller's scopes at the time
}
```

### 8.2 · Invariants

- No UPDATE, no DELETE, no truncate. Rows are written once, read forever.
- `ts` is timezone-aware UTC. Naive datetimes raise at validation time.
- `scope` is required and non-empty. No implicit "global" write path.
- `action` is a free-form dot-separated string. The reference impl ships `ACTION_NAMESPACES` as a catalog, but implementations may add new namespaces additively.
- `payload` is JSON-serializable — plain `dict` or a typed `DataRef` (see §9). Never a class instance.
- `seq` is monotonic and unique. A writer appending to the journal receives the committed `EventEntry` back — see §8.3.
- `prev_hash` forms a hash chain. An implementation may verify the chain on read; any break indicates tampering or corruption.

### 8.3 · Journal contract (0.3.3)

```
append(entry: EventEntry) -> EventEntry    # returns the committed entry w/ seq + prev_hash
query(
    *,
    action: str | None = None,
    action_prefix: str | None = None,      # added 0.3.3 — prefix match on dot-separated action
    actor_kind: str | None = None,
    actor_id: str | None = None,
    correlation_id: UUID | None = None,
    causation_id: UUID | None = None,
    since_seq: int = 0,
    until_seq: int | None = None,
    since_ts: datetime | None = None,
) -> Iterable[EventEntry]
replay_from(since_seq: int = 0) -> Iterable[EventEntry]
```

Implementations may add query dimensions (e.g., scope, payload-field) but must support the above at minimum.

### 8.4 · DataRef (journal-layer — query recipe)

Journal payloads may contain a `DataRef` instead of an inline `dict` when the data lives outside the journal and should be resolved on demand:

```
DataRef {
  source:         str              # adapter name, e.g. "drive", "salesforce"
  query:          str | None
  scopes:         [str]
  point_in_time:  datetime | None  # UTC
}
```

See also §9 for the **retrieval-layer** `DataRef`, which identifies a specific candidate returned by a `SourceAdapter`. The two share a name because they share the concept "pointer to external data" but operate at different granularities.

---

## 9 · Retrieval

The spec defines the vocabulary. Concrete routers, brokers, and adapters live in the consuming runtime.

### 9.1 · RetrievalRequest

```
RetrievalRequest {
  query:           str                # free-text or source-native query
  actor:           Actor
  scopes:          [str]              # caller's scope context, non-empty
  correlation_id:  UUID | None
  sources:         [str] | None       # explicit allowlist, or all-registered if None
  limit:           int                # default 20
  strategy:        Literal["first", "parallel", "sequential"]  # default "parallel"
  timeout_s:       float              # default 10.0
  point_in_time:   datetime | None    # UTC. Added 0.3.3 — native time-travel field
}
```

### 9.2 · RetrievalCandidate + DataRef (retrieval-layer)

> **Naming note.** The retrieval-layer `DataRef` is re-exported from `soul_protocol.spec` as `RetrievalDataRef` to distinguish it from the journal-layer `DataRef` (see §8.4, query recipe used in `EventEntry.payload`). Inside `spec/retrieval.py` itself it is named `DataRef`; at the `soul_protocol.spec` package boundary it surfaces as `RetrievalDataRef`. Language bindings should expose both names so consumers can disambiguate. The two types are intentionally distinct: the journal `DataRef` is "resolve this query at this moment," the retrieval `DataRef` is "this specific record from this source at this revision."


```
RetrievalCandidate {
  source:   str
  content:  dict | DataRef            # DataRef for zero-copy, dict for projection sources
  score:    float | None
  as_of:    datetime                  # UTC
  cached:   bool
}

DataRef {
  kind:         Literal["dataref"]
  source:       str
  id:           str                   # stable identifier in the source system
  scopes:       [str]
  revision_id:  str | None            # point-in-time identifier
  extra:        dict
}
```

### 9.3 · Protocols

```
SourceAdapter (Protocol) {
  supports_dataref: bool

  query(request: RetrievalRequest, credential: Credential | None)
    -> list[RetrievalCandidate]
}

AsyncSourceAdapter (Protocol) {
  query(...)                          # sync method present too
  async aquery(request, credential) -> list[RetrievalCandidate]   # 0.3.3
}

CredentialBroker (Protocol) {
  acquire(source: str, scopes: [str]) -> Credential
  ensure_usable(credential: Credential, requester_scopes: [str]) -> None
  mark_used(credential: Credential) -> None
  revoke(credential_id: UUID) -> None
}
```

### 9.4 · Credential

```
Credential {
  id:            UUID
  source:        str
  scopes:        [str]        # non-empty
  token:         str          # opaque bearer
  acquired_at:   datetime     # UTC
  expires_at:    datetime     # UTC
  last_used_at:  datetime | None
}
```

### 9.5 · Exception hierarchy

```
RetrievalError              (base)
├── NoSourcesError          (no registered source matched scopes/list)
├── SourceTimeoutError      (adapter did not return within timeout)
├── CredentialScopeError    (credential used outside its scope)
├── CredentialExpiredError  (credential used after TTL elapsed)
└── PointInTimeNotSupported (adapter can't honor time-travel field; router records and continues)
```

### 9.6 · What is not in the spec

- `RetrievalRouter` — the orchestrator that fans out across sources, applies strategies, handles timeouts, emits `retrieval.query` journal events. **Application-layer.** The reference implementation (Python) ships it inside pocketpaw.
- `InMemoryCredentialBroker` — a concrete broker. **Application-layer.** Production deployments use their platform's secret store.
- `ProjectionAdapter`, `MockAdapter` — concrete adapters. **Application-layer / test helpers.**

A third-party runtime implementing Soul Protocol provides these for itself. The spec only pins the interfaces they implement.

---

## 10 · CognitiveEngine

The spec defines the single-method interface agents use to invoke their underlying LLM.

```
CognitiveEngine (Protocol) {
  think(prompt: str) -> str
}
```

A `CognitiveEngine` is the agent's thinking substrate — Claude, GPT-4, local Ollama, whatever. The protocol is deliberately minimal: string in, string out. Streaming, tool use, vision, etc., are consumer-level concerns built on top.

---

## 11 · Conformance

An implementation **claims Soul Protocol 0.3.3 compliance** when it can:

- [ ] Read and write `.soul` files at schema_version 0.3.3 (§2)
- [ ] Honor the memory tier semantics, including activation decay and significance gating (§4)
- [ ] Implement the `Journal.append` / `Journal.query` contract including `action_prefix` (§8)
- [ ] Emit scope-non-empty `EventEntry` records with UTC timestamps (§8)
- [ ] Round-trip `.soul` files produced by the reference impl without field loss (§2)
- [ ] Implement the `CognitiveEngine` protocol (§10)

Retrieval infrastructure (Router/Broker/Adapter implementations) is explicitly NOT required for compliance — it is application-layer.

A conformance test suite lives in the reference implementation under `tests/conformance/` (planned — 0.4.0).

---

## 12 · Versioning

- **Patch** (0.3.1 → 0.3.3) — additive fields, new query parameters, new exported types. Non-breaking.
- **Minor** (0.3.x → 0.4.0) — backward-compatible structural changes. Implementations may need to upgrade but old `.soul` files still read.
- **Major** (0.x → 1.0) — reserved for the first stable release.

The reference implementation may release patch versions faster than the spec. Spec versions advance only when the contract changes.

---

## 13 · Reference implementation

The reference implementation lives in this repository under `src/soul_protocol/`:

```
src/soul_protocol/
├── spec/           # This document's contract, as Python types + Protocols.
│                   # Zero imports from opinionated modules. Implements §2–§10.
├── engine/         # Substrate implementations (currently: the journal).
├── runtime/        # Reference algorithms (psychology pipeline, memory managers,
│                   # dream consolidation, retrieval-over-memory, ...)
├── cli/            # CLI reference tool (soul command).
├── mcp/            # MCP server reference tool.
└── spike/          # Experimental modules. NOT part of the shipped API.
```

See [docs/architecture.md](./architecture.md) for the detailed internal layout. Other runtimes (Rust, Go, TypeScript) implement against §2–§10 of this document and are free to ignore `engine/`, `runtime/`, `cli/`, `mcp/`.

---

## See also

- [docs/architecture.md](./architecture.md) — reference implementation's internal architecture.
- [docs/org-journal-spec.md](./org-journal-spec.md) — deeper dive on the journal, its scope grammar, and the decision-trace vocabulary on top of it.
- [docs/memory-architecture.md](./memory-architecture.md) — reference impl's memory subsystem in depth.
- [docs/cognitive-engine.md](./cognitive-engine.md) — how to wire a concrete LLM into the `CognitiveEngine` protocol.
