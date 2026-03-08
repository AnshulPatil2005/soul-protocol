<!-- COMPARISON.md — Feature comparison matrix: Soul Protocol vs competing AI memory systems.
     Created: 2026-03-08. Sources: WHITEPAPER.md sections 10/12, LAUNCH-STATUS.md benchmarks,
     HARD-QUESTIONS.md competitive positioning. -->

# Comparison: Soul Protocol vs. AI Memory Systems

How Soul Protocol compares to Mem0, MemGPT/Letta, LangChain Memory, Cognee, and OpenAI Memory. We try to be fair. Every system on this list solves real problems. The question is which problems you need solved.

---

## Feature Matrix

| Feature | Soul Protocol | Mem0 | MemGPT / Letta | LangChain Memory | Cognee | OpenAI Memory |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Portable identity** (.soul file) | Yes | No | No | No | No | No |
| **Psychology pipeline** (somatic markers, significance gate, self-model) | Yes | No | No | No | No | No |
| **Personality model** (OCEAN Big Five, structured) | Yes | No | No | No | No | No |
| **Significance gating** (LIDA — decide what's worth remembering) | Yes | No | No | No | No | No |
| **Emotional memory** (somatic markers on every memory) | Yes | No | No | No | No | No |
| **Self-model** (Klein — emergent identity from experience) | Yes | No | No | No | No | No |
| **Activation decay** (ACT-R — recency + frequency scoring) | Yes | No | No | No | No | No |
| **Knowledge graph** (temporal entity-relations) | Yes | No | No | No | Yes | No |
| **Vector search** | Pluggable | Built-in | Via tools | Built-in | Built-in | Internal |
| **Pluggable LLM** (any provider, including offline) | Yes | Partial | No (OpenAI-focused) | Yes | Yes | No (OpenAI only) |
| **Heuristic fallback** (zero LLM calls, zero cost) | Yes | No | No | No | No | No |
| **Offline mode** (no network required) | Yes | No | No | Partial | No | No |
| **Multi-language schemas** (JSON Schema for any language) | Yes | No | No | No | No | No |
| **Open standard / RFC process** | Yes | No | No | No | No | No |
| **Context window management** | No | No | Yes | No | No | No |
| **RAG pipeline** | No (use with) | Yes | Via tools | Yes | Yes | Internal |
| **Production vector DB integrations** | Planned | Yes | Yes | Yes | Yes | Internal |
| **Managed cloud service** | No | Yes | Yes | No | Yes | Yes |

---

## Benchmark Comparison

Head-to-head results from our five-tier validation. Soul Protocol and Mem0 (v1.0.5) processed identical conversations, scored by the same LLM judge. Stateless baseline included for reference.

| Test | Soul Protocol | Mem0 v1.0.5 | Stateless Baseline |
|------|:---:|:---:|:---:|
| **Overall** | **8.5** | 6.0 | 3.0 |
| **Emotional Continuity** | **9.2** | 7.0 | 1.8 |
| **Hard Recall** (fact buried under 30+ turns) | **7.8** | 5.1 | 4.2 |

Component ablation (which parts of Soul Protocol actually matter):

| Condition | Response Quality | Hard Recall | Emotional Continuity | Overall |
|-----------|:---:|:---:|:---:|:---:|
| **Full Soul** (personality + memory) | 8.3 +/- 0.3 | 8.4 +/- 0.4 | 9.3 +/- 0.2 | **8.7 +/- 0.2** |
| **RAG Only** (memory, no personality) | 7.8 +/- 0.3 | 8.2 +/- 0.2 | 9.3 +/- 0.2 | 8.4 +/- 0.2 |
| **Personality Only** (no memory) | 7.8 +/- 0.4 | 5.9 +/- 0.7 | 7.2 +/- 0.7 | 7.0 +/- 0.4 |

Validation details: 5 judge models from 4 providers (Anthropic, Google, DeepSeek, Meta). 20/20 judgments favored Soul over stateless baseline. Total validation cost under $5. Full methodology in the [whitepaper](../WHITEPAPER.md#12-empirical-validation).

---

## How Each System Differs

### Mem0

Mem0 is a persistent memory layer for LLM applications. It stores user facts and preferences in a vector database and retrieves them via similarity search. It does this well and has production-ready integrations with major vector stores.

**Where Soul Protocol differs:** Mem0 treats memory as a retrieval problem. Soul Protocol treats it as an identity problem. Mem0 stores facts. Soul Protocol stores facts with emotional context (somatic markers), filters what's worth storing (significance gate), lets memories strengthen or fade based on usage (ACT-R decay), and builds an emergent self-concept from accumulated experience (Klein self-model). In benchmarks, both systems beat a stateless baseline, but Soul Protocol scored 8.5 overall vs. Mem0's 6.0, with the largest gap in emotional continuity (9.2 vs. 7.0).

Mem0 has no concept of portable identity. There is no file format, no personality model, and no way to move a memory state between platforms.

### MemGPT / Letta

MemGPT solves a specific and important problem: how to give an LLM access to more memory than fits in a single context window. It pages memory in and out, uses function calls to manage retrieval, and effectively gives an LLM an operating system for its own context.

**Where Soul Protocol differs:** MemGPT manages *what fits in the prompt*. Soul Protocol defines *who the agent is*. MemGPT doesn't have personality, portable identity, emotional markers, or a self-model. Soul Protocol doesn't manage context windows. The two are complementary: a MemGPT system could use Soul Protocol for the identity layer that gets paged into context.

### LangChain Memory

LangChain provides memory modules for RAG pipelines: conversation buffers, summary buffers, entity memory, vector store-backed retrieval. These are retrieval infrastructure components.

**Where Soul Protocol differs:** LangChain memory answers "how do I find relevant context?" Soul Protocol answers "who is this AI and what does it remember?" LangChain has no significance filtering (everything gets stored), no emotional tagging, no activation decay, no self-model, and no portable file format. Soul Protocol's memory pipeline decides *whether* to store something before deciding *how* to retrieve it.

### Cognee

Cognee builds knowledge graphs from unstructured data with domain isolation. It has strong graph construction and query capabilities with production integrations.

**Where Soul Protocol differs:** Cognee's knowledge graph is locked to its runtime. Soul Protocol's knowledge graph is portable (temporal edges serialize into the `.soul` file) and comes alongside four other memory tiers. Soul Protocol adds identity, personality, emotional memory, and significance gating that Cognee doesn't address. Cognee has stronger graph-specific features (domain isolation, advanced queries) than Soul Protocol's current graph implementation.

### OpenAI Memory

OpenAI's built-in memory stores facts about users across conversations within the OpenAI ecosystem. It's automatic, requires no setup, and works well within ChatGPT and the API.

**Where Soul Protocol differs:** OpenAI Memory is per-account, per-platform. You cannot export it, move it to another provider, or inspect the raw data. Soul Protocol is a portable file you own. Rename it to `.zip`, read the JSON, load it with Claude today and Ollama tomorrow. OpenAI Memory also has no personality model, no emotional markers, and no self-model. It stores facts; Soul Protocol stores identity.

---

## When to Use What

Not every project needs Soul Protocol. Here's an honest guide.

**Use Mem0 if** you need a production-ready persistent memory layer with minimal setup, you're building a standard chatbot that needs to remember user preferences, and you don't need portable identity or emotional context. Mem0 is simpler to deploy and has mature vector store integrations.

**Use MemGPT/Letta if** your primary problem is context window management. If your agent needs to work with very long conversations and you need to page information in and out of context efficiently, MemGPT is purpose-built for that.

**Use LangChain Memory if** you're already in the LangChain ecosystem and need basic conversation persistence. Buffer memory and entity memory are straightforward to add to an existing chain. If you just need "remember what the user said earlier in this conversation," LangChain memory modules are sufficient.

**Use Cognee if** your primary need is building and querying knowledge graphs from unstructured data with strong domain isolation. If your application is more about structured knowledge than companion identity, Cognee's graph-first approach may be a better fit.

**Use OpenAI Memory if** you're building exclusively on OpenAI's platform and want zero-config persistence. It just works, with no additional infrastructure.

**Use Soul Protocol if** you're building an AI companion that needs to feel like someone rather than something. If your agent needs a persistent personality that evolves, memories that carry emotional weight, a sense of self that develops from experience, and the ability to move between platforms without losing its identity. Soul Protocol is designed for long-lived AI relationships, not single-session retrieval.

Soul Protocol also works alongside these systems. You can use Mem0 or LangChain for retrieval and Soul Protocol for the identity layer on top. The `CognitiveEngine` interface means any LLM backend works, and the `.soul` file format means the identity is never locked to one platform.
