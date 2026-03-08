<!-- RFC-003-COGNITIVE-ENGINE-PROTOCOL.md — Defines the CognitiveEngine single-method -->
<!-- protocol, HeuristicEngine fallback, CognitiveProcessor orchestrator, and LLM integration. -->

# RFC-003: Cognitive Engine Protocol

**Status:** Draft -- Open for feedback
**Author:** Soul Protocol Community
**Date:** 2026-03-08

## Summary

Soul Protocol needs a way to think -- to analyze sentiment, assess significance, extract
facts, reflect on identity. The `CognitiveEngine` protocol solves this with a single
async method: `think(prompt: str) -> str`. Any LLM, any provider, any local model can
implement this one method and immediately power a soul's cognitive pipeline. When no LLM
is available, the `HeuristicEngine` provides a zero-dependency fallback using word lists,
regex patterns, and formula-based scoring.

This design prioritizes maximum compatibility over maximum capability. A soul that works
with Claude, GPT-4, Ollama, and a $0 heuristic fallback is more valuable than one that
only works with one provider's structured output API.

## Problem Statement

AI memory systems typically hardcode their LLM integration: specific API clients, model
names, structured output formats. This creates three problems:

1. **Vendor lock-in.** Switch LLM providers, rewrite the integration.
2. **Cost barrier.** Every memory operation costs an API call. Small teams and hobbyists
   can't afford it for every interaction.
3. **Offline failure.** No internet, no API key, no memory processing.

Soul Protocol needs cognitive capabilities (sentiment detection, fact extraction,
self-reflection) that work across any LLM and degrade gracefully to zero-cost
heuristics when no LLM is available.

## Proposed Solution

### CognitiveEngine Protocol

The protocol is deliberately minimal -- one method, no configuration:

```python
@runtime_checkable
class CognitiveEngine(Protocol):
    """Interface for the soul's cognitive processing.

    The consumer provides an LLM via this interface. The soul uses it
    to think about emotions, significance, facts, and identity.

    Simplest implementation:
        class MyCognitive:
            async def think(self, prompt: str) -> str:
                return await my_llm_client.complete(prompt)
    """

    async def think(self, prompt: str) -> str: ...
```

That's it. One async method. String in, string out.

### Why Single Method

The protocol could have defined separate methods for each cognitive task:
`detect_sentiment()`, `extract_facts()`, `assess_significance()`. Instead, it uses a
single `think()` method because:

- **Maximum compatibility.** Every LLM API in existence can take a string prompt and
  return a string response. No structured output, no tool calling, no function schemas
  required.
- **Prompt-driven routing.** The `CognitiveProcessor` constructs task-specific prompts
  with `[TASK:xxx]` markers. The engine doesn't need to know what task it's performing.
- **Simplest possible integration.** A Claude adapter is 5 lines. A GPT adapter is 5
  lines. An Ollama adapter is 5 lines.

### LLM Integration Examples

**Claude (Anthropic):**

```python
class ClaudeEngine:
    def __init__(self, client):
        self.client = client

    async def think(self, prompt: str) -> str:
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
```

**OpenAI GPT:**

```python
class GPTEngine:
    def __init__(self, client):
        self.client = client

    async def think(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
```

**Ollama (local):**

```python
class OllamaEngine:
    async def think(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            r = await client.post("http://localhost:11434/api/generate",
                json={"model": "llama3", "prompt": prompt, "stream": False})
            return r.json()["response"]
```

### HeuristicEngine Fallback

When no LLM is available, the `HeuristicEngine` routes prompts to task-specific
heuristics based on `[TASK:xxx]` markers in the prompt text:

```python
class HeuristicEngine:
    """Zero-dependency fallback that wraps v0.2.0 heuristic modules."""

    async def think(self, prompt: str) -> str:
        task = _extract_task_marker(prompt)

        if task == "sentiment":
            return self._sentiment(prompt)     # word-list matching
        elif task == "significance":
            return self._significance(prompt)  # formula-based scoring
        elif task == "extract_facts":
            return self._extract_facts(prompt) # 18 regex patterns
        elif task == "extract_entities":
            return self._extract_entities(prompt)
        elif task == "self_reflection":
            return self._self_reflection(prompt)
        elif task == "reflect":
            return json.dumps({...})           # minimal reflection

        return json.dumps({"error": f"unknown task: {task}"})
```

The heuristic engine produces identical output format to LLM responses (JSON), so
downstream code doesn't need to distinguish between the two paths.

Capabilities comparison:

