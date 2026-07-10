from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

SEMANTIC_POLICY_VERSION = "semantic-tool-policy-v1"

SemanticDecisionValue = Literal["allow", "deny"]


class SemanticReasonCode(StrEnum):
    INTENT_TOOL_MISMATCH = "INTENT_TOOL_MISMATCH"
    CAPABILITY_TOOL_MISMATCH = "CAPABILITY_TOOL_MISMATCH"
    MENTORING_MODE_VIOLATION = "MENTORING_MODE_VIOLATION"
    SOLUTION_LEAKAGE_RISK = "SOLUTION_LEAKAGE_RISK"
    EXPLICIT_REVEAL_NOT_AUTHORIZED = "EXPLICIT_REVEAL_NOT_AUTHORIZED"
    PROMPT_INJECTION_SUSPECTED = "PROMPT_INJECTION_SUSPECTED"
    INSTRUCTION_OVERRIDE_ATTEMPT = "INSTRUCTION_OVERRIDE_ATTEMPT"
    TOOL_ARGUMENT_SEMANTIC_MISMATCH = "TOOL_ARGUMENT_SEMANTIC_MISMATCH"
    UNSUPPORTED_TASK = "UNSUPPORTED_TASK"
    CAPABILITY_DRIFT = "CAPABILITY_DRIFT"
    UNTRUSTED_CONTEXT_POLICY_OVERRIDE = "UNTRUSTED_CONTEXT_POLICY_OVERRIDE"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
    POLICY_CONTEXT_INVALID = "POLICY_CONTEXT_INVALID"
    INTENT_ALIGNED = "INTENT_ALIGNED"
    CAPABILITY_ALIGNED = "CAPABILITY_ALIGNED"
    EXPLICIT_REVEAL_AUTHORIZED = "EXPLICIT_REVEAL_AUTHORIZED"
    SAFE_READ_OPERATION = "SAFE_READ_OPERATION"
    BOUNDED_ANALYSIS_ALLOWED = "BOUNDED_ANALYSIS_ALLOWED"


class MentoringMode(StrEnum):
    HINT_ONLY = "HINT_ONLY"
    VALIDATE_APPROACH = "VALIDATE_APPROACH"
    EXPLAIN_CONCEPT = "EXPLAIN_CONCEPT"
    RECOMMEND_TRANSFER = "RECOMMEND_TRANSFER"
    EXPLICIT_SOLUTION = "EXPLICIT_SOLUTION"
    CODE_REVIEW = "CODE_REVIEW"


@dataclass(frozen=True)
class SemanticPolicyContext:
    principal_id: str | None
    caller_id: str
    requested_tool_id: str
    operation_type: str
    tool_arguments: dict[str, Any]
    selected_capability: str | None = None
    user_intent: str | None = None
    mentoring_mode: str | None = None
    reveal_authorized: bool = False
    request_id: str | None = None
    trace_id: str | None = None
    session_id: str | None = None
    trajectory_id: str | None = None
    prior_hint_context: dict[str, Any] = field(default_factory=dict)
    task_context: dict[str, Any] = field(default_factory=dict)
    trusted_context: dict[str, Any] = field(default_factory=dict)
    untrusted_user_content_present: bool = True


@dataclass(frozen=True)
class SemanticPolicyDecision:
    decision: SemanticDecisionValue
    reason_code: SemanticReasonCode
    reason: str
    policy_version: str = SEMANTIC_POLICY_VERSION
    constraints: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)
    injection_suspected: bool = False
    reveal_authorized: bool | None = None
    selected_capability: str | None = None
    user_intent: str | None = None
    mentoring_mode: str | None = None

    @property
    def policy_id(self) -> str:
        return f"semantic.{self.reason_code.value.lower()}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "policy_layer": "semantic",
            "reason_code": self.reason_code.value,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "constraints": self.constraints,
            "evidence": self.evidence,
            "provenance": self.provenance,
            "injection_suspected": self.injection_suspected,
            "reveal_authorized": self.reveal_authorized,
            "selected_capability": self.selected_capability,
            "user_intent": self.user_intent,
            "mentoring_mode": self.mentoring_mode,
        }


CAPABILITY_TOOL_ALLOWLIST = {
    "problem_analysis": {"problem.detect_pattern"},
    "next_hint": {"problem.detect_pattern"},
    "recommendations": {"problem.related_problems"},
    "recommendation": {"problem.related_problems"},
    "pattern_transfer": {"problem.related_problems"},
}

