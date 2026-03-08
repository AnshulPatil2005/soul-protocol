<!-- FAQ.md — Public-facing frequently asked questions for Soul Protocol.
     Created: 2026-03-08. Adapted from idocs/HARD-QUESTIONS.md with benchmark data
     from LAUNCH-STATUS.md and technical details from WHITEPAPER.md. -->

# Frequently Asked Questions

---

### 1. How is this different from Mem0?

Mem0 is a vector memory layer. It stores user facts and retrieves them by similarity. Soul Protocol is an identity protocol. It adds significance gating (deciding what's worth remembering), somatic markers (emotional context on every memory), ACT-R activation decay (memories strengthen or fade based on usage), and a self-model that evolves from experience. In head-to-head benchmarks on identical conversations, Soul Protocol scored 8.5 overall vs. Mem0's 6.0, with the largest gap in emotional continuity (9.2 vs. 7.0). The difference isn't retrieval quality -- it's what gets stored alongside the facts. See [docs/COMPARISON.md](docs/COMPARISON.md) for the full matrix.

---

### 2. How is this different from MemGPT/Letta?

MemGPT manages context windows -- it pages memory in and out so an LLM can work with more information than fits in a single prompt. Soul Protocol defines who the agent *is*: personality, emotional memory, self-concept, portable identity. They solve different problems at different layers. A MemGPT system could use Soul Protocol for the identity data that gets paged into context. They're complementary, not competitive.

---

### 3. Why not just use vector embeddings?

Vector embeddings answer "what text is similar to this query?" That's one part of memory. Human memory also uses recency and frequency (ACT-R power-law decay), emotional salience (Damasio's somatic markers), significance filtering (LIDA -- not everything deserves to be remembered), and self-relevance (memories shape who you think you are). Soul Protocol models all of these. Vector search is pluggable through the `EmbeddingProvider` interface -- the protocol ships HashEmbedder and TFIDFEmbedder, and you can swap in OpenAI, Cohere, or local embeddings. Embeddings find similar things. Psychology determines what matters. You need both.

---

### 4. The heuristic engine sounds like a toy.

The heuristic engine (word-list sentiment, formula-based significance, regex fact extraction) is intentionally simple. It's the offline fallback for when you don't have an LLM available, when you're running tests and need deterministic results, when cost matters, or when privacy requires that no text leaves the machine. The `CognitiveEngine` protocol lets you plug in any LLM for real analysis. The architecture is: LLM when available, heuristic when not. The heuristic has a low ceiling but a high floor -- it never crashes, never costs money, never leaks data, and never hallucinates.

---

### 5. What about hallucinated facts?

Valid concern. Current mitigations: structured JSON schemas in extraction prompts reduce hallucination, a validation layer rejects unparseable output, the heuristic fallback kicks in when LLM output can't be parsed, and fact deduplication checks token overlap against existing facts (>70% similarity = skip). The system also tracks fact conflict through `superseded_by` chains rather than silently overwriting. Planned additions include confidence scores on extracted facts, source attribution, and user correction mechanisms. The system degrades gracefully -- bad extraction results in a missed fact, not corrupted state.

---

### 6. How does this handle multi-user?

Currently, a soul bonds to one entity (the `bonded_to` field). Multi-user is not built yet. The architecture supports it: the entity graph already tracks relationships, `Interaction.metadata` can carry user IDs, and the self-model could track per-user relationship context. The routing logic needs to be added. This is a planned feature, not a current capability.

---

### 7. Can I use this with my LLM? (Claude, GPT, Ollama, local)

Yes. The `CognitiveEngine` protocol is a single method: `async def think(self, prompt: str) -> str`. Implement it with any LLM -- Claude, GPT, Gemini, Ollama, a local model, or anything that takes text in and returns text out. The soul handles prompt construction and response parsing internally. Without any engine at all, the `HeuristicEngine` provides deterministic processing with zero API calls. One integration point, three lines of code.

---

### 8. How do .soul files work exactly?

A `.soul` file is a ZIP archive. Rename it to `.zip` and open it with any archive tool. Inside: `manifest.json` (version, soul ID, checksums), `soul.json` (identity, personality DNA, evolution config), `state.json` (mood, energy, focus), `dna.md` (human-readable personality blueprint), and a `memory/` directory containing `core.json`, `episodic.json`, `semantic.json`, `procedural.json`, `graph.json`, and `self_model.json`. Everything is JSON. JSON Schemas are auto-generated from the protocol models, so any language with a JSON Schema validator can read and write `.soul` files without the Python SDK.

---

### 9. Is there a TypeScript implementation?

Not yet. The protocol spec is 624 lines of Pydantic models designed for porting. JSON Schemas are auto-generated from those models, so you can validate `.soul` files in TypeScript (or any language) today using standard JSON Schema validators. A native TypeScript SDK is on the roadmap. If you want to build one, the spec layer is intentionally small and self-contained.

---

### 10. Why psychology? Isn't this overengineered?

The psychology isn't decoration -- it's the mechanism that makes memory selective. Without significance gating (LIDA), every interaction gets stored and you get memory bloat. Without activation decay (ACT-R), old memories never fade and retrieval degrades. Without somatic markers (Damasio), there's no emotional context and the agent can't track how a user's experience *felt*. In our component ablation, removing these components dropped emotional continuity scores from 9.3 to 7.2. The theories aren't complex to implement -- LIDA is a weighted formula, ACT-R is a power law, somatic markers are three floats. The complexity is in knowing which theories to apply, not in the code.

---

### 11. What about privacy/security?

The `.soul` file is a local ZIP archive the user controls. No cloud required, no phone-home, no telemetry. The protocol makes zero network calls. When a `CognitiveEngine` uses a cloud LLM, interaction text goes to that provider -- but that's the consumer's choice, not the protocol's. The heuristic engine processes everything locally with zero external calls. Eternal storage (Arweave/IPFS) is opt-in and planned to support user-controlled encryption. The file format is inspectable: rename to `.zip`, read the JSON, verify exactly what's stored.

---

### 12. How do I integrate this into my existing agent?

Three steps. First, birth a soul: `soul = await Soul.birth("Name", engine=YourEngine())`. Second, call `soul.observe(Interaction(user_input=..., agent_output=...))` after each exchange -- this runs the full psychology pipeline (sentiment, significance, fact extraction, self-model update). Third, use `soul.to_system_prompt()` to inject the soul's personality and relevant memories into your agent's system prompt, and `soul.recall(query)` to retrieve specific memories. The soul produces identity data. Your agent framework handles everything else. Works with LangChain, LlamaIndex, custom agents, or bare API calls.
