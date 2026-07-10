from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from app.evaluation.core.metrics import METRIC_REGISTRY, MetricDefinition
from app.evaluation.core.models import EVAL_PLATFORM_VERSION, EvalRunResult

ACCEPTED_BASELINE_SCHEMA_VERSION = "accepted-baseline-v1"
CI_CONTRACT_VERSION = "ci-eval-contract-v1"
METRIC_DEFINITION_VERSION = "metric-definition-v1"
FAILURE_TAXONOMY_VERSION = "failure-taxonomy-v1"
DEFAULT_ACCEPTED_BASELINE_PATH = Path("../evals/baselines/accepted/current.json")

ComparisonStatus = Literal["pass", "fail", "not_comparable"]
RegressionSeverity = Literal["blocking", "warning", "informational"]


@dataclass(frozen=True)
class RegressionPolicy:
    suite: str
    metric: str
    max_regression: float
    severity: RegressionSeverity
    rationale: str


@dataclass(frozen=True)
class MetricDelta:
    suite: str
    metric: str
    baseline_value: float | None
    current_value: float | None
    delta: float | None
    direction: str | None
    severity: RegressionSeverity
    status: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class CasesetDrift:
    suite: str
    baseline_case_count: int | None
    current_case_count: int | None
    added_case_ids: list[str] = field(default_factory=list)
    removed_case_ids: list[str] = field(default_factory=list)
    split_count_changes: dict[str, dict[str, int | None]] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return bool(
            self.added_case_ids
            or self.removed_case_ids
            or self.split_count_changes
            or self.baseline_case_count != self.current_case_count
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "baseline_case_count": self.baseline_case_count,
            "current_case_count": self.current_case_count,
            "added_case_ids": self.added_case_ids,
            "removed_case_ids": self.removed_case_ids,
            "split_count_changes": self.split_count_changes,
            "changed": self.changed,
        }


@dataclass(frozen=True)
class BaselineComparison:
    baseline_id: str
    current_run_id: str
    contract_version: str
    status: ComparisonStatus
    metric_deltas: list[MetricDelta]
    caseset_drift: list[CasesetDrift]
    blocking_regressions: list[MetricDelta]
    warnings: list[MetricDelta]
    not_comparable: list[MetricDelta]
    infrastructure_failure: bool = False

    @property
    def exit_code(self) -> int:
        if self.infrastructure_failure:
            return 2
        if self.blocking_regressions:
            return 1
        return 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "current_run_id": self.current_run_id,
            "contract_version": self.contract_version,
            "status": self.status,
            "exit_code": self.exit_code,
            "metric_deltas": [delta.to_dict() for delta in self.metric_deltas],
            "caseset_drift": [drift.to_dict() for drift in self.caseset_drift],
            "blocking_regressions": [delta.to_dict() for delta in self.blocking_regressions],
            "warnings": [delta.to_dict() for delta in self.warnings],
            "not_comparable": [delta.to_dict() for delta in self.not_comparable],
            "infrastructure_failure": self.infrastructure_failure,
        }


RELATIVE_REGRESSION_POLICIES = [
    RegressionPolicy("hinting", "pass_rate", 0.0, "blocking", "deterministic hint cases should keep passing"),
    RegressionPolicy("hinting", "intervention_type_accuracy", 0.0, "blocking", "wrong hint intent is core behavior"),
    RegressionPolicy("hinting", "solution_leakage_rate", 0.0, "blocking", "solution leakage is safety critical"),
    RegressionPolicy("code_review", "pass_rate", 0.0, "blocking", "deterministic review cases should keep passing"),
    RegressionPolicy("code_review", "unsupported_claim_rate", 0.0, "blocking", "unsupported claims are safety critical"),
    RegressionPolicy("code_review", "rewrite_policy_compliance_rate", 0.0, "blocking", "rewrite boundaries must hold"),
    RegressionPolicy("code_review", "workflow_precision", 0.05, "warning", "small-data quality signal"),
    RegressionPolicy("problem_intelligence", "pass_rate", 0.0, "blocking", "deterministic classification cases should keep passing"),
    RegressionPolicy("problem_intelligence", "unsupported_claim_rate", 0.0, "blocking", "unsupported claims are safety critical"),
    RegressionPolicy("problem_intelligence", "primary_topic_accuracy", 0.05, "warning", "small-data quality signal"),
    RegressionPolicy("problem_intelligence", "pattern_precision", 0.05, "warning", "small-data quality signal"),
    RegressionPolicy("problem_intelligence", "pattern_recall", 0.05, "warning", "small-data quality signal"),
    RegressionPolicy("pattern_transfer", "pass_rate", 0.0, "blocking", "deterministic transfer cases should keep passing"),
    RegressionPolicy("pattern_transfer", "unsupported_claim_rate", 0.0, "blocking", "unsupported claims are safety critical"),
    RegressionPolicy("pattern_transfer", "same_topic_shortcut_rate", 0.0, "blocking", "shortcut behavior defeats transfer learning"),
    RegressionPolicy("pattern_transfer", "provenance_completeness", 0.0, "blocking", "transfer must remain evidence-grounded"),
    RegressionPolicy("pattern_transfer", "recommendation_relevance", 0.05, "warning", "small-data quality signal"),
    RegressionPolicy("pattern_transfer", "transfer_type_accuracy", 0.05, "warning", "small-data quality signal"),
]


