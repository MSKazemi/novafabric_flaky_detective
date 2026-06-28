"""FastAPI wrapper — the tool the UiPath Agent Builder agent calls.

Run locally:   uvicorn flaky_detective.api:app --reload --port 8000
Then POST to:  /analyze   with two capsule directory paths, OR `fixture:` aliases.

For the UiPath demo, expose this over a public URL (Cloud Run / Render / a tunnel) and add it as a
tool in Agent Builder via a custom Integration Service connector built from this app's
`/openapi.json`. See docs/BUILD-PLAN.md §5b.

`fixture:` aliases (`fixture:baseline`, `fixture:flaky`, `fixture:regression`) resolve to capsules
generated in-process, so the cloud agent never needs access to a shared filesystem — it just sends
two aliases and gets a real NovaFabric diff verdict. This is what makes the demo recordable.
"""
from __future__ import annotations

import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from flaky_detective.classifier import analyze
from flaky_detective.seed_scenarios import build_scenarios

app = FastAPI(
    title="NovaFabric Flaky Detective",
    description="Classify an AI-agent test run as pass / flaky / regression by diffing NovaFabric capsules.",
    version="0.1.0",
)

_FIXTURE_PREFIX = "fixture:"


@lru_cache(maxsize=1)
def _fixtures() -> dict[str, Path]:
    """Generate the demo capsules once, in a temp dir, and cache the {alias: path} map."""
    return build_scenarios(Path(tempfile.mkdtemp(prefix="flaky-fixtures-")))


def _resolve(capsule: str) -> Path:
    if capsule.startswith(_FIXTURE_PREFIX):
        name = capsule[len(_FIXTURE_PREFIX):]
        fixtures = _fixtures()
        if name not in fixtures:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown fixture '{name}'. Available: {sorted(fixtures)}",
            )
        return fixtures[name]
    path = Path(capsule)
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Capsule not found: {path}")
    return path


class AnalyzeRequest(BaseModel):
    baseline_capsule: str = Field(
        ..., description="Baseline capsule dir path, or a 'fixture:<name>' alias."
    )
    current_capsule: str = Field(
        ..., description="Current run's capsule dir path, or a 'fixture:<name>' alias."
    )


class AnalyzeResponse(BaseModel):
    verdict: str  # pass | flaky | regression
    confidence: float
    differing_step: str | None
    remediation: str
    signal: dict


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "flaky-detective"}


@app.get("/fixtures")
def fixtures() -> dict:
    """List the built-in demo aliases usable as capsule paths."""
    return {"fixtures": [f"{_FIXTURE_PREFIX}{name}" for name in sorted(_fixtures())]}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_runs(req: AnalyzeRequest) -> AnalyzeResponse:
    base = _resolve(req.baseline_capsule)
    curr = _resolve(req.current_capsule)
    result = analyze(base, curr)
    return AnalyzeResponse(
        verdict=result.verdict,
        confidence=result.confidence,
        differing_step=result.differing_step,
        remediation=result.remediation,
        signal=result.signal,
    )
