from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from app.core.auth import Principal
from app.core.policy import PolicyDecision
from app.core.request_context import get_request_context
from app.core.semantic_policy import SemanticPolicyContext, SemanticPolicyDecision, evaluate_semantic_policy
from app.runtime.trajectory import Trajectory, TrajectoryEventType
from app.skills.code_review.workflow import CodeReviewContext, review_code_workflow
from app.tools.problem_intelligence import detect_problem_pattern, recommend_related_problems

ToolRisk = Literal["low", "medium", "high"]
ToolOperation = Literal["read", "draft", "act"]


class ToolGatewayError(ValueError):
    """Raised when a tool call is denied or invalid."""

    def __init__(self, message: str, record: ToolCallRecord | None = None) -> None:
        super().__init__(message)
        self.record = record


class ProblemPatternInput(BaseModel):
    title: str
    description: str


class RelatedProblemsInput(BaseModel):
    pattern: str


class CodeReviewToolInput(BaseModel):
    title: str
    language: str
    code: str
    problem_description: str | None = None
    user_intent: str | None = None


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    description: str
    operation: ToolOperation
    risk: ToolRisk
    input_model: type[BaseModel]
    output_type: type | tuple[type, ...]
    handler: Callable[..., Any]
    allowed_callers: set[str] = field(default_factory=set)
    timeout_ms: int = 1000


@dataclass(frozen=True)
class ToolCallRecord:
    tool_id: str
    caller: str
    operation: ToolOperation
    risk: ToolRisk
    decision: PolicyDecision
    semantic_decision: SemanticPolicyDecision | None = None
    latency_ms: float | None = None
    success: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "caller": self.caller,
            "operation": self.operation,
            "risk": self.risk,
            "decision": {
                "decision": self.decision.decision,
                "policy_id": self.decision.policy_id,
                "reason": self.decision.reason,
                "risk": self.decision.risk,
                "request_id": self.decision.request_id,
            },
            "semantic_decision": self.semantic_decision.to_dict() if self.semantic_decision else None,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error": self.error,
        }


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "problem.detect_pattern": ToolSpec(
        tool_id="problem.detect_pattern",
        description="Classify a problem into topic/pattern metadata.",
        operation="read",
        risk="low",
        input_model=ProblemPatternInput,
        output_type=dict,
        handler=lambda payload: detect_problem_pattern(payload.title, payload.description),
        allowed_callers={"adk_narrow_coordinator", "mentor_service"},
    ),
    "problem.related_problems": ToolSpec(
        tool_id="problem.related_problems",
        description="Return curated related problems for a pattern label.",
        operation="draft",
        risk="low",
        input_model=RelatedProblemsInput,
        output_type=list,
        handler=lambda payload: recommend_related_problems(payload.pattern),
        allowed_callers={"adk_narrow_coordinator", "mentor_service"},
    ),
    "code.review_static": ToolSpec(
        tool_id="code.review_static",
        description="Return deterministic static code-review feedback without executing learner code.",
        operation="draft",
        risk="medium",
        input_model=CodeReviewToolInput,
        output_type=dict,
        handler=lambda payload: _review_code_static(payload),
        allowed_callers={"adk_narrow_coordinator", "mentor_service"},
    ),
}


def _review_code_static(payload: CodeReviewToolInput) -> dict[str, Any]:
    result = review_code_workflow(
        CodeReviewContext(
            title=payload.title,
            language=payload.language,
            code=payload.code,
            problem_description=payload.problem_description,
            user_intent=payload.user_intent,
        )
    )
    return {
        "correctness": result.correctness,
        "time_complexity": result.time_complexity,
        "space_complexity": result.space_complexity,
        "edge_cases": result.edge_cases,
        "optimization_opportunities": result.optimization_opportunities,
        "readability_feedback": result.readability_feedback,
        "alternative_approaches": result.alternative_approaches,
        "suspected_mistakes": result.suspected_mistakes,
        "senior_engineer_summary": result.senior_engineer_summary,
        "review_intent": result.intent.value,
        "language_supported": result.language_supported,
        "analysis_layers": result.analysis_layers,
        "findings": [finding.to_dict() for finding in result.findings],
        "corrected_code": result.corrected_code,
        "rewrite_allowed": result.rewrite_allowed,
        "unsupported_claims": result.unsupported_claims,
    }


