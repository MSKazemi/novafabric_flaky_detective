"""API tests — exercise /analyze through the fixture aliases over HTTP (TestClient)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from flaky_detective.api import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_fixtures_listed() -> None:
    r = client.get("/fixtures")
    assert r.status_code == 200
    assert set(r.json()["fixtures"]) == {"fixture:baseline", "fixture:flaky", "fixture:regression"}


@pytest.mark.parametrize(
    ("current", "verdict"),
    [("fixture:baseline", "pass"), ("fixture:flaky", "flaky"), ("fixture:regression", "regression")],
)
def test_analyze_via_fixture_aliases(current: str, verdict: str) -> None:
    r = client.post(
        "/analyze",
        json={"baseline_capsule": "fixture:baseline", "current_capsule": current},
    )
    assert r.status_code == 200
    assert r.json()["verdict"] == verdict


def test_unknown_fixture_is_400() -> None:
    r = client.post(
        "/analyze",
        json={"baseline_capsule": "fixture:baseline", "current_capsule": "fixture:nope"},
    )
    assert r.status_code == 400
