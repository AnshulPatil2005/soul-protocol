# Memory-Journal Spike

Design doc for the spike that applies the org-journal pattern (v0.3.1) to
soul memory storage. Lives on `feat/0.3.2-spike`. Kept local until thesis B
validates against the 532-memory pocketpaw fixture.

## Thesis

> Soul memory becomes a journal consumer. `remember`/`forget`/`promote`
> are events. The three tiers are projections, rebuildable from the journal.
> Cleanup is a rebuild, not a destructive delete. Forget is a tombstone.

## Why now

- The April 5 cleanup incident wiped 553 memories. The pattern stays risky
  as long as projections and truth are the same thing.
- `soul cleanup --auto` dedups at 0.8 token-Jaccard — too aggressive, no
  confirmation, no undo.
- The journal + projection pattern is already shipped (v0.3.1) and running
  in production at pocketpaw (`ee/fabric/`, `ee/widget/`, `ee/retrieval/`).
- 0.3.2 primitive #1 (`Journal.append` returns committed EventEntry) lands
  the seq-ack pattern this spike needs.

## Non-goals

- Migrating all existing souls automatically. The spike works on a copy
  of the fixture; migration tooling comes after benchmark validation.
- Replacing `ArchivalMemoryStore`. That stays — archive is still a
  projection, just a different one.
- Changing the `MemoryStore` Protocol. The spike implements the existing
  Protocol, backed by the journal.

## Storage model

One SQLite file per soul, inside the `.soul` zip:

```
memory.db
├── events               ← THE JOURNAL (append-only, from v0.3.1 engine)
├── memory_episodic      ← projection
├── memory_semantic      ← projection
├── memory_procedural    ← projection
├── fts_memories         ← FTS5 virtual table (bm25 search)
└── projection_meta      ← last replayed seq, schema version
```

The `events` table is the existing journal schema. Projection tables are
new — they're caches, not truth.

## Event schema

Reuses existing `ACTION_NAMESPACES`:

| Action | Trigger | Payload |
|---|---|---|
| `memory.remembered` | `remember(...)` | content, tier, importance, tags, memory_id |
| `memory.forgotten` | `forget(memory_id)` | memory_id, reason (no content — GDPR) |
| `memory.graduated` | `promote(memory_id, to_tier)` | memory_id, from_tier, to_tier, reason |

Action additively introduced in this spike:
| Action | Trigger | Payload |
|---|---|---|
| `memory.archived` | dream-cycle compression | memory_id, archive_id (content stays, tier moves) |

Payload shapes (informal — formalize as Pydantic models if spike validates):

```python
# memory.remembered
{
    "memory_id": str,          # stable id for future refs
    "content": str,            # the memory text
    "tier": "episodic" | "semantic" | "procedural",
    "importance": int,         # 0-10
    "emotion": str | None,
    "tags": list[str],
    "source": str,             # "user" | "agent" | "cognitive.extract" | ...
}

# memory.forgotten  (tombstone — GDPR-safe)
{
    "memory_id": str,
    "reason": str,             # "user" | "dedup" | "cleanup" | "gdpr"
}

# memory.graduated
{
    "memory_id": str,
    "from_tier": str,
    "to_tier": str,
    "reason": str,             # "importance>=7" | "dream-cycle" | "manual"
}

# memory.archived
{
    "memory_id": str,
    "archive_id": str,         # opaque ref into the archival store
    "reason": str,
}
```

## Projection rebuild

Deterministic, idempotent. Replay events in seq order:

```python
def rebuild_projections(journal: Journal, proj_db: sqlite3.Connection) -> None:
    proj_db.execute("DELETE FROM memory_episodic")
    proj_db.execute("DELETE FROM memory_semantic")
    proj_db.execute("DELETE FROM memory_procedural")
    proj_db.execute("DELETE FROM fts_memories")

    for event in journal.replay_from(0):
        match event.action:
            case "memory.remembered":
                insert_into_tier(event.payload)
            case "memory.forgotten":
                delete_from_tier(event.payload["memory_id"])
            case "memory.graduated":
                move_tier(event.payload)
            case "memory.archived":
                remove_from_active_tiers(event.payload["memory_id"])

    proj_db.execute(
        "UPDATE projection_meta SET last_replayed_seq = ?",
        (event.seq,),
    )
    proj_db.commit()
```

