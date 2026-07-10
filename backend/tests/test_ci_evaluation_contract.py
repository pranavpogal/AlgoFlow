from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from app.evaluation.cli import main
from app.evaluation.core.baseline import (
    DEFAULT_ACCEPTED_BASELINE_PATH,
    BaselineValidationError,
    build_candidate_baseline,
    compare_run_to_baseline,
    load_accepted_baseline,
    validate_baseline,
    write_candidate_baseline,
)
from app.evaluation.core.runner import run_evaluations


def test_accepted_baseline_loads_and_validates() -> None:
    baseline = load_accepted_baseline(DEFAULT_ACCEPTED_BASELINE_PATH)

    assert baseline["baseline_id"] == "accepted-2026-07-06-deterministic-v1"
    assert baseline["contract_version"] == "ci-eval-contract-v1"
    assert baseline["suite_results"]["hinting"]["case_count"] == 5


def test_invalid_baseline_missing_required_field_is_rejected() -> None:
    baseline = load_accepted_baseline(DEFAULT_ACCEPTED_BASELINE_PATH)
    baseline.pop("suite_results")

    with pytest.raises(BaselineValidationError):
        validate_baseline(baseline)


def test_invalid_baseline_schema_version_is_rejected() -> None:
    baseline = load_accepted_baseline(DEFAULT_ACCEPTED_BASELINE_PATH)
    baseline["schema_version"] = "accepted-baseline-v0"

    with pytest.raises(BaselineValidationError):
        validate_baseline(baseline)


def test_comparison_passes_for_current_accepted_baseline() -> None:
    run = run_evaluations(suite="all")
    baseline = load_accepted_baseline(DEFAULT_ACCEPTED_BASELINE_PATH)

    comparison = compare_run_to_baseline(run, baseline)

    assert comparison.exit_code == 0
    assert comparison.status == "pass"
    assert comparison.blocking_regressions == []
    assert comparison.not_comparable == []


def test_higher_is_better_blocking_regression_is_detected() -> None:
    run = run_evaluations(suite="all")
    degraded = _replace_metric(run, "hinting", "pass_rate", 0.8)
    baseline = load_accepted_baseline(DEFAULT_ACCEPTED_BASELINE_PATH)

    comparison = compare_run_to_baseline(degraded, baseline)

    assert comparison.exit_code == 1
    assert any(delta.metric == "pass_rate" for delta in comparison.blocking_regressions)


def test_lower_is_better_blocking_regression_is_detected() -> None:
    run = run_evaluations(suite="all")
    degraded = _replace_metric(run, "pattern_transfer", "same_topic_shortcut_rate", 0.2)
    baseline = load_accepted_baseline(DEFAULT_ACCEPTED_BASELINE_PATH)

    comparison = compare_run_to_baseline(degraded, baseline)

    assert comparison.exit_code == 1
    assert any(delta.metric == "same_topic_shortcut_rate" for delta in comparison.blocking_regressions)


def test_warning_regression_does_not_fail_exit_code() -> None:
    run = run_evaluations(suite="all")
    degraded = _replace_metric(run, "code_review", "workflow_precision", 0.5)
    baseline = load_accepted_baseline(DEFAULT_ACCEPTED_BASELINE_PATH)

    comparison = compare_run_to_baseline(degraded, baseline)

    assert comparison.exit_code == 0
    assert comparison.blocking_regressions == []
    assert any(delta.metric == "workflow_precision" for delta in comparison.warnings)


def test_incompatible_metric_definition_is_not_comparable() -> None:
    run = run_evaluations(suite="all")
    baseline = load_accepted_baseline(DEFAULT_ACCEPTED_BASELINE_PATH)
    baseline["metric_definition_versions"]["pass_rate"] = "metric-definition-v0"

    comparison = compare_run_to_baseline(run, baseline)

    assert comparison.status == "not_comparable"
    assert any(delta.metric == "pass_rate" for delta in comparison.not_comparable)


def test_caseset_drift_detects_removed_case_id() -> None:
    run = run_evaluations(suite="all")
    baseline = load_accepted_baseline(DEFAULT_ACCEPTED_BASELINE_PATH)
    baseline["suite_results"]["hinting"]["case_ids"] = baseline["suite_results"]["hinting"]["case_ids"][:-1]
    baseline["suite_results"]["hinting"]["case_count"] = 4

    comparison = compare_run_to_baseline(run, baseline)
    drift = next(item for item in comparison.caseset_drift if item.suite == "hinting")

    assert drift.changed
    assert drift.added_case_ids


def test_candidate_baseline_generation_is_explicit_and_serializable(tmp_path: Path) -> None:
    run = run_evaluations(suite="hinting")
    candidate = build_candidate_baseline(run, baseline_id="candidate-test", notes="test candidate")
    output = tmp_path / "candidate.json"

    write_candidate_baseline(candidate, output)
    reloaded = json.loads(output.read_text())

    assert reloaded["baseline_id"] == "candidate-test"
    assert reloaded["suite_results"]["hinting"]["case_count"] == 5
    assert not (tmp_path / "current.json").exists()


def test_cli_invalid_baseline_is_infrastructure_failure(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}")

    assert main(["compare", "--baseline", str(invalid)]) == 2


def test_cli_compare_writes_comparison_artifact(tmp_path: Path) -> None:
    run = run_evaluations(suite="hinting")
    candidate = build_candidate_baseline(run, baseline_id="artifact-test")
    baseline_path = tmp_path / "baseline.json"
    write_candidate_baseline(candidate, baseline_path)

    exit_code = main(["compare", "--suite", "hinting", "--baseline", str(baseline_path), "--json"])

    assert exit_code == 0
    comparison_files = list(Path("../evals/artifacts").glob("*/baseline_comparison.json"))
    assert comparison_files


def _replace_metric(run, suite_name: str, metric: str, value: float):
    suites = []
    for suite in run.suites:
        if suite.suite != suite_name:
            suites.append(suite)
            continue
        metrics = copy.deepcopy(suite.metrics)
        metrics[metric] = value
        suites.append(replace(suite, metrics=metrics))
    return replace(run, suites=suites)