class BaselineValidationError(ValueError):
    """Raised when an accepted baseline cannot be trusted for comparison."""


def load_accepted_baseline(path: str | Path = DEFAULT_ACCEPTED_BASELINE_PATH) -> dict[str, Any]:
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BaselineValidationError(f"Unable to read baseline at {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise BaselineValidationError(f"Invalid baseline JSON at {path}: {exc}") from exc
    validate_baseline(payload)
    return payload


def validate_baseline(payload: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "baseline_id",
        "contract_version",
        "created_at",
        "source_revision",
        "suite_results",
        "metric_definition_versions",
        "taxonomy_versions",
        "notes",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise BaselineValidationError(f"Baseline missing required fields: {', '.join(missing)}")
    if payload["schema_version"] != ACCEPTED_BASELINE_SCHEMA_VERSION:
        raise BaselineValidationError(f"Unsupported baseline schema: {payload['schema_version']}")
    if payload["contract_version"] != CI_CONTRACT_VERSION:
        raise BaselineValidationError(f"Unsupported contract version: {payload['contract_version']}")
    if not isinstance(payload["suite_results"], dict) or not payload["suite_results"]:
        raise BaselineValidationError("Baseline must include suite_results")
    for suite_name, suite in payload["suite_results"].items():
        _validate_suite_baseline(suite_name, suite)


def build_candidate_baseline(
    run: EvalRunResult,
    *,
    baseline_id: str | None = None,
    notes: str = "Candidate generated from deterministic unified eval run.",
) -> dict[str, Any]:
    created_at = datetime.now(UTC).isoformat()
    return {
        "schema_version": ACCEPTED_BASELINE_SCHEMA_VERSION,
        "baseline_id": baseline_id or f"candidate-{run.run_id}",
        "contract_version": CI_CONTRACT_VERSION,
        "created_at": created_at,
        "source_revision": _current_git_revision(),
        "eval_version": run.eval_version,
        "result_schema_version": run.result_schema_version,
        "suite_results": {
            suite.suite: {
                "capability": suite.capability,
                "case_count": suite.case_count,
                "passed": suite.passed,
                "failed": suite.failed,
                "errored": suite.errored,
                "skipped": suite.skipped,
                "case_ids": sorted(case.case_id for case in suite.case_results),
                "split_counts": _split_counts(suite),
                "metrics": _numeric_metrics(suite.metrics),
                "baseline_metrics": _numeric_metrics(suite.baseline_metrics),
            }
            for suite in run.suites
        },
        "metric_definition_versions": {
            metric_id: METRIC_DEFINITION_VERSION for metric_id in sorted(METRIC_REGISTRY)
        },
        "metric_definition_fingerprints": {
            metric_id: _metric_fingerprint(definition)
            for metric_id, definition in sorted(METRIC_REGISTRY.items())
        },
        "taxonomy_versions": {
            "failure_taxonomy": FAILURE_TAXONOMY_VERSION,
            "eval_platform": EVAL_PLATFORM_VERSION,
        },
        "notes": notes,
    }


def compare_run_to_baseline(run: EvalRunResult, baseline: dict[str, Any]) -> BaselineComparison:
    validate_baseline(baseline)
    metric_deltas: list[MetricDelta] = []
    caseset_drift: list[CasesetDrift] = []
    not_comparable: list[MetricDelta] = []
    warnings: list[MetricDelta] = []
    blocking: list[MetricDelta] = []

    current_suites = {suite.suite: suite for suite in run.suites}
    baseline_suites = baseline["suite_results"]
    for suite_name in sorted(set(current_suites) | set(baseline_suites)):
        current_suite = current_suites.get(suite_name)
        baseline_suite = baseline_suites.get(suite_name)
        if current_suite is None or baseline_suite is None:
            drift = CasesetDrift(
                suite=suite_name,
                baseline_case_count=baseline_suite.get("case_count") if baseline_suite else None,
                current_case_count=current_suite.case_count if current_suite else None,
            )
            caseset_drift.append(drift)
            continue
        caseset_drift.append(_compare_caseset(suite_name, baseline_suite, current_suite))

    for policy in RELATIVE_REGRESSION_POLICIES:
        delta = _compare_metric(run, baseline, policy)
        metric_deltas.append(delta)
        if delta.status == "not_comparable":
            not_comparable.append(delta)
        elif delta.status == "regressed" and delta.severity == "blocking":
            blocking.append(delta)
        elif delta.status == "regressed" and delta.severity == "warning":
            warnings.append(delta)

    status: ComparisonStatus = "pass"
    if not_comparable:
        status = "not_comparable"
    if blocking:
        status = "fail"
    return BaselineComparison(
        baseline_id=baseline["baseline_id"],
        current_run_id=run.run_id,
        contract_version=CI_CONTRACT_VERSION,
        status=status,
        metric_deltas=metric_deltas,
        caseset_drift=caseset_drift,
        blocking_regressions=blocking,
        warnings=warnings,
        not_comparable=not_comparable,
        infrastructure_failure=run.exit_code == 2,
    )


def write_candidate_baseline(payload: dict[str, Any], path: Path) -> None:
    validate_baseline(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def human_comparison_summary(comparison: BaselineComparison) -> str:
    drift_count = sum(1 for drift in comparison.caseset_drift if drift.changed)
    improved = sum(1 for delta in comparison.metric_deltas if delta.status == "improved")
    regressed = sum(1 for delta in comparison.metric_deltas if delta.status == "regressed")
    unchanged = sum(1 for delta in comparison.metric_deltas if delta.status == "unchanged")
    lines = [
        "AlgoFlow Evaluation Contract",
        "----------------------------",
        f"Baseline: {comparison.baseline_id}",
        f"Current run: {comparison.current_run_id}",
        f"Status: {comparison.status}",
        f"Exit: {comparison.exit_code}",
        "",
        "Accepted baseline comparison:",
        f"- improved: {improved}",
        f"- regressed: {regressed}",
        f"- unchanged: {unchanged}",
        f"- not comparable: {len(comparison.not_comparable)}",
        f"- caseset drift: {drift_count}",
        "",
        f"Blocking regressions: {len(comparison.blocking_regressions)}",
        f"Warnings: {len(comparison.warnings)}",
    ]
    for delta in comparison.blocking_regressions[:5]:
        lines.append(f"- BLOCKING {delta.suite}.{delta.metric}: {delta.message}")
    for delta in comparison.warnings[:5]:
        lines.append(f"- WARNING {delta.suite}.{delta.metric}: {delta.message}")
    return "\n".join(lines)


def _validate_suite_baseline(suite_name: str, suite: dict[str, Any]) -> None:
    required = {"case_count", "metrics", "case_ids", "split_counts"}
    missing = sorted(required - set(suite))
    if missing:
        raise BaselineValidationError(f"Suite {suite_name} missing fields: {', '.join(missing)}")
    if not isinstance(suite["case_count"], int) or suite["case_count"] < 0:
        raise BaselineValidationError(f"Suite {suite_name} has invalid case_count")
    if not isinstance(suite["metrics"], dict):
        raise BaselineValidationError(f"Suite {suite_name} metrics must be an object")
    if not isinstance(suite["case_ids"], list):
        raise BaselineValidationError(f"Suite {suite_name} case_ids must be a list")
    if len(suite["case_ids"]) != len(set(suite["case_ids"])):
        raise BaselineValidationError(f"Suite {suite_name} contains duplicate case IDs")


def _compare_metric(run: EvalRunResult, baseline: dict[str, Any], policy: RegressionPolicy) -> MetricDelta:
    suite = next((candidate for candidate in run.suites if candidate.suite == policy.suite), None)
    baseline_suite = baseline["suite_results"].get(policy.suite)
    definition = METRIC_REGISTRY.get(policy.metric)
    if suite is None or baseline_suite is None or definition is None:
        return _not_comparable(policy, "suite or metric is missing")
    if not _metric_definition_compatible(baseline, policy.metric, definition):
        return _not_comparable(policy, "metric definition changed")
    baseline_value = _as_number(baseline_suite.get("metrics", {}).get(policy.metric))
    current_value = _as_number(suite.metrics.get(policy.metric))
    if baseline_value is None or current_value is None:
        return _not_comparable(policy, "baseline or current metric missing")

    delta = round(current_value - baseline_value, 6)
    if _is_regression(delta, definition.direction, policy.max_regression):
        status = "regressed"
    elif _is_improvement(delta, definition.direction):
        status = "improved"
    else:
        status = "unchanged"
    message = (
        f"baseline={baseline_value}, current={current_value}, delta={delta}, "
        f"allowed_regression={policy.max_regression}; {policy.rationale}"
    )
    return MetricDelta(
        suite=policy.suite,
        metric=policy.metric,
        baseline_value=baseline_value,
        current_value=current_value,
        delta=delta,
        direction=definition.direction,
        severity=policy.severity,
        status=status,
        message=message,
    )


def _not_comparable(policy: RegressionPolicy, reason: str) -> MetricDelta:
    return MetricDelta(
        suite=policy.suite,
        metric=policy.metric,
        baseline_value=None,
        current_value=None,
        delta=None,
        direction=None,
        severity=policy.severity,
        status="not_comparable",
        message=reason,
    )


def _is_regression(delta: float, direction: str, max_regression: float) -> bool:
    if direction == "higher_is_better":
        return delta < -max_regression
    if direction == "lower_is_better":
        return delta > max_regression
    return False


def _is_improvement(delta: float, direction: str) -> bool:
    if direction == "higher_is_better":
        return delta > 0
    if direction == "lower_is_better":
        return delta < 0
    return False


def _compare_caseset(suite_name: str, baseline_suite: dict[str, Any], current_suite: Any) -> CasesetDrift:
    baseline_case_ids = set(baseline_suite.get("case_ids", []))
    current_case_ids = {case.case_id for case in current_suite.case_results}
    baseline_splits = baseline_suite.get("split_counts", {})
    current_splits = _split_counts(current_suite)
    split_count_changes = {}
    for split in sorted(set(baseline_splits) | set(current_splits)):
        baseline_count = baseline_splits.get(split)
        current_count = current_splits.get(split)
        if baseline_count != current_count:
            split_count_changes[split] = {"baseline": baseline_count, "current": current_count}
    return CasesetDrift(
        suite=suite_name,
        baseline_case_count=baseline_suite.get("case_count"),
        current_case_count=current_suite.case_count,
        added_case_ids=sorted(current_case_ids - baseline_case_ids),
        removed_case_ids=sorted(baseline_case_ids - current_case_ids),
        split_count_changes=split_count_changes,
    )


def _metric_definition_compatible(
    baseline: dict[str, Any], metric_id: str, definition: MetricDefinition
) -> bool:
    versions = baseline.get("metric_definition_versions", {})
    if versions.get(metric_id) != METRIC_DEFINITION_VERSION:
        return False
    fingerprints = baseline.get("metric_definition_fingerprints", {})
    expected = fingerprints.get(metric_id)
    return expected is None or expected == _metric_fingerprint(definition)


def _metric_fingerprint(definition: MetricDefinition) -> dict[str, str]:
    return {
        "formula": definition.formula,
        "valid_range": definition.valid_range,
        "direction": definition.direction,
        "aggregation": definition.aggregation,
        "missing_data": definition.missing_data,
    }


def _split_counts(suite: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in suite.case_results:
        counts[case.split] = counts.get(case.split, 0) + 1
    return dict(sorted(counts.items()))


def _numeric_metrics(metrics: dict[str, Any]) -> dict[str, float]:
    return {key: float(value) for key, value in sorted(metrics.items()) if isinstance(value, (int, float))}


def _as_number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _current_git_revision() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    revision = completed.stdout.strip()
    return revision or None
