"""Classifier tests against generated NovaFabric capsules (real DiffEngine, no LLM)."""
from __future__ import annotations

from pathlib import Path

import pytest

from flaky_detective.classifier import analyze
from flaky_detective.seed_scenarios import build_scenarios


@pytest.fixture(scope="module")
def scenarios(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return build_scenarios(tmp_path_factory.mktemp("capsules"))


def test_pass_identical(scenarios: dict[str, Path]) -> None:
    result = analyze(scenarios["baseline"], scenarios["baseline"])
    assert result.verdict == "pass"
    assert result.differing_step is None


def test_flaky_only_model_response_differs(scenarios: dict[str, Path]) -> None:
    result = analyze(scenarios["baseline"], scenarios["flaky"])
    assert result.verdict == "flaky"
    assert result.differing_step is not None
    assert "model call" in result.differing_step


def test_regression_tool_and_output_differ(scenarios: dict[str, Path]) -> None:
    result = analyze(scenarios["baseline"], scenarios["regression"])
    assert result.verdict == "regression"
    assert result.differing_step is not None
    assert "tool call" in result.differing_step


def test_signal_is_full_diff_report(scenarios: dict[str, Path]) -> None:
    result = analyze(scenarios["baseline"], scenarios["flaky"])
    assert "sections" in result.signal
    assert "model_calls" in result.signal["sections"]