INTENT_TOOL_ALLOWLIST = {
    "PROBLEM_ANALYSIS": {"problem.detect_pattern"},
    "ONE_HINT": {"problem.detect_pattern"},
    "ANOTHER_HINT": {"problem.detect_pattern"},
    "NO_SOLUTION": {"problem.detect_pattern"},
    "IDEA_VALIDATION": {"problem.detect_pattern"},
    "WHY_STATE_WRONG": {"problem.detect_pattern"},
    "APPROACH_REVIEW": {"problem.detect_pattern"},
    "ALREADY_KNOWS_RECURRENCE": {"problem.detect_pattern"},
    "FULL_SOLUTION": {"problem.detect_pattern"},
    "RECOMMEND_TRANSFER": {"problem.related_problems"},
    "RECOMMENDATION": {"problem.related_problems"},
    "RELATED_PROBLEMS": {"problem.related_problems"},
}

MENTORING_MODE_TOOL_ALLOWLIST = {
    MentoringMode.HINT_ONLY.value: {"problem.detect_pattern"},
    MentoringMode.VALIDATE_APPROACH.value: {"problem.detect_pattern"},
    MentoringMode.EXPLAIN_CONCEPT.value: {"problem.detect_pattern"},
    MentoringMode.EXPLICIT_SOLUTION.value: {"problem.detect_pattern"},
    MentoringMode.RECOMMEND_TRANSFER.value: {"problem.related_problems"},
}

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "bypass policy",
    "bypass tool policy",
    "pretend i am an admin",
    "pretend to be admin",
    "call every available tool",
    "call all tools",
    "reveal hidden instructions",
    "override system policy",
    "change caller identity",
    "disable safety checks",
    "disable policy checks",
    "you are now",
]


def evaluate_semantic_policy(context: SemanticPolicyContext) -> SemanticPolicyDecision:
    injection_evidence = _injection_evidence(context)
    if _invalid_context(context):
        return _deny(
            context,
            SemanticReasonCode.POLICY_CONTEXT_INVALID,
            "Semantic policy context is missing required trusted runtime fields.",
            evidence=injection_evidence,
        )
    if injection_evidence and _attempts_policy_override(injection_evidence):
        return _deny(
            context,
            SemanticReasonCode.PROMPT_INJECTION_SUSPECTED,
            "Untrusted content contains instruction-override pressure relevant to tool execution.",
            evidence=injection_evidence,
            injection_suspected=True,
        )
    if not _capability_allows_tool(context):
        return _deny(
            context,
            SemanticReasonCode.CAPABILITY_TOOL_MISMATCH,
            "Requested tool is not compatible with the server-selected capability.",
            evidence=_alignment_evidence(context),
            injection_suspected=bool(injection_evidence),
        )
    if not _intent_allows_tool(context):
        return _deny(
            context,
            SemanticReasonCode.INTENT_TOOL_MISMATCH,
            "Requested tool is not justified by the derived user intent.",
            evidence=_alignment_evidence(context),
            injection_suspected=bool(injection_evidence),
        )
    if not _mentoring_mode_allows_tool(context):
        return _deny(
            context,
            SemanticReasonCode.MENTORING_MODE_VIOLATION,
            "Requested tool would drift outside the current mentoring mode.",
            evidence=_alignment_evidence(context),
            injection_suspected=bool(injection_evidence),
        )
    leakage_decision = _solution_leakage_decision(context, bool(injection_evidence))
    if leakage_decision:
        return leakage_decision
    if not _tool_arguments_match_task(context):
        return _deny(
            context,
            SemanticReasonCode.TOOL_ARGUMENT_SEMANTIC_MISMATCH,
            "Tool arguments do not match the trusted task context.",
            evidence=_argument_evidence(context),
            injection_suspected=bool(injection_evidence),
        )
    return SemanticPolicyDecision(
        decision="allow",
        reason_code=_allow_reason(context),
        reason="Tool call is aligned with capability, intent, mentoring mode, and task context.",
        evidence=_alignment_evidence(context) + injection_evidence,
        provenance=["semantic_policy.evaluate_semantic_policy", SEMANTIC_POLICY_VERSION],
        injection_suspected=bool(injection_evidence),
        reveal_authorized=context.reveal_authorized,
        selected_capability=context.selected_capability,
        user_intent=context.user_intent,
        mentoring_mode=context.mentoring_mode,
    )


def _invalid_context(context: SemanticPolicyContext) -> bool:
    return not (
        context.caller_id
        and context.requested_tool_id
        and context.operation_type
        and context.selected_capability
        and context.mentoring_mode
    )


def _capability_allows_tool(context: SemanticPolicyContext) -> bool:
    return context.requested_tool_id in CAPABILITY_TOOL_ALLOWLIST.get(context.selected_capability or "", set())