**Safety property:** if the projection tables are dropped, corrupted, or
manually deleted, a rebuild reproduces the exact state implied by the
journal. Cleanup can never cause data loss because it can't touch the
journal — only projections.

## Public API (JournalBackedMemoryStore)

Implements the existing `MemoryStore` Protocol so downstream code
(Soul, MemoryManager, CLI) doesn't change.

```python
class JournalBackedMemoryStore(MemoryStore):
    def __init__(self, journal: Journal, db: sqlite3.Connection) -> None: ...

    # MemoryStore Protocol
    def store(self, layer: str, entry: MemoryEntry) -> str: ...
    def recall(self, layer: str, *, limit: int = 10) -> list[MemoryEntry]: ...
    def search(self, query: str, *, limit: int = 10) -> list[MemoryEntry]: ...
    def delete(self, memory_id: str) -> bool: ...
    def layers(self) -> list[str]: ...

    # Journal-specific ops (not in Protocol)
    def promote(self, memory_id: str, to_tier: str, reason: str) -> None: ...
    def rebuild(self) -> None: ...
    def audit_trail(self, memory_id: str) -> list[EventEntry]: ...
```

Notes:
- `store()` writes a `memory.remembered` event, returns the memory_id.
- `delete()` writes a `memory.forgotten` tombstone (content is NOT stored
  in the event payload) and removes from projections.
- `search()` hits FTS5 with BM25 ranking. No token-Jaccard.
- `rebuild()` drops projections, replays the journal. Safe, idempotent.
- `audit_trail(id)` queries journal for all events referencing a memory_id
  — useful for "when was this written, when was it promoted, when forgotten".

## Benchmark plan (Task #12)

Against the 532-memory pocketpaw fixture, measure:

| Axis | Baseline (current 3-tier) | Candidate (journal + FTS5) |
|---|---|---|
| Storage | JSON dicts in .soul | SQLite in .soul |
| Recall latency p50/p95/p99 | ? | ? |
| Recall@5 on canonical query set | ? | ? |
| Forget correctness (collateral damage) | ? | ? |
| Rebuild from journal | n/a | ? |
| Cold-start load time | ? | ? |
| Write latency (`remember`) | ? | ? |

Canonical query set: 20-30 queries from real usage (grep session logs).

Pass criteria:
- recall@5 >= baseline on 25/30 queries
- p95 latency <= 2x baseline
- forget-without-collateral-damage: proven on fixture
- rebuild: projection tables deleted, rebuild matches pre-delete state

Fail-open: if the candidate loses on recall@5 or bloats storage 3x, shelve
the spike and document what broke.

## Testing discipline

Every piece of spike code gets all 4 test layers:

1. **Unit** — isolated function tests (single-file, pure logic)
2. **Smoke** — basic sanity after build (store → recall → get back)
3. **E2E** — full flow through MemoryStore Protocol + journal + projection
4. **Real-world sim** — load pocketpaw fixture, run canonical query set

## Open questions

- Where does `memory.db` live inside `.soul`? Top-level, or in `memory/`
  alongside the JSON dumps during transition?
- Do we keep the JSON dumps during the spike for parallel-query comparison,
  or replace them outright? (Likely: keep during spike, replace on merge.)
- Dream-cycle: does it issue `memory.archived` events, or
  `memory.graduated` with `to_tier="archive"`? Both work; former is clearer.
- Core memory (persona, human) — is that also journal-backed, or separate?
  Argument for journal-backed: full audit of persona drift. Out of scope
  for this spike.
- OCEAN + state drift — same question, same answer (out of scope).
- MCP bridge — the hot-reload bug hit on 2026-03-16 was about staleness
  after external writes. Journal + projection naturally fixes this:
  MCP just replays from last_seen_seq on every read. Add to the benchmark.
