from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

EVAL_PLATFORM_VERSION = "eval-platform-v1"
CASE_SCHEMA_VERSION = "eval-case-v1"
RESULT_SCHEMA_VERSION = "eval-result-v1"


class EvalStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class FailureCategory(StrEnum):
    INTENT_MISMATCH = "INTENT_MISMATCH"
    SOLUTION_LEAKAGE = "SOLUTION_LEAKAGE"
    REPETITION = "REPETITION"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    WRONG_CLASSIFICATION = "WRONG_CLASSIFICATION"
    WRONG_TRANSFER_TYPE = "WRONG_TRANSFER_TYPE"
    INVALID_STRUCTURE = "INVALID_STRUCTURE"
    MISSING_PROVENANCE = "MISSING_PROVENANCE"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    TIMEOUT = "TIMEOUT"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
    INVALID_CASE = "INVALID_CASE"
    METRIC_FAILURE = "METRIC_FAILURE"


@dataclass(frozen=True)
class EvalCheck:
    name: str
    passed: bool
    category: FailureCategory | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "category": self.category.value if self.category else None,
            "details": self.details,
        }


@dataclass(frozen=True)
class EvalFailure:
    category: FailureCategory
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"category": self.category.value, "message": self.message, "details": self.details}


@dataclass(frozen=True)
class EvalCaseEnvelope:
    case_id: str
    suite: str
    capability: str
    split: str = "development"
    tags: list[str] = field(default_factory=list)
    input: dict[str, Any] = field(default_factory=dict)
    expected: dict[str, Any] = field(default_factory=dict)
    forbidden: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    raw_case: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "suite": self.suite,
            "capability": self.capability,
            "split": self.split,
            "tags": self.tags,
            "input": self.input,
            "expected": self.expected,
            "forbidden": self.forbidden,
            "metadata": self.metadata,
            "provenance": self.provenance,
            "raw_case": self.raw_case,
        }


@dataclass(frozen=True)
class EvalCaseResult:
    case_id: str
    suite: str
    capability: str
    split: str
    status: EvalStatus
    metrics: dict[str, float] = field(default_factory=dict)
    checks: list[EvalCheck] = field(default_factory=list)
    failures: list[EvalFailure] = field(default_factory=list)
    latency_ms: float | None = None
    token_usage: dict[str, Any] | None = None
    model_calls: int | None = None
    tool_calls: int | None = None
    trace_id: str | None = None
    implementation_version: str | None = None
    eval_version: str = EVAL_PLATFORM_VERSION
    raw_result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "suite": self.suite,
            "capability": self.capability,
            "split": self.split,
            "status": self.status.value,
            "metrics": self.metrics,
            "checks": [check.to_dict() for check in self.checks],
            "failures": [failure.to_dict() for failure in self.failures],
            "latency_ms": self.latency_ms,
            "token_usage": self.token_usage,
            "model_calls": self.model_calls,
            "tool_calls": self.tool_calls,
            "trace_id": self.trace_id,
            "implementation_version": self.implementation_version,
            "eval_version": self.eval_version,
            "raw_result": self.raw_result,
        }


@dataclass(frozen=True)
class GateResult:
    metric: str
    operator: str
    threshold: float
    actual: float | None
    severity: str
    passed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "operator": self.operator,
            "threshold": self.threshold,
            "actual": self.actual,
            "severity": self.severity,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass(frozen=True)
class EvalSuiteResult:
    suite: str
    capability: str
    case_count: int
    passed: int
    failed: int
    errored: int
    skipped: int
    metrics: dict[str, Any]
    case_results: list[EvalCaseResult]
    gates: list[GateResult]
    baseline_metrics: dict[str, Any] = field(default_factory=dict)
    raw_legacy_result: dict[str, Any] = field(default_factory=dict)
    duration_ms: float | None = None

    def blocking_gate_failed(self) -> bool:
        return any(gate.severity == "blocking" and not gate.passed for gate in self.gates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "capability": self.capability,
            "case_count": self.case_count,
            "passed": self.passed,
            "failed": self.failed,
            "errored": self.errored,
            "skipped": self.skipped,
            "metrics": self.metrics,
            "gates": [gate.to_dict() for gate in self.gates],
            "baseline_metrics": self.baseline_metrics,
            "duration_ms": self.duration_ms,
            "raw_legacy_result": self.raw_legacy_result,
            "case_results": [case.to_dict() for case in self.case_results],
        }


@dataclass(frozen=True)
class EvalRunResult:
    run_id: str
    suites: list[EvalSuiteResult]
    artifact_dir: str | None
    eval_version: str = EVAL_PLATFORM_VERSION
    result_schema_version: str = RESULT_SCHEMA_VERSION
    started_at: str | None = None
    finished_at: str | None = None

    @property
    def exit_code(self) -> int:
        if any(suite.errored for suite in self.suites):
            return 2
        if any(suite.blocking_gate_failed() for suite in self.suites):
            return 1
        return 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "eval_version": self.eval_version,
            "result_schema_version": self.result_schema_version,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "artifact_dir": self.artifact_dir,
            "exit_code": self.exit_code,
            "suites": [suite.to_dict() for suite in self.suites],
            "summary": {
                "suite_count": len(self.suites),
                "case_count": sum(suite.case_count for suite in self.suites),
                "passed": sum(suite.passed for suite in self.suites),
                "failed": sum(suite.failed for suite in self.suites),
                "errored": sum(suite.errored for suite in self.suites),
                "skipped": sum(suite.skipped for suite in self.suites),
            },
        }