def _intent_allows_tool(context: SemanticPolicyContext) -> bool:
    if not context.user_intent:
        return False
    return context.requested_tool_id in INTENT_TOOL_ALLOWLIST.get(context.user_intent, set())


def _mentoring_mode_allows_tool(context: SemanticPolicyContext) -> bool:
    if not context.mentoring_mode:
        return False
    return context.requested_tool_id in MENTORING_MODE_TOOL_ALLOWLIST.get(context.mentoring_mode, set())


def _solution_leakage_decision(
    context: SemanticPolicyContext, injection_suspected: bool
) -> SemanticPolicyDecision | None:
    if context.mentoring_mode != MentoringMode.EXPLICIT_SOLUTION.value and context.user_intent == "FULL_SOLUTION":
        return _deny(
            context,
            SemanticReasonCode.EXPLICIT_REVEAL_NOT_AUTHORIZED,
            "Full-solution intent is present but explicit reveal is not authorized.",
            evidence=_alignment_evidence(context),
            injection_suspected=injection_suspected,
        )
    if context.mentoring_mode == MentoringMode.HINT_ONLY.value and context.requested_tool_id == "problem.related_problems":
        return _deny(
            context,
            SemanticReasonCode.SOLUTION_LEAKAGE_RISK,
            "Hint-only mode cannot drift into related-problem recommendation.",
            evidence=_alignment_evidence(context),
            injection_suspected=injection_suspected,
        )
    return None


def _tool_arguments_match_task(context: SemanticPolicyContext) -> bool:
    task_title = _normalize(context.task_context.get("title"))
    arg_title = _normalize(context.tool_arguments.get("title"))
    if context.requested_tool_id == "problem.detect_pattern":
        return bool(context.tool_arguments.get("description")) and (not task_title or task_title == arg_title)
    if context.requested_tool_id == "problem.related_problems":
        return bool(context.tool_arguments.get("pattern"))
    return False


def _allow_reason(context: SemanticPolicyContext) -> SemanticReasonCode:
    if context.user_intent == "FULL_SOLUTION" and context.reveal_authorized:
        return SemanticReasonCode.EXPLICIT_REVEAL_AUTHORIZED
    if context.requested_tool_id == "problem.detect_pattern":
        return SemanticReasonCode.BOUNDED_ANALYSIS_ALLOWED
    return SemanticReasonCode.INTENT_ALIGNED


def _injection_evidence(context: SemanticPolicyContext) -> list[dict[str, Any]]:
    haystacks = {
        "user_message": context.task_context.get("user_message", ""),
        "problem_title": context.task_context.get("title", ""),
        "problem_description": context.task_context.get("description", ""),
    }
    evidence = []
    for source, value in haystacks.items():
        text = str(value).lower()
        for pattern in INJECTION_PATTERNS:
            if pattern in text:
                evidence.append({"source": source, "pattern": pattern})
    return evidence


def _attempts_policy_override(evidence: list[dict[str, Any]]) -> bool:
    override_markers = {
        "bypass policy",
        "bypass tool policy",
        "pretend i am an admin",
        "pretend to be admin",
        "call every available tool",
        "call all tools",
        "reveal hidden instructions",
        "override system policy",
        "change caller identity",
        "disable safety checks",
        "disable policy checks",
        "ignore previous instructions",
        "ignore all previous instructions",
    }
    return any(item["pattern"] in override_markers for item in evidence)


def _deny(
    context: SemanticPolicyContext,
    reason_code: SemanticReasonCode,
    reason: str,
    *,
    evidence: list[dict[str, Any]],
    injection_suspected: bool = False,
) -> SemanticPolicyDecision:
    return SemanticPolicyDecision(
        decision="deny",
        reason_code=reason_code,
        reason=reason,
        evidence=evidence,
        provenance=["semantic_policy.evaluate_semantic_policy", SEMANTIC_POLICY_VERSION],
        injection_suspected=injection_suspected,
        reveal_authorized=context.reveal_authorized,
        selected_capability=context.selected_capability,
        user_intent=context.user_intent,
        mentoring_mode=context.mentoring_mode,
    )


def _alignment_evidence(context: SemanticPolicyContext) -> list[dict[str, Any]]:
    return [
        {
            "selected_capability": context.selected_capability,
            "user_intent": context.user_intent,
            "mentoring_mode": context.mentoring_mode,
            "requested_tool_id": context.requested_tool_id,
        }
    ]


def _argument_evidence(context: SemanticPolicyContext) -> list[dict[str, Any]]:
    return [
        {
            "task_title": context.task_context.get("title"),
            "argument_title": context.tool_arguments.get("title"),
            "tool_id": context.requested_tool_id,
        }
    ]


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())
