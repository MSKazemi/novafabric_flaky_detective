# Demo scenarios

> ⚠️ **Superseded (2026-06-25).** The live `nova capture python agent.py` flow below does NOT
> work for this demo: the stand-in `baseline_agent/agent.py` makes no real LLM/tool calls, so
> captured `model-calls.jsonl` / `tool-calls.jsonl` are empty, and its "flaky" run prints the
> reworded answer to stdout — which the classifier reads as a **regression**, not flaky. Use the
> synthetic capsules from `flaky_detective.seed_scenarios.build_scenarios()` instead (exercised by
> the tests and served by the API as `fixture:baseline|flaky|regression`). `agent.py` is kept only
> as an illustration of the scenario shape.

Two captured runs that make the classifier's job visible in the demo video:

1. **FLAKY** — the agent's LLM phrases its answer differently on a re-run, but the tool calls
   and final output are identical. Flaky Detective should say `flaky`.
2. **REGRESSION** — a tool's behavior changed (e.g. a lookup now returns a different value),
   so the final output diverges. Flaky Detective should say `regression`.

## How to produce the capsules

```bash
. ../.venv/bin/activate

# Baseline capture
nova capture python baseline_agent/agent.py --output-dir ../captures/baseline

# Flaky re-run (same code, non-deterministic model text)
SCENARIO=flaky    nova capture python baseline_agent/agent.py --output-dir ../captures/flaky

# Regression re-run (tool behavior changed)
SCENARIO=regression nova capture python baseline_agent/agent.py --output-dir ../captures/regression
```

Then:
```bash
curl -s localhost:8000/analyze -H 'content-type: application/json' \
  -d '{"baseline_capsule":"../captures/baseline","current_capsule":"../captures/flaky"}'      # -> flaky
curl -s localhost:8000/analyze -H 'content-type: application/json' \
  -d '{"baseline_capsule":"../captures/baseline","current_capsule":"../captures/regression"}' # -> regression
```

> The `agent.py` here is a stand-in "system under test". Swap in any real agent later; the
> classifier only needs two NovaFabric capsules to compare.
