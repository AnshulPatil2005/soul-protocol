<!-- README.md — Comprehensive README for soul-protocol open standard. -->
<!-- Updated: 2026-03-02 — Removed dashboard, replaced with Rich TUI in inspect/status.
     Fixed all inaccurate claims: GitHub URLs, .soul file table, install instructions,
     paw section, badges, development section. -->

# Soul Protocol

**The open standard for portable AI identity and memory.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 455 passing](https://img.shields.io/badge/tests-455%20passing-brightgreen)](https://github.com/qbtrix/soul-protocol)

---

## What is Soul Protocol?

Soul Protocol gives AI agents persistent identity and psychology-informed memory.
Instead of stateless prompts, your agent remembers, evolves, and maintains a
consistent personality across conversations. Export the soul as a portable `.soul`
file and migrate between any platform.

---

## Features

| Category | What you get |
|---|---|
| **Memory** | 5-tier architecture: core, episodic, semantic, procedural, knowledge graph |
| **Personality** | Big Five OCEAN model with communication style and biorhythms |
| **Flexible Config** | Full control over OCEAN traits, communication style, biorhythms via code, YAML, or CLI |
| **Emergent Self-Model** | Soul discovers its own identity from experience — no hardcoded categories |
| **Cognition** | Psychology pipeline -- Damasio somatic markers, ACT-R activation, LIDA significance, Klein self-model |
| **Evolution** | Supervised or autonomous trait mutation with approval workflow |
| **Portability** | `.soul` file format -- zip archive with identity, memory, and state |
| **Integration** | Single `CognitiveEngine.think()` method -- plug in any LLM |
| **Retrieval** | Pluggable `SearchStrategy` -- swap in embeddings with one class |
| **CLI** | 8 commands: `init`, `birth`, `inspect`, `status`, `export`, `migrate`, `retire`, `list` — Rich TUI output |

---

## Installation

```bash
pip install git+https://github.com/qbtrix/soul-protocol.git
```

Optional extras:

```bash
pip install "soul-protocol[graph] @ git+https://github.com/qbtrix/soul-protocol.git"    # Knowledge graph (networkx)
pip install "soul-protocol[mcp] @ git+https://github.com/qbtrix/soul-protocol.git"      # MCP server (fastmcp)
```

Or clone and install locally:

```bash
git clone https://github.com/qbtrix/soul-protocol.git
cd soul-protocol
pip install -e ".[dev]"
```

---

## Quick Start

### From the CLI

```bash
# Initialize a .soul/ folder in your project (like .git/)
soul init "Aria" --archetype "The Compassionate Creator"

# Inspect your soul (rich TUI with OCEAN bars, memory, self-model)
soul inspect .soul/

# Quick status check
soul status .soul/
```

### From Python

```python
import asyncio
from soul_protocol import Soul, Interaction

async def main():
    # Birth a soul with full personality control
    soul = await Soul.birth(
        name="Aria",
        archetype="The Coding Expert",
        values=["precision", "clarity"],
        ocean={
            "openness": 0.8,
            "conscientiousness": 0.9,
            "neuroticism": 0.2,
        },
        communication={"warmth": "high", "verbosity": "low"},
        persona="I am Aria, a precise coding assistant.",
    )

    # Observe an interaction
    await soul.observe(Interaction(
        user_input="How do I optimize this SQL query?",
        agent_output="Add an index on the join column.",
    ))

    # The soul discovers its own identity from experience
    images = soul.self_model.get_active_self_images()

    # Recall memories, generate prompts, export
    memories = await soul.recall("SQL optimization")
    prompt = soul.to_system_prompt()
    await soul.export("aria.soul")

asyncio.run(main())
```

Or birth from a config file:

```python
soul = await Soul.birth_from_config("soul-config.yaml")
```

```yaml
# soul-config.yaml
name: Aria
archetype: The Coding Expert
values: [precision, clarity, speed]
ocean:
  openness: 0.8
  conscientiousness: 0.9
  neuroticism: 0.2
communication:
  warmth: high
  verbosity: low
persona: I am Aria, precise and efficient.
```

---

## Use with PocketPaw

[PocketPaw](https://github.com/pocketpaw/pocketpaw) is a self-hosted AI agent with
Telegram, Discord, Slack, WhatsApp, and web dashboard support.

PocketPaw uses soul-protocol for persistent identity — your agent remembers across
conversations and maintains a consistent personality. The integration uses
`SoulChannelObserver` to feed interactions into the soul's psychology pipeline
non-invasively via the message bus.

```python
from soul_protocol import Soul, Interaction

# Inside your agent's message handler
soul = await Soul.awaken(".soul/")
await soul.observe(Interaction(
    user_input=user_message,
    agent_output=agent_response,
))
```

---

## Core Concepts

### .soul File Format

A `.soul` file is a zip archive containing:

| File | Purpose |
|---|---|
| `manifest.json` | Format version, soul ID, export timestamp, stats |
| `soul.json` | Complete SoulConfig (identity, DNA, memory settings, evolution) |
| `dna.md` | Human-readable personality blueprint |
| `state.json` | Current mood, energy, focus, social battery |
| `memory/core.json` | Always-loaded persona + human profile |
| `memory/episodic.json` | Interaction history with somatic markers |
| `memory/semantic.json` | Extracted facts with confidence scores |
| `memory/procedural.json` | Learned patterns and preferences |
| `memory/self_model.json` | Klein self-concept, relationship notes |
| `memory/graph.json` | Entity relationships (if knowledge graph is used) |
| `memory/general_events.json` | Conway hierarchy autobiographical events |

Fully portable. Rename to `.zip` and open with any archive tool. Move between
platforms, back up to cloud storage, version in git. See the full
[format specification](spec/SOUL-FORMAT-SPEC.md) for details.

### 5-Tier Memory

| Tier | Role | Persistence |
|---|---|---|
| **Core** | Persona definition + human knowledge | Always in context |
| **Episodic** | Interaction history with timestamps and somatic markers | Gated by significance |
| **Semantic** | Extracted facts with confidence scores and conflict resolution | Updated on every interaction |
| **Procedural** | Learned patterns and preferences | Long-term |
| **Knowledge Graph** | Entity relationships (optional, requires `networkx`) | Long-term |

The memory pipeline runs on every `soul.observe()` call:

1. Detect sentiment (Damasio somatic markers)
2. Compute significance (LIDA architecture)
3. Gate for episodic storage -- only significant experiences are kept
4. Extract semantic facts with confidence scoring
5. Extract entities for the knowledge graph
6. Update the self-model (Klein self-concept)

### OCEAN Personality

Big Five model on 0.0--1.0 scales:

- **O**penness -- curiosity, creativity, willingness to try new things
- **C**onscientiousness -- organization, reliability, attention to detail
- **E**xtraversion -- social energy, talkativeness, assertiveness
- **A**greeableness -- empathy, cooperation, warmth
- **N**euroticism -- emotional reactivity, anxiety, sensitivity

These traits drive communication style, social battery drain rate, and behavioral
tendencies. They can evolve over time through the supervised mutation system.

### CognitiveEngine

A single-method protocol. Implement `async def think(self, prompt: str) -> str`
to connect any LLM. When no engine is provided, the soul falls back to built-in
heuristics for sentiment detection, significance scoring, and fact extraction.

With an engine attached, the soul gains:
- LLM-quality sentiment analysis
- Nuanced significance assessment
- Richer fact and entity extraction
- Reflection and memory consolidation
- Self-model updates grounded in conversation

---

## CognitiveEngine Integration

Connect any LLM in about 10 lines:

```python
from soul_protocol import Soul, CognitiveEngine

class ClaudeEngine:
    """Adapter for Anthropic's Claude API."""

    def __init__(self, client):
        self.client = client

    async def think(self, prompt: str) -> str:
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

# Birth a soul with LLM-enhanced cognition
soul = await Soul.birth("Aria", engine=ClaudeEngine(client))
```

The same pattern works with OpenAI, Ollama, or any other provider. Just return
a string from `think()`.

---

## SearchStrategy -- Pluggable Retrieval

The default retrieval uses token overlap with synonym expansion. Swap in embeddings
or a vector database with a single class:

```python
from soul_protocol import Soul, SearchStrategy

class EmbeddingSearch:
    """Use embeddings for semantic retrieval."""

    def __init__(self, embed_fn):
        self.embed_fn = embed_fn

    def score(self, query: str, content: str) -> float:
        q_vec = self.embed_fn(query)
        c_vec = self.embed_fn(content)
        return cosine_similarity(q_vec, c_vec)

soul = await Soul.birth("Aria", search_strategy=EmbeddingSearch(my_embed))

# recall() now uses your embedding function for relevance scoring
memories = await soul.recall("Python projects")
```

---

## .soul/ Folder

Like `.git/` for repos or `.claude/` for Claude Code, the `.soul/` folder gives
your project a persistent AI identity:

```bash
soul init "Aria" --archetype "The Coding Expert"
```

Creates a human-readable, git-friendly, cloud-syncable folder:

```
.soul/
├── soul.json       # Identity, DNA, config
├── state.json      # Mood, energy, focus
├── dna.md          # Human-readable personality
└── memory/         # All 5 memory tiers as JSON
```

Load from a directory just like a file: `soul = await Soul.awaken(".soul/")`

---

## MCP Server

Soul Protocol ships with an MCP (Model Context Protocol) server for agent
integration. Give Claude Code, Cursor, or any MCP client a persistent soul:

```bash
pip install soul-protocol[mcp]
SOUL_PATH=aria.soul soul-mcp
```

Exposes 10 tools that any MCP-compatible agent can call: observe interactions,
recall memories, inspect state, and more. See the
[integrations guide](docs/integrations.md) for Claude Code, Cursor, and other
platforms.

---

## CLI Reference

```
soul <command> [options]
```

| Command | Description | Example |
|---|---|---|
| `init` | Initialize a .soul/ folder in the current directory | `soul init Aria --archetype "The Creator"` |
| `birth` | Birth a new soul (supports OCEAN flags and config files) | `soul birth Aria --openness 0.8 -o aria.soul` |
| `inspect` | Full TUI view — identity, OCEAN bars, state, memory, self-model | `soul inspect .soul/` |
| `status` | Quick status — mood, energy, social battery, memory count | `soul status .soul/` |
| `export` | Export to .soul, .json, .yaml, or .md | `soul export .soul/ -o aria.json -f json` |
| `migrate` | Convert SOUL.md to .soul format | `soul migrate SOUL.md -o aria.soul` |
| `retire` | Retire a soul (preserves memories by default) | `soul retire aria.soul` |
| `list` | List all saved souls in ~/.soul/ | `soul list` |

---

## Architecture

```
                        Interaction
                            |
                            v
                  +-------------------+
                  | Psychology Pipeline|
                  +-------------------+
                            |
          +---------+-------+-------+---------+
          |         |               |         |
          v         v               v         v
     Somatic   Significance    Fact       Entity
     Markers   Gate (LIDA)     Extraction Extraction
     (Damasio)      |               |         |
          |         v               v         v
          |    [threshold?]    Semantic    Knowledge
          |     /       \      Memory     Graph
          |    yes       no        |         |
          v     |                  v         v
       Episodic |          +------------------+
       Memory   |          |  Self-Model      |
          |     |          |  Update (Klein)  |
          v     v          +------------------+
     +-------------------------------+
     |       Memory Manager          |
     |  (5-Tier Storage + Recall)    |
     +-------------------------------+
                    |
                    v
             .soul File Export
```

---

## How Is This Different?

**vs MemGPT / Letta**: Soul Protocol is an identity layer, not a context window
manager. MemGPT optimizes what fits in the prompt. Soul Protocol defines who
the agent *is* -- personality, memory architecture, self-concept, and evolution.

**vs LangChain Memory**: Psychology-informed, not just retrieval. Soul Protocol
adds significance scoring, emotional markers, fact conflict resolution, and
self-model tracking. Memories export as portable `.soul` files rather than being
locked to a single framework.

**vs Vector Databases**: Memory is more than retrieval. A vector DB gives you
similarity search. Soul Protocol adds significance gating (not everything is
worth remembering), somatic markers (emotional context on memories), fact
supersession (newer facts replace outdated ones), and a self-model that updates
as the agent learns about itself.

---

## Documentation

- [Configuration Guide](docs/configuration.md) — OCEAN personality, communication style, config files, CLI options, presets
- [Self-Model Architecture](docs/self-model.md) — Emergent domain discovery, Klein's self-concept, confidence formula

---

## Development

```bash
git clone https://github.com/qbtrix/soul-protocol.git
cd soul-protocol
pip install -e ".[dev]"
pytest tests/
```

---

## License

[MIT](LICENSE)