| Task | LLM Engine | Heuristic Engine |
|------|-----------|-----------------|
| Sentiment | Nuanced emotional analysis | Word-list + intensity modifiers |
| Significance | Context-aware scoring | Token overlap + arousal proxy |
| Fact extraction | Free-form understanding | 18 regex patterns |
| Entity extraction | Relationship inference | Known tech terms + proper nouns |
| Self-reflection | Genuine identity reasoning | Minimal placeholder |
| Reflection/consolidation | Theme discovery, pattern analysis | Returns None (skipped) |

### CognitiveProcessor (Internal Orchestrator)

The `CognitiveProcessor` sits between the soul and the engine. It constructs prompts,
parses responses, validates output, and falls back to heuristics on parse failure:

```python
class CognitiveProcessor:
    def __init__(self, engine: CognitiveEngine,
                 fallback: HeuristicEngine | None = None, ...):
        self._engine = engine
        self._fallback = fallback
        self._is_heuristic_only = isinstance(engine, HeuristicEngine)

    async def detect_sentiment(self, text: str) -> SomaticMarker: ...
    async def assess_significance(self, interaction, values, recent) -> SignificanceScore: ...
    async def extract_facts(self, interaction, existing_facts) -> list[MemoryEntry]: ...
    async def extract_entities(self, interaction) -> list[dict]: ...
    async def update_self_model(self, interaction, facts, self_model) -> None: ...
    async def reflect(self, episodes, self_model, soul_name) -> ReflectionResult | None: ...
```

Each method follows the same pattern:
1. Check `_is_heuristic_only` -- if true, call the v0.2.0 heuristic directly (fast path)
2. Construct a task-specific prompt from templates in `cognitive/prompts.py`
3. Call `engine.think(prompt)` and parse the JSON response
4. Validate and clamp values to expected ranges
5. On parse failure, fall back to heuristic if a fallback is configured

### JSON Response Parsing

LLM responses are parsed with a robust `_parse_json()` function that handles:
1. Direct JSON
2. Markdown-fenced JSON blocks (` ```json ... ``` `)
3. JSON embedded after preamble text (finds first `{` or `[`)

This tolerates the natural variability in LLM output formatting.

## Implementation Notes

- CognitiveEngine protocol: `src/soul_protocol/runtime/cognitive/engine.py` (line 66-78)
- HeuristicEngine: `src/soul_protocol/runtime/cognitive/engine.py` (line 86-173)
- CognitiveProcessor: `src/soul_protocol/runtime/cognitive/engine.py` (line 246-480)
- Prompt templates: `src/soul_protocol/runtime/cognitive/prompts.py`
- The protocol lives in the runtime layer, not the spec layer. This is intentional --
  the spec defines data primitives (Identity, MemoryEntry, MemoryStore), while the
  runtime defines processing interfaces (CognitiveEngine).

## Alternatives Considered

**Multi-method protocol.** Separate methods for each cognitive task would give type
safety and clearer contracts, but would require every LLM adapter to implement 6+
methods instead of 1. The current design pushes task-specific logic into prompt
templates, keeping the adapter layer trivially simple.

**Structured output requirement.** Using provider-specific structured output APIs
(OpenAI function calling, Anthropic tool use) would give more reliable parsing but
would break the universal compatibility goal. Not every LLM supports structured output.

**Middleware/plugin pattern.** Instead of a single engine, a chain of middleware
processors. More flexible but significantly more complex to implement and debug.

## Open Questions

1. **Streaming support.** Should the protocol support streaming responses
   (`async def think_stream(prompt: str) -> AsyncIterator[str]`)? Use cases:
   real-time sentiment analysis during long conversations, progress feedback on
   reflection tasks. Risk: complicates the interface for a feature most cognitive
   tasks don't need.

2. **Structured output.** Should there be an optional `think_structured()` method
   that returns parsed JSON directly, for engines that support it? This could skip
   the `_parse_json()` step and reduce LLM errors.

3. **Tool use.** Should the engine support tool calling for tasks like web search
   during fact extraction or memory retrieval during reflection? This would make the
   engine more capable but significantly more complex.

4. **Token budgets.** Should `think()` accept a `max_tokens` parameter? Currently
   the adapter controls token limits internally. Exposing it would let the processor
   request shorter responses for simple tasks (sentiment: ~50 tokens) vs. longer
   responses for complex tasks (reflection: ~500 tokens).

5. **Engine metadata.** Should the protocol include a `capabilities` property so
   the processor can adapt its prompting strategy based on what the engine supports
   (e.g., structured output, large context windows, vision)?

## References

- Anderson, J.R. (2007). *How Can the Human Mind Occur in the Physical Universe?*
- Klein, S.B. (2004). *The Cognitive Neuroscience of Knowing One's Self*
- `src/soul_protocol/runtime/cognitive/engine.py` -- full implementation
- `src/soul_protocol/runtime/cognitive/prompts.py` -- prompt templates
- `docs/cognitive-engine.md` -- user-facing documentation
