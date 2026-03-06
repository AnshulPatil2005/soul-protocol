# Soul Protocol -- Architecture

> Current implementation architecture, module dependencies, memory layers, and data flow.

**Date:** 2026-03-06
**Version:** 0.2.2

---

## 1. Two-Layer Architecture

The codebase separates concerns into a data/storage layer ("core") and an intelligence layer ("engine"). This was not in the original vision -- it emerged from the v0.2.0 psychology-informed memory work.

```
+===========================================================================+
|                          ENGINE LAYER                                      |
|  Intelligence, scoring, and cognition                                      |
|                                                                            |
|  +------------------+  +------------------+  +------------------+          |
|  | cognitive/       |  | memory/          |  | memory/          |          |
|  |   engine.py      |  |   activation.py  |  |   self_model.py  |          |
|  |   prompts.py     |  |   attention.py   |  |   sentiment.py   |          |
|  |                  |  |   strategy.py    |  |                  |          |
|  +------------------+  +------------------+  +------------------+          |
|                                                                            |
|  CognitiveEngine protocol       ACT-R scoring          Klein self-concept  |
|  HeuristicEngine fallback       Significance gate       Somatic markers    |
|  CognitiveProcessor orchestrator  Spreading activation   EMA mood inertia  |
+===========================================================================+
           |                    |                    |
           v                    v                    v
+===========================================================================+
|                           CORE LAYER                                       |
|  Data models, stores, serialization, and I/O                               |
|                                                                            |
|  +----------+  +----------+  +----------+  +----------+  +----------+     |
|  | types.py |  | memory/  |  | export/  |  | storage/ |  | parsers/ |     |
|  | (models) |  |  core.py |  |  pack.py |  |  file.py |  |  md.py   |     |
|  |          |  | epis.py  |  | unpack.py|  | proto.py |  |  yaml.py |     |
|  |          |  |  sem.py  |  |          |  | mem.py   |  |  json.py |     |
|  |          |  | proc.py  |  |          |  |          |  |          |     |
|  |          |  | graph.py |  |          |  |          |  |          |     |
|  |          |  | recall.py|  |          |  |          |  |          |     |
|  |          |  | search.py|  |          |  |          |  |          |     |
|  +----------+  +----------+  +----------+  +----------+  +----------+     |
|                                                                            |
|  +----------+  +----------+  +----------+  +----------+  +----------+     |
|  | soul.py  |  |identity/ |  |  dna/    |  |  state/  |  |evolution/|     |
|  | (facade) |  |  did.py  |  | prompt.py|  | manager  |  | manager  |     |
|  +----------+  +----------+  +----------+  +----------+  +----------+     |
+===========================================================================+
           |                    |
           v                    v
+===========================================================================+
|                       INTERFACE LAYER                                      |
|  External-facing APIs                                                      |
|                                                                            |
|  +------------------+     +------------------+                             |
|  | cli/main.py      |     | mcp/server.py    |                             |
|  | (Click commands)  |     | (FastMCP tools)  |                             |
|  +------------------+     +------------------+                             |
+===========================================================================+
```

---

## 2. Module Dependency Graph

Arrows indicate "imports from". Only significant dependencies shown.

