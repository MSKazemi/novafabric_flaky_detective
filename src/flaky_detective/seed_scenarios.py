"""Generate synthetic NovaFabric capsules for the demo + tests — no LLM/API keys needed.

The record fields below match exactly what `novafabric.diff.DiffEngine` reads (verified against
novafabric/diff/_engine.py and _align.py v0.56.3):

- model-calls.jsonl : parent_span_id, model_call_id, gen_ai.request.model,
                      gen_ai.request.messages, gen_ai.response.choices
- tool-calls.jsonl  : tool_name, tool_call_id, arguments, result
- outputs/<file>    : compared by SHA-256
- capsule.yaml      : run_id (used only for report labels)

Three capsules are generated so the classifier's three verdicts are all exercisable by diffing
against `baseline`:

    analyze(baseline, baseline)   -> pass
    analyze(baseline, flaky)      -> flaky        (only the model response wording differs)
    analyze(baseline, regression) -> regression   (tool result + final output diverge)
"""
from __future__ import annotations

import json
from pathlib import Path

_USER_MSG = [{"role": "user", "content": "Summarize the search results"}]
_SEARCH_ARGS = {"query": "climate policy 2026"}
_SEARCH_RESULT_OK = ["article1", "article2", "article3"]


def _choices(text: str) -> list[dict]:
    return [{"index": 0, "message": {"role": "assistant", "content": text}}]


def _write_capsule(
    capsule_dir: Path,
    *,
    run_id: str,
    model_response: str,
    tool_result: list,
    stdout: str,
) -> Path:
    capsule_dir.mkdir(parents=True, exist_ok=True)
    (capsule_dir / "capsule.yaml").write_text(f"run_id: {run_id}\nstatus: success\n")

    model_call = {
        "parent_span_id": "span-summarize",
        "model_call_id": f"{run_id}-mc1",
        "gen_ai.request.model": "gpt-4o-mini",
        "gen_ai.request.messages": _USER_MSG,
        "gen_ai.response.choices": _choices(model_response),
    }
    (capsule_dir / "model-calls.jsonl").write_text(json.dumps(model_call) + "\n")

    tool_call = {
        "tool_name": "web_search",
        "tool_call_id": f"{run_id}-tc1",
        "arguments": _SEARCH_ARGS,
        "result": tool_result,
    }
    (capsule_dir / "tool-calls.jsonl").write_text(json.dumps(tool_call) + "\n")

    outputs = capsule_dir / "outputs"
    outputs.mkdir(exist_ok=True)
    (outputs / "stdout.txt").write_text(stdout)
    return capsule_dir


def build_scenarios(base_dir: Path) -> dict[str, Path]:
    """Write the three capsules under base_dir and return {name: path}."""
    base_dir = Path(base_dir)
    baseline = _write_capsule(
        base_dir / "baseline",
        run_id="baseline",
        model_response="The top 3 results discuss climate policy, renewable energy, and carbon capture.",
        tool_result=_SEARCH_RESULT_OK,
        stdout="Summary: climate policy, renewable energy, carbon capture\n",
    )
    # FLAKY: identical request/tool/output; only the model response wording changes.
    flaky = _write_capsule(
        base_dir / "flaky",
        run_id="flaky",
        model_response="Based on the search, I found content about climate change policy, "
        "green energy programs, and carbon sequestration methods.",
        tool_result=_SEARCH_RESULT_OK,
        stdout="Summary: climate policy, renewable energy, carbon capture\n",
    )
    # REGRESSION: the tool result changed, so the final output diverges.
    regression = _write_capsule(
        base_dir / "regression",
        run_id="regression",
        model_response="I was unable to find relevant results.",
        tool_result=["no results"],
        stdout="Summary: no results found\n",
    )
    return {"baseline": baseline, "flaky": flaky, "regression": regression}
