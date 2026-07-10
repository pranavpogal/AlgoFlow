from __future__ import annotations

from app.evaluation.adapters.adk_routing import AdkRoutingEvalAdapter
from app.evaluation.adapters.adk_tool_orchestration import AdkToolOrchestrationEvalAdapter
from app.evaluation.adapters.adk_live_runtime import AdkLiveRuntimeEvalAdapter
from app.evaluation.adapters.base import EvalAdapter
from app.evaluation.adapters.code_review import CodeReviewEvalAdapter
from app.evaluation.adapters.hinting import HintingEvalAdapter
from app.evaluation.adapters.pattern_transfer import PatternTransferEvalAdapter
from app.evaluation.adapters.problem_intelligence import ProblemIntelligenceEvalAdapter
from app.evaluation.adapters.semantic_tool_policy import SemanticToolPolicyEvalAdapter

DEFAULT_CI_SUITES = ["code_review", "hinting", "pattern_transfer", "problem_intelligence"]

_ADAPTERS: dict[str, EvalAdapter] = {
    "adk_live_runtime": AdkLiveRuntimeEvalAdapter(),
    "adk_routing": AdkRoutingEvalAdapter(),
    "adk_tool_orchestration": AdkToolOrchestrationEvalAdapter(),
    "hinting": HintingEvalAdapter(),
    "code_review": CodeReviewEvalAdapter(),
    "problem_intelligence": ProblemIntelligenceEvalAdapter(),
    "pattern_transfer": PatternTransferEvalAdapter(),
    "semantic_tool_policy": SemanticToolPolicyEvalAdapter(),
}

ALIASES = {
    "all": "all",
    "hints": "hinting",
    "hint_leakage": "hinting",
    "classification": "problem_intelligence",
    "problem_classification": "problem_intelligence",
    "transfer": "pattern_transfer",
    "routing": "adk_routing",
    "trajectory": "adk_routing",
    "live_adk": "adk_live_runtime",
    "adk_live": "adk_live_runtime",
    "tool_orchestration": "adk_tool_orchestration",
    "adk_tools": "adk_tool_orchestration",
    "semantic_policy": "semantic_tool_policy",
    "tool_policy": "semantic_tool_policy",
}


def suite_names() -> list[str]:
    return sorted(_ADAPTERS)


def resolve_suite(name: str) -> str:
    return ALIASES.get(name, name)


def get_adapter(name: str) -> EvalAdapter:
    suite = resolve_suite(name)
    if suite not in _ADAPTERS:
        available = ", ".join(suite_names())
        raise KeyError(f"Unknown eval suite '{name}'. Available suites: {available}")
    return _ADAPTERS[suite]


def selected_adapters(suite: str) -> list[EvalAdapter]:
    resolved = resolve_suite(suite)
    if resolved == "all":
        return [_ADAPTERS[name] for name in DEFAULT_CI_SUITES]
    return [get_adapter(resolved)]