```
soul.py (main facade)
  |
  +---> types.py (all Pydantic models)
  +---> identity/did.py
  +---> dna/prompt.py
  +---> memory/manager.py
  |       |
  |       +---> memory/core.py -------> types.py
  |       +---> memory/episodic.py ---> types.py
  |       +---> memory/semantic.py ---> types.py
  |       +---> memory/procedural.py -> types.py
  |       +---> memory/graph.py
  |       +---> memory/recall.py
  |       |       +---> memory/activation.py
  |       |       |       +---> memory/search.py
  |       |       |       +---> memory/strategy.py (protocol)
  |       |       +---> memory/episodic.py
  |       |       +---> memory/semantic.py
  |       |       +---> memory/procedural.py
  |       +---> memory/self_model.py --> memory/search.py
  |       +---> memory/attention.py ---> memory/sentiment.py
  |       +---> memory/search.py
  |       +---> cognitive/engine.py (lazy import)
  |
  +---> state/manager.py ---------> types.py
  +---> evolution/manager.py -----> types.py
  +---> export/pack.py -----------> dna/prompt.py, types.py
  +---> export/unpack.py ---------> types.py
  +---> storage/file.py ----------> dna/prompt.py, types.py
  +---> cognitive/engine.py ------> cognitive/prompts.py, types.py

cli/main.py
  +---> soul.py (lazy import)
  +---> storage/file.py

mcp/server.py
  +---> soul.py
  +---> types.py
  +---> exceptions.py

crypto/encrypt.py
  +---> cryptography (external, no internal deps)

parsers/markdown.py
  +---> identity/did.py, types.py, yaml (external)

parsers/yaml_parser.py
  +---> types.py, yaml (external)

parsers/json_parser.py
  +---> types.py
```

### Circular Dependency Avoidance

The primary circular risk is `cognitive/engine.py <-> memory/manager.py`. This is resolved via:
- `memory/manager.py` uses a lazy import (`from soul_protocol.cognitive.engine import ...` inside `__init__`)
- `cognitive/engine.py` uses `TYPE_CHECKING` for `SelfModelManager`
- `memory/attention.py` and `memory/sentiment.py` have no dependency on `cognitive/`

---

## 3. Memory System Layers

```
+=======================================================================+
|                    SOUL MEMORY SYSTEM                                  |
|                                                                        |
|  +--------- CORE MEMORY (CoreMemoryManager) ---------+               |
|  |  Always in context. ~500 tokens each.              |               |
|  |                                                    |               |
|  |  persona: "I am Aria, warm and creative..."       |               |
|  |  human:   "Alex prefers Python, works late..."    |               |
|  |                                                    |               |
|  |  Editable via edit_core_memory()                   |               |
|  +----------------------------------------------------+               |
|                          |                                             |
|                          v                                             |
|  +--------- RECALL MEMORY (RecallEngine) ------------+               |
|  |  Searchable via token overlap + ACT-R activation   |               |
|  |                                                    |               |
|  |  +-----------+  +-----------+  +-------------+    |               |
|  |  | EPISODIC  |  | SEMANTIC  |  | PROCEDURAL  |    |               |
|  |  | (events)  |  | (facts)   |  | (how-to)    |    |               |
|  |  |           |  |           |  |             |    |               |
|  |  | Capped at |  | Capped at |  | Uncapped    |    |               |
|  |  | 10,000    |  | 1,000     |  |             |    |               |
|  |  +-----------+  +-----------+  +-------------+    |               |
|  |                                                    |               |
|  |  Scoring: base_activation (ACT-R decay)            |               |
|  |         + spreading_activation (query relevance)   |               |
|  |         + emotional_boost (somatic markers)        |               |
|  +----------------------------------------------------+               |
|                          |                                             |
|                          v                                             |
|  +--------- KNOWLEDGE GRAPH (KnowledgeGraph) --------+               |
|  |  Entities + directed relationships                 |               |
|  |                                                    |               |
|  |  [Python] --type--> [technology]                   |               |
|  |  [Alex]   --uses--> [Python]                       |               |
|  |  [Alex]   --works_at--> [Interacly]               |               |
|  |                                                    |               |
|  |  Auto-populated from entity extraction             |               |
|  +----------------------------------------------------+               |
|                          |                                             |
|                          v                                             |
|  +--------- SELF-MODEL (SelfModelManager) -----------+               |
|  |  Klein's self-concept: "who am I based on what    |               |
|  |  I do?"                                            |               |
|  |                                                    |               |
|  |  Domains:  technical_helper (conf: 0.87, 42 ev)   |               |
|  |            problem_solver   (conf: 0.65, 18 ev)   |               |
|  |            creative_writer  (conf: 0.23, 3 ev)    |               |
|  |                                                    |               |
|  |  Relationship notes: {user: "Name: Alex;          |               |
|  |                        Works at: Interacly"}      |               |
|  +----------------------------------------------------+               |
|                                                                        |
|  +--------- GENERAL EVENTS (Conway Hierarchy) -------+               |
|  |  Theme-based episode clustering                    |               |
|  |                                                    |               |
|  |  "debugging session" -> [ep-001, ep-003, ep-007]  |               |
|  |  "architecture work" -> [ep-002, ep-005]          |               |
|  |                                                    |               |
|  |  Created during reflect() + consolidate()          |               |
|  +----------------------------------------------------+               |
+=======================================================================+
```

