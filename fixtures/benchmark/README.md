# Benchmark fixtures

Local-only snapshots of real souls used to validate the 0.3.2 primitives
and the memory-journal spike against production-like data. Not committed —
`*.soul` is gitignored (private memory content).

## Regenerating

```bash
cp /Users/prakash-1/Documents/paw-workspace/soul-protocol/.soul/pocketpaw.soul \
   fixtures/benchmark/pocketpaw-snapshot-$(date +%Y-%m-%d).soul
```

## Why local-only

- Contains real conversation memory and private context.
- Binary-ish zip archives; git churn is ugly.
- Always reproducible from the live soul.

Tests that need benchmark data should skip gracefully when the fixture
is missing — CI doesn't have access to these snapshots.
