# Soul Protocol Validation Study

<!-- Created 2026-03-06. Documentation for the research simulation framework. -->

## What This Proves

The Soul Protocol claims that psychology-informed memory (OCEAN personality, significance gating, somatic markers, bond tracking) produces measurably better AI companion behavior than naive approaches like raw RAG or stateless interaction.

This simulation framework tests that claim empirically. It runs 1000 simulated agents across 5 memory conditions and 4 use cases, producing 20,000+ experimental runs with publication-grade statistical analysis. The design is a full factorial ablation study: each layer of the Soul Protocol pipeline is toggled independently so we can attribute improvements to specific components.

## How to Run

**Smoke test** (10 agents, 2 conditions, 1 use case):

```bash
python -m research.run --quick
```

**Full experiment** (1000 agents, all conditions, all use cases):

```bash
python -m research.run
```

**Custom configuration:**

```bash
python -m research.run --agents 500 --conditions none,full_soul --use-cases companion,coding --seed 123
```

**Unit tests:**

```bash
uv run pytest research/test_smoke.py -v
```

## Architecture

| Module | Description |
|--------|-------------|
| `config.py` | Experiment configuration: conditions enum, use cases enum, hyperparameters, reproducibility seed. |
| `agents.py` | Generates diverse agent profiles with realistic OCEAN distributions and user profiles per use case. |
| `scenarios.py` | Scenario bank: multi-turn interaction sequences with planted facts and recall queries for 4 domains. |
| `conditions.py` | Implements the 5 memory conditions as pluggable classes (the independent variable in the ablation). |
| `metrics.py` | Metric collection (6 categories) and statistical utilities (Cohen's d, Mann-Whitney U, confidence intervals). |
| `simulator.py` | Core simulation engine: runs the full factorial experiment with async batching and error isolation. |
| `analysis.py` | Statistical analysis: summary tables, pairwise comparisons, ablation chain, per-use-case breakdown, report generation. |
| `run.py` | CLI entry point: parses arguments, builds config, runs simulation, writes results. |

## Experimental Design

### Conditions (independent variable)

1. **No Memory** (`none`). Stateless baseline. No information persists between turns.
2. **RAG Only** (`rag_only`). Pure vector similarity retrieval. Everything is stored, nothing is filtered.
3. **RAG + Significance** (`rag_sig`). Adds LIDA-inspired significance gating. Only important interactions are stored.
4. **Full Pipeline, No Emotion** (`full_no_emo`). Full Soul Protocol stack minus somatic markers and bond tracking.
5. **Full Soul Protocol** (`full_soul`). Complete stack: significance gating, somatic markers, bond, skills, personality.

### Use Cases (evaluation domains)

1. **Customer Support** (`support`). Account issues, follow-up sessions, cross-session recall of user details.
2. **Coding Assistant** (`coding`). Language/framework preferences, debugging context, tool preferences.
3. **Personal Companion** (`companion`). Hobbies, food preferences, emotional states, life events.
4. **Knowledge Worker** (`knowledge`). Research domains, tool preferences, boss communication style.

### Key Metrics (dependent variables)

- **Recall precision**: Of returned memories, how many were relevant?
- **Recall hit rate**: Was the planted fact found in top-k results?
- **Emotion accuracy**: Did somatic markers match expected emotional tone?
- **Bond strength**: Final bond level after all interactions.
- **Personality drift**: OCEAN trait stability over time (lower is better).
- **Memory compression**: Interactions per stored memory (higher means more selective).

## Output

Results are written to `research/results/` (configurable via `--output`). A full run produces:

- `analysis_report.md`. Markdown report with summary statistics, pairwise comparisons, ablation table, and per-use-case analysis.
- `summary_statistics.csv`. Aggregated stats (mean, std, median, 95% CI) grouped by condition and use case.
- `pairwise_comparisons.csv`. Full Soul Protocol vs. every other condition for each metric, with effect sizes and p-values.

## Methodology

**Effect size**: Cohen's d with pooled standard deviation. Interpreted as negligible (< 0.2), small (0.2-0.5), medium (0.5-0.8), or large (> 0.8).

**Significance testing**: Mann-Whitney U test (non-parametric, no normality assumption). Two-tailed p-values via normal approximation. Significance threshold: p < 0.05.

**Confidence intervals**: 95% CI using t-distribution approximation (t=1.96 for n > 30, t=2.0 otherwise).

**Reproducibility**: All randomness is seeded. Default seed is 42. The same seed and configuration will produce identical results.
