"""Flaky-vs-regression classifier.

Core idea (verified against NovaFabric v0.56.3 — see docs/NOVAFABRIC-API.md and the diff
engine source at novafabric/diff/_engine.py):

`DiffEngine().compare(a, b)` aligns two capsules and returns a `DiffReport`. Its `as_dict()`
is nested under `sections`:

    {
      "summary": {"changed", "added", "removed"},
      "sections": {
        "environment": {"changes": [...]},
        "model_calls": {"changed", "pairs": [ {"changed","span_id",
                         "request_changed","response_changed"} | {"added"|"removed", ...} ]},
        "tool_calls":  {"changed", "pairs": [ {"changed","tool_name","result_changed"}
                         | {"added"|"removed","tool_name"} ]},
        "outputs":     {"changes": [ {"path","before_hash","after_hash"} ]},
      },
    }

Heuristic:
  - No changes at all                          -> PASS  (the "failure" was noise; re-run)
  - ONLY a model-call *response* differs, with request/tools/outputs/env all identical
                                               -> FLAKY (non-deterministic generation, same effect)
  - tool results/added/removed, outputs, a model *request*, or env drift differ
                                               -> REGRESSION (behavior actually changed)

The UiPath Agent Builder agent (LLM) turns this deterministic signal into the human-facing
verdict + remediation. This function returns the signal + a heuristic verdict so the demo works
even without the LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Verdict = Literal["pass", "flaky", "regression"]


@dataclass
class AnalysisResult:
    verdict: Verdict
    confidence: float
    differing_step: str | None
    remediation: str
    signal: dict = field(default_factory=dict)  # full DiffReport.as_dict()


def analyze(baseline_capsule: Path, current_capsule: Path) -> AnalysisResult:
    """Compare two NovaFabric capsules and classify the difference."""
    from novafabric.diff import DiffEngine  # noqa: PLC0415  (NovaFabric — public on PyPI)

    report = DiffEngine().compare(capsule_a=baseline_capsule, capsule_b=current_capsule)
    signal = report.as_dict()
    sections = signal.get("sections", {})

    model_pairs = sections.get("model_calls", {}).get("pairs", []) or []
    tool_pairs = sections.get("tool_calls", {}).get("pairs", []) or []
    output_changes = sections.get("outputs", {}).get("changes", []) or []
    env_changes = sections.get("environment", {}).get("changes", []) or []

    outputs_changed = bool(output_changes)
    env_changed = bool(env_changes)
    tools_changed = any(
        p.get("result_changed") or p.get("added") or p.get("removed") for p in tool_pairs
    )
    model_structural = any(p.get("added") or p.get("removed") for p in model_pairs)
    model_request_changed = any(p.get("request_changed") for p in model_pairs)
    model_response_changed = any(p.get("response_changed") for p in model_pairs)

    # A real behavioral change is anything other than a pure model-response rewording.
    regression_signal = (
        outputs_changed or tools_changed or env_changed or model_structural or model_request_changed
    )

    if not (regression_signal or model_response_changed):
        return AnalysisResult(
            verdict="pass",
            confidence=0.95,
            differing_step=None,
            remediation="No behavioral difference vs baseline. Treat the original failure as noise; re-run.",
            signal=signal,
        )

    if model_response_changed and not regression_signal:
        return AnalysisResult(
            verdict="flaky",
            confidence=0.8,
            differing_step=_first_model_response_step(model_pairs),
            remediation=(
                "Only the model's response text varied; request, tool results, outputs, and "
                "environment are identical. This is non-deterministic flakiness. Pin temperature/"
                "seed for the test, or assert on tool outcomes rather than raw model text."
            ),
            signal=signal,
        )

    return AnalysisResult(
        verdict="regression",
        confidence=0.85,
        differing_step=_first_regression_step(
            tool_pairs, output_changes, model_pairs, env_changes
        ),
        remediation=(
            "Tool results, final outputs, the model request, or the environment changed vs "
            "baseline — behavior actually diverged. Inspect the flagged step; this is a real "
            "regression, not flakiness."
        ),
        signal=signal,
    )


def _first_model_response_step(model_pairs: list[dict]) -> str | None:
    for p in model_pairs:
        if p.get("response_changed"):
            return f"model call (span {p.get('span_id')})"
    return None


def _first_regression_step(
    tool_pairs: list[dict],
    output_changes: list[dict],
    model_pairs: list[dict],
    env_changes: list[dict],
) -> str | None:
    for p in tool_pairs:
        if p.get("added"):
            return f"tool call added ({p.get('tool_name')})"
        if p.get("removed"):
            return f"tool call removed ({p.get('tool_name')})"
        if p.get("result_changed"):
            return f"tool call result changed ({p.get('tool_name')})"
    if output_changes:
        return f"output changed ({output_changes[0].get('path')})"
    for p in model_pairs:
        if p.get("request_changed"):
            return f"model request changed (span {p.get('span_id')})"
        if p.get("added") or p.get("removed"):
            return f"model call {'added' if p.get('added') else 'removed'} (span {p.get('span_id')})"
    if env_changes:
        return f"environment drift ({env_changes[0].get('field')})"
    return None
