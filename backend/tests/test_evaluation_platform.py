from __future__ import annotations

import json

from app.evaluation.cli import main
from app.evaluation.core.metrics import metric_catalog
from app.evaluation.core.runner import run_evaluations
from app.evaluation.core.thresholds import evaluate_gates


def test_unified_runner_preserves_existing_suite_counts() -> None:
    result = run_evaluations(suite="all")

    assert result.exit_code == 0
    assert result.to_dict()["summary"] == {
        "suite_count": 4,
        "case_count": 66,
        "passed": 66,
        "failed": 0,
        "errored": 0,
        "skipped": 0,
    }
    assert {suite.suite: suite.case_count for suite in result.suites} == {
        "code_review": 16,
        "hinting": 5,
        "pattern_transfer": 15,
        "problem_intelligence": 30,
    }


def test_adk_routing_suite_is_explicit_and_gated() -> None:
    result = run_evaluations(suite="adk_routing")

    assert result.exit_code == 0
    assert len(result.suites) == 1
    suite = result.suites[0]
    assert suite.case_count == 6
    assert suite.passed == 6
    assert suite.metrics["routing_accuracy"] == 1.0
    assert suite.metrics["trajectory_event_coverage"] == 1.0
    assert suite.metrics["trajectory_identity_completeness"] == 1.0
    assert all(gate.passed for gate in suite.gates)


def test_split_filter_limits_pattern_transfer_cases() -> None:
    result = run_evaluations(suite="pattern_transfer", split="adversarial")

    assert result.exit_code == 0
    assert len(result.suites) == 1
    suite = result.suites[0]
    assert suite.case_count == 4
    assert suite.passed == 4
    assert suite.metrics["case_count"] == 4
    assert {case.split for case in suite.case_results} == {"adversarial"}


def test_gate_policy_blocks_bad_metrics() -> None:
    gates = evaluate_gates(
        "hinting",
        {
            "solution_leakage_rate": 0.2,
            "intervention_type_accuracy": 1.0,
        },
    )

    assert any(not gate.passed and gate.severity == "blocking" for gate in gates)
    assert gates[0].metric == "solution_leakage_rate"


def test_metric_catalog_documents_platform_metrics() -> None:
    catalog = {entry["metric_id"] for entry in metric_catalog()}

    assert "unsupported_claim_rate" in catalog
    assert "same_topic_shortcut_rate" in catalog
    assert "solution_leakage_rate" in catalog


def test_artifact_writer_outputs_machine_readable_files(tmp_path) -> None:
    result = run_evaluations(suite="hinting", write_json=True, artifact_root=tmp_path)

    assert result.exit_code == 0
    assert result.artifact_dir is not None
    artifact_dir = tmp_path / result.run_id
    assert (artifact_dir / "summary.json").exists()
    assert (artifact_dir / "cases.json").exists()
    assert (artifact_dir / "failures.json").exists()

    summary = json.loads((artifact_dir / "summary.json").read_text())
    cases = json.loads((artifact_dir / "cases.json").read_text())
    failures = json.loads((artifact_dir / "failures.json").read_text())

    assert summary["summary"]["case_count"] == 5
    assert len(cases) == 5
    assert failures == []


def test_cli_unknown_suite_is_infrastructure_failure() -> None:
    assert main(["run", "--suite", "not_a_suite"]) == 2