class ToolGateway:
    def __init__(self, registry: dict[str, ToolSpec] | None = None) -> None:
        self.registry = registry or TOOL_REGISTRY

    def call(
        self,
        tool_id: str,
        payload: dict[str, Any],
        *,
        caller: str,
        principal: Principal | None = None,
        trajectory: Trajectory | None = None,
        semantic_context: SemanticPolicyContext | None = None,
    ) -> tuple[Any, ToolCallRecord]:
        spec = self._spec(tool_id)
        decision = self._authorize(spec, caller=caller, principal=principal)
        self._record_structural_policy(trajectory, spec, caller, decision)
        if decision.decision == "deny":
            record = ToolCallRecord(
                tool_id=tool_id,
                caller=caller,
                operation=spec.operation,
                risk=spec.risk,
                decision=decision,
                success=False,
                error=decision.reason,
            )
            self._record_trajectory(trajectory, record)
            raise ToolGatewayError(decision.reason, record=record)

        start = perf_counter()
        try:
            parsed = spec.input_model.model_validate(payload)
            semantic_decision = evaluate_semantic_policy(
                semantic_context
                or SemanticPolicyContext(
                    principal_id=principal.user_id if principal else None,
                    caller_id=caller,
                    requested_tool_id=tool_id,
                    operation_type=spec.operation,
                    tool_arguments=payload,
                )
            )
            self._record_semantic_policy(trajectory, spec, semantic_decision)
            if semantic_decision.decision == "deny":
                record = ToolCallRecord(
                    tool_id=tool_id,
                    caller=caller,
                    operation=spec.operation,
                    risk=spec.risk,
                    decision=decision,
                    semantic_decision=semantic_decision,
                    latency_ms=round((perf_counter() - start) * 1000, 2),
                    success=False,
                    error=semantic_decision.reason_code.value,
                )
                self._record_trajectory(trajectory, record)
                raise ToolGatewayError(semantic_decision.reason, record=record)
            result = spec.handler(parsed)
            if not isinstance(result, spec.output_type):
                raise ToolGatewayError(f"Tool {tool_id} returned invalid output type.")
        except (ValidationError, ToolGatewayError) as exc:
            if isinstance(exc, ToolGatewayError) and exc.record is not None:
                raise
            latency = round((perf_counter() - start) * 1000, 2)
            record = ToolCallRecord(
                tool_id=tool_id,
                caller=caller,
                operation=spec.operation,
                risk=spec.risk,
                decision=decision,
                semantic_decision=locals().get("semantic_decision"),
                latency_ms=latency,
                success=False,
                error=type(exc).__name__,
            )
            self._record_trajectory(trajectory, record)
            raise

        latency = round((perf_counter() - start) * 1000, 2)
        record = ToolCallRecord(
            tool_id=tool_id,
            caller=caller,
            operation=spec.operation,
            risk=spec.risk,
            decision=decision,
            semantic_decision=semantic_decision,
            latency_ms=latency,
            success=True,
        )
        self._record_trajectory(trajectory, record)
        return result, record

    def _spec(self, tool_id: str) -> ToolSpec:
        if tool_id not in self.registry:
            raise ToolGatewayError(f"Unknown tool: {tool_id}")
        return self.registry[tool_id]

    def _authorize(
        self, spec: ToolSpec, *, caller: str, principal: Principal | None
    ) -> PolicyDecision:
        context = get_request_context()
        if caller not in spec.allowed_callers:
            return PolicyDecision(
                decision="deny",
                policy_id="tool.caller.denied",
                reason=f"Caller {caller} is not allowed to use {spec.tool_id}.",
                risk="high",
                request_id=context.request_id if context else None,
            )
        if spec.operation == "act":
            return PolicyDecision(
                decision="deny",
                policy_id="tool.act.denied_without_explicit_policy",
                reason="Act tools require explicit operation-specific policy.",
                risk="high",
                request_id=context.request_id if context else None,
            )
        return PolicyDecision(
            decision="allow",
            policy_id=f"tool.{spec.operation}.allowed",
            reason="Tool operation is read/draft and caller is allowlisted.",
            risk=spec.risk,
            request_id=context.request_id if context else None,
        )

    def _record_trajectory(self, trajectory: Trajectory | None, record: ToolCallRecord) -> None:
        if trajectory is None:
            return
        trajectory.add(
            TrajectoryEventType.TOOL_CALL_COMPLETED if record.success else TrajectoryEventType.TOOL_CALL_DENIED,
            "Tool gateway call completed." if record.success else "Tool gateway call denied or failed.",
            tool_name=record.tool_id,
            latency_ms=record.latency_ms,
            metadata=record.to_dict(),
        )

    def _record_structural_policy(
        self, trajectory: Trajectory | None, spec: ToolSpec, caller: str, decision: PolicyDecision
    ) -> None:
        if trajectory is None:
            return
        trajectory.add(
            TrajectoryEventType.STRUCTURAL_POLICY_EVALUATED,
            "Structural tool policy evaluated.",
            tool_name=spec.tool_id,
            metadata={
                "tool_id": spec.tool_id,
                "caller": caller,
                "operation": spec.operation,
                "risk": spec.risk,
                "decision": decision.decision,
                "policy_id": decision.policy_id,
            },
        )

    def _record_semantic_policy(
        self, trajectory: Trajectory | None, spec: ToolSpec, decision: SemanticPolicyDecision
    ) -> None:
        if trajectory is None:
            return
        trajectory.add(
            TrajectoryEventType.SEMANTIC_POLICY_EVALUATED,
            "Semantic tool policy evaluated.",
            tool_name=spec.tool_id,
            metadata=decision.to_dict(),
        )


tool_gateway = ToolGateway()
