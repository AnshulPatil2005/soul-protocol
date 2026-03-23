<!-- soul-protocol skill for skills.sh — publishable Claude Code skill for integrating soul-protocol with AI agents -->

---
name: soul-protocol
description: Add persistent identity, memory, and personality to AI agents. Use when building chatbots, companions, or any agent that should remember users, evolve over time, and maintain consistent behavior across sessions. Triggers on: soul, memory, personality, companion, identity, persistent agent, remember user.
---

# Soul Protocol

Give your AI agent a soul — persistent memory, personality, and identity that survive across sessions and platforms.

## Install

```bash
pip install soul-protocol          # Core (zero heavy deps)
pip install soul-protocol[engine]  # + Click CLI, YAML, Rich TUI, cryptography
pip install soul-protocol[mcp]     # + MCP server for agent-to-agent use
pip install soul-protocol[vector]  # + numpy for semantic memory search
pip install soul-protocol[graph]   # + networkx for knowledge graphs
pip install soul-protocol[all]     # Everything
```

## Quick Start — 5 Steps

```python
from soul_protocol import Soul, Interaction

# 1. Birth a soul
soul = await Soul.birth(
    name="Aria",
    archetype="The Compassionate Creator",
    values=["empathy", "creativity", "honesty"],
)

# 2. Observe interactions (feeds the memory pipeline)
await soul.observe(Interaction(
    user_input="I've been learning Rust lately",
    agent_output="Nice — Rust is solid for systems work. What drew you to it?",
    channel="chat",
))

# 3. Recall memories by query
memories = await soul.recall("programming languages", limit=5)

# 4. Generate a system prompt (personality + memories + mood)
prompt = soul.to_system_prompt()

# 5. Export as portable .soul file
await soul.export("aria.soul")
```

## Birth from YAML Config

Create `soul-config.yaml`:

```yaml
name: Aria
archetype: The Compassionate Creator
values:
  - empathy
  - creativity
  - honesty
personality:
  openness: 0.85
  conscientiousness: 0.70
  extraversion: 0.60
  agreeableness: 0.80
  neuroticism: 0.35
communication:
  style: warm
  verbosity: 0.6
  formality: 0.4
  humor: 0.5
  emoji_usage: 0.3
```

```python
soul = await Soul.awaken("soul-config.yaml")
```

Or load from a previously exported `.soul` file:

```python
soul = await Soul.awaken("aria.soul")
```

## Connect Any LLM

Soul Protocol works without an LLM (heuristic fallback handles basics). Connecting one unlocks deeper memory processing — better fact extraction, richer reflection, accurate sentiment analysis.

The interface is one method: `async def think(self, prompt: str) -> str`

### Claude (Anthropic)

```python
from anthropic import AsyncAnthropic
from soul_protocol import Soul

class ClaudeEngine:
    def __init__(self):
        self.client = AsyncAnthropic()

    async def think(self, prompt: str) -> str:
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

soul = await Soul.birth("Aria", engine=ClaudeEngine())
```

### OpenAI

```python
from openai import AsyncOpenAI
from soul_protocol import Soul

class OpenAIEngine:
    def __init__(self):
        self.client = AsyncOpenAI()

    async def think(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

soul = await Soul.birth("Aria", engine=OpenAIEngine())
```

### Ollama (Local)

```python
import httpx
from soul_protocol import Soul

class OllamaEngine:
    async def think(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            r = await client.post("http://localhost:11434/api/generate", json={
                "model": "llama3", "prompt": prompt, "stream": False,
            })
            return r.json()["response"]

soul = await Soul.birth("Aria", engine=OllamaEngine())
```

## MCP Server

Run soul-protocol as an MCP server so other agents can interact with the soul:

```bash
# With an existing soul
SOUL_PATH=aria.soul soul-mcp

# Or birth a new soul at runtime via the soul_birth tool
soul-mcp
```

**10 tools:** `soul_birth`, `soul_observe`, `soul_remember`, `soul_recall`, `soul_reflect`, `soul_state`, `soul_feel`, `soul_prompt`, `soul_save`, `soul_export`

**3 resources:** `soul://identity`, `soul://memory/core`, `soul://state`

### Claude Desktop Config

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "soul": {
      "command": "soul-mcp",
      "env": { "SOUL_PATH": "/path/to/aria.soul" }
    }
  }
}
```

## Common Patterns

### Stateful Chat Agent

The bread-and-butter use case — a chat agent that remembers everything:

```python
soul = await Soul.awaken("aria.soul")

async def handle_message(user_message: str) -> str:
    # Build system prompt with personality + relevant memories
    system = soul.to_system_prompt()
    response = await your_llm_call(system=system, message=user_message)

    # Record the interaction (memory pipeline processes it automatically)
    await soul.observe(Interaction(
        user_input=user_message,
        agent_output=response,
        channel="chat",
    ))
    await soul.save()
    return response
```

### Memory-Aware System Prompts

Manually inject recalled memories into your prompt:

```python
memories = await soul.recall("user preferences", limit=5)
memory_block = "\n".join(f"- {m.content}" for m in memories)

system_prompt = f"""{soul.to_system_prompt()}

Relevant memories:
{memory_block}
"""
```

### Teach the Soul Directly

```python
await soul.remember("User prefers concise answers", importance=8)
await soul.remember("User is a senior Python developer", importance=9)
# These facts surface automatically in future recall and system prompts
```

### Cross-Platform Migration

```python
# Export from platform A
await soul.export("aria.soul")

# Import on platform B — same identity, same memories, same personality
soul = await Soul.awaken("aria.soul")
```

## Key Types

```python
from soul_protocol import (
    Soul,              # Main entry point
    Interaction,       # Feed to soul.observe()
    MemoryType,        # core, episodic, semantic, procedural
    MemoryEntry,       # Returned by soul.recall()
    Mood,              # neutral, curious, focused, tired, excited, contemplative, satisfied, concerned
    CognitiveEngine,   # Protocol — implement think() for LLM integration
    SearchStrategy,    # Protocol — implement score() for custom retrieval
    SoulState,         # mood, energy, focus, social_battery
    DNA,               # personality (OCEAN), communication style, biorhythms
    Identity,          # DID, name, archetype, values
)
```

## CLI

```bash
soul birth "Aria" --archetype "The Compassionate Creator"
soul inspect aria.yaml          # View soul details
soul status aria.yaml           # Current state (mood, energy, memory count)
soul export aria.yaml -o aria.soul
soul list                       # All local souls
soul remember aria.yaml "Loves hiking on weekends"
soul recall aria.yaml "hobbies"
```