### Missing Memory Layers (from Vision)

```
  NOT IMPLEMENTED:

  +--------- WORKING MEMORY (volatile) ----------------+
  |  Current conversation context                       |
  |  Managed by the runtime, not the soul              |
  +----------------------------------------------------+

  +--------- ARCHIVAL MEMORY (deep storage) -----------+
  |  Full conversation transcripts                      |
  |  Compressed summaries                               |
  |  External storage links (vector DB, IPFS, etc.)    |
  +----------------------------------------------------+
```

---

## 4. Data Flow

### 4.1 Birth -> Interact -> Remember -> Recall -> Evolve -> Save

```
   BIRTH                        INTERACT
     |                              |
     v                              v
 Soul.birth()                 Soul.observe(interaction)
     |                              |
     |  Creates:                    |  Pipeline:
     |  - Identity (DID)            |  1. detect_sentiment() -> SomaticMarker
     |  - DNA (OCEAN)               |  2. assess_significance() -> SignificanceScore
     |  - Empty core memory         |  3. IF significant: store episodic
     |  - Default state             |  4. extract_facts() -> semantic memories
     |  - Evolution config          |  5. extract_entities() -> knowledge graph
     |                              |  6. update_self_model()
     v                              |  7. update state (energy, mood)
 Soul instance                      |  8. check evolution triggers
                                    v
                              Soul with memories
                                    |
                  +-----------------+-----------------+
                  |                                   |
                  v                                   v
            Soul.recall(query)                  Soul.reflect()
                  |                                   |
                  |  1. Search episodic               |  1. Review recent episodes
                  |  2. Search semantic               |  2. Identify themes
                  |  3. Search procedural             |  3. Summarize patterns
                  |  4. ACT-R activation score        |  4. Generate self-insight
                  |  5. Rank + return top N            |  5. Consolidate into memory
                  |  6. Update access timestamps       |
                  v                                   v
            List[MemoryEntry]                   ReflectionResult
                                                      |
                                               (auto-apply if enabled)
                  |                                   |
                  v                                   v
            Soul.save(path)                     Soul.export(path)
                  |                                   |
                  |  Atomic write to:                 |  Creates zip with:
                  |  ~/.soul/<soul_id>/               |  - manifest.json
                  |    soul.json                      |  - soul.json
                  |    state.json                     |  - dna.md
                  |    dna.md                         |  - state.json
                  |    memory/                        |  - memory/
                  |      core.json                    |    core.json
                  |      episodic.json                |    episodic.json
                  |      semantic.json                |    semantic.json
                  |      procedural.json              |    procedural.json
                  |      graph.json                   |    graph.json
                  |      self_model.json              |    self_model.json
                  |      general_events.json          |    general_events.json
                  v                                   v
            Saved to disk                       .soul file (portable)
```

### 4.2 Observe Pipeline Detail

