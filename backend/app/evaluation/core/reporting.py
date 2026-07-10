from __future__ import annotations

import json
from pathlib import Path

from app.evaluation.core.models import EvalRunResult


def write_artifacts(result: EvalRunResult, artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_dict()
    (artifact_dir / "summary.json").write_text(json.dumps(_summary_payload(payload), indent=2), encoding="utf-8")
    (artifact_dir / "cases.json").write_text(json.dumps(_cases_payload(payload), indent=2), encoding="utf-8")
    (artifact_dir / "failures.json").write_text(json.dumps(_failures_payload(payload), indent=2), encoding="utf-8")


def human_summary(result: EvalRunResult) -> str:
    lines = [
        f"Eval run: {result.run_id}",
        f"Suites: {len(result.suites)} | Cases: {sum(s.case_count for s in result.suites)} | Exit: {result.exit_code}",
    ]
    for suite in result.suites:
        gate_status = "PASS" if not suite.blocking_gate_failed() else "BLOCKING GATE FAILED"
        lines.append(
            f"- {suite.suite}: {suite.passed}/{suite.case_count} passed, "
            f"failed={suite.failed}, errored={suite.errored}, gates={gate_status}"
        )
        metric_text = ", ".join(f"{key}={value}" for key, value in suite.metrics.items() if isinstance(value, (int, float)))
        if metric_text:
            lines.append(f"  metrics: {metric_text}")
        failed_cases = [case.case_id for case in suite.case_results if case.failures][:5]
        if failed_cases:
            lines.append(f"  top failures: {', '.join(failed_cases)}")
    if result.artifact_dir:
        lines.append(f"Artifacts: {result.artifact_dir}")
    return "\n".join(lines)


def _summary_payload(payload: dict) -> dict:
    return {
        key: payload[key]
        for key in ["run_id", "eval_version", "result_schema_version", "started_at", "finished_at", "artifact_dir", "exit_code", "summary"]
    } | {
        "suites": [
            {key: suite[key] for key in ["suite", "capability", "case_count", "passed", "failed", "errored", "skipped", "metrics", "gates", "baseline_metrics", "duration_ms"]}
            for suite in payload["suites"]
        ]
    }


def _cases_payload(payload: dict) -> list[dict]:
    return [case for suite in payload["suites"] for case in suite["case_results"]]


def _failures_payload(payload: dict) -> list[dict]:
    failures = []
    for suite in payload["suites"]:
        for case in suite["case_results"]:
            if case["failures"]:
                failures.append({"suite": suite["suite"], "case_id": case["case_id"], "failures": case["failures"]})
    return failures