```
Interaction (user_input + agent_output)
    |
    v
CognitiveProcessor.detect_sentiment(user_input)
    |
    |  HeuristicEngine path:           LLM path:
    |    Word-list matching              SENTIMENT_PROMPT -> engine.think()
    |    Intensity modifiers             Parse JSON response
    |    Negation detection              Validate valence/arousal
    |
    v
SomaticMarker (valence, arousal, label)
    |
    v
CognitiveProcessor.assess_significance(interaction, core_values, recent)
    |
    |  HeuristicEngine path:           LLM path:
    |    Token overlap for novelty       SIGNIFICANCE_PROMPT -> engine.think()
    |    Arousal for emotion             Parse JSON response
    |    Value word matching             Validate 3 dimensions
    |
    v
SignificanceScore (novelty, emotional_intensity, goal_relevance)
    |
    |  overall = 0.4*novelty + 0.35*emotion + 0.25*goal
    |  threshold = 0.25
    |
    +----> NOT significant?  Skip episodic storage
    |                        (but still extract facts)
    |
    +----> Significant?  Store in EpisodicStore
    |                    with somatic marker + significance
    |
    v
CognitiveProcessor.extract_facts(interaction, existing_facts)
    |
    |  HeuristicEngine path:           LLM path:
    |    18 regex patterns               FACT_EXTRACTION_PROMPT -> engine.think()
    |    Token-overlap dedup             Parse JSON array
    |    Template-based output           Validate each entry
    |
    v
List[MemoryEntry] (semantic facts)
    |
    |  Resolve conflicts (supersede old contradicting facts)
    |  Store in SemanticStore
    |
    |  If facts extracted but wasn't significant: promote to episodic
    |
    v
CognitiveProcessor.extract_entities(interaction)
    |
    |  Known tech terms + proper nouns
    |  Infer relationships (uses, builds, prefers, etc.)
    |
    v
List[entity dicts] --> Update KnowledgeGraph
    |
    v
CognitiveProcessor.update_self_model(interaction, facts, self_model)
    |
    |  HeuristicEngine path:           LLM path:
    |    Token matching vs domains       SELF_REFLECTION_PROMPT -> engine.think()
    |    Dynamic domain creation         Parse self_images + relationship_notes
    |    Keyword expansion               Update SelfModelManager
    |
    v
Updated SelfModelManager
    |
    v
StateManager.on_interaction(interaction, somatic)
    |
    |  Energy -= 2, Social Battery -= 5
    |  EMA-smooth valence
    |  Map to mood via label or quadrant
    |  Energy < 20? Override to TIRED
    |
    v
Updated SoulState
```

---

## 5. File Format (.soul Archive)

```
name.soul (zip, deflated)
|
+-- manifest.json          # SoulManifest: format version, dates, stats
+-- soul.json              # Full SoulConfig: identity, DNA, settings
+-- dna.md                 # Human-readable personality markdown
+-- state.json             # Current SoulState snapshot
+-- memory/
    +-- core.json          # CoreMemory: persona + human text
    +-- episodic.json      # List of MemoryEntry (episodic type)
    +-- semantic.json      # List of MemoryEntry (semantic type)
    +-- procedural.json    # List of MemoryEntry (procedural type)
    +-- graph.json         # KnowledgeGraph: entities + edges
    +-- self_model.json    # SelfModelManager: images + notes + keywords
    +-- general_events.json # List of GeneralEvent (Conway themes)
```

### Directory Format (.soul/ folder)

Same structure but unpacked on disk. Created by `soul init` or `soul.save_local()`.

```
.soul/
|
+-- soul.json
+-- dna.md
+-- state.json
+-- memory/
    +-- core.json
    +-- episodic.json
    +-- semantic.json
    +-- procedural.json
    +-- graph.json
    +-- self_model.json
    +-- general_events.json
```

---

## 6. External Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| pydantic >= 2.0 | All data models, validation, serialization | Yes |
| click >= 8.0 | CLI framework | Yes |
| pyyaml >= 6.0 | YAML parsing (soul.yaml, config files) | Yes |
| rich >= 13.0 | CLI rich text output (inspect, status) | Yes |
| cryptography >= 42.0 | Fernet encryption, PBKDF2 | Yes |
| fastmcp >= 0.4 | MCP server (optional extra) | No (mcp extra) |

---

*Document generated from codebase analysis on 2026-03-06.*
