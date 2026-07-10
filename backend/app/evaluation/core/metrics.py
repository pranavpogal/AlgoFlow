from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Direction = Literal["higher_is_better", "lower_is_better", "informational"]


@dataclass(frozen=True)
class MetricDefinition:
    metric_id: str
    name: str
    capability: str
    formula: str
    valid_range: str
    direction: Direction
    aggregation: str
    missing_data: str
    threshold_semantics: str
    limitations: str

    def to_dict(self) -> dict[str, str]:
        return self.__dict__.copy()


METRIC_REGISTRY = {
    "pass_rate": MetricDefinition("pass_rate", "Pass Rate", "shared", "passed / case_count", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "suite-specific gates", "Does not explain failure quality."),
    "solution_leakage_rate": MetricDefinition("solution_leakage_rate", "Solution Leakage Rate", "hinting", "leakage failures / case_count", "0.0 to 1.0", "lower_is_better", "suite", "0 when no cases", "blocking when above threshold", "Marker-based leakage check is incomplete."),
    "intervention_type_accuracy": MetricDefinition("intervention_type_accuracy", "Intervention Type Accuracy", "hinting", "matching interventions / case_count", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "warning/blocking gates", "Does not measure helpfulness."),
    "workflow_precision": MetricDefinition("workflow_precision", "Workflow Finding Precision", "code_review", "coarse true positives / predicted findings", "0.0 to 1.0", "higher_is_better", "suite", "0 when no predictions", "warning gates", "Coarse labels; not full recall."),
    "legacy_precision": MetricDefinition("legacy_precision", "Legacy Finding Precision", "code_review", "legacy coarse true positives / predictions", "0.0 to 1.0", "higher_is_better", "suite", "0 when no predictions", "baseline only", "Approximate baseline."),
    "unsupported_claim_rate": MetricDefinition("unsupported_claim_rate", "Unsupported Claim Rate", "shared", "unsupported claim failures / case_count", "0.0 to 1.0", "lower_is_better", "suite", "0 when no cases", "blocking/warning depending suite", "Depends on suite labeling policy."),
    "structured_output_validity_rate": MetricDefinition("structured_output_validity_rate", "Structured Output Validity", "shared", "structured outputs / case_count", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "blocking when below threshold", "Only validates expected shape."),
    "rewrite_policy_compliance_rate": MetricDefinition("rewrite_policy_compliance_rate", "Rewrite Policy Compliance", "code_review", "rewrite policy successes / case_count", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "blocking when below threshold", "Only checks explicit fixture expectations."),
    "primary_topic_accuracy": MetricDefinition("primary_topic_accuracy", "Primary Topic Accuracy", "problem_intelligence", "correct primary topics / case_count", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "warning/blocking gates", "Small fixture set."),
    "pattern_precision": MetricDefinition("pattern_precision", "Pattern Precision", "problem_intelligence", "correct primary patterns / case_count", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "warning gates", "Single-label approximation."),
    "pattern_recall": MetricDefinition("pattern_recall", "Pattern Recall", "problem_intelligence", "correct primary patterns / expected patterns", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "warning gates", "Single-label approximation."),
    "multi_label_precision": MetricDefinition("multi_label_precision", "Multi-label Precision", "problem_intelligence", "secondary label hits / predicted secondary labels", "0.0 to 1.0", "higher_is_better", "suite", "0 when no predictions", "informational", "Current secondary labels preserve uncertainty."),
    "multi_label_recall": MetricDefinition("multi_label_recall", "Multi-label Recall", "problem_intelligence", "secondary label hits / expected secondary labels", "0.0 to 1.0", "higher_is_better", "suite", "1 when no expected labels", "informational", "Small multi-label set."),
    "provenance_completeness": MetricDefinition("provenance_completeness", "Provenance Completeness", "shared", "outputs with provenance / case_count", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "blocking/warning gates", "Checks presence, not quality."),
    "recommendation_relevance": MetricDefinition("recommendation_relevance", "Recommendation Relevance", "pattern_transfer", "target-ok cases / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "warning gates", "Fixture-specific target expectations."),
    "transfer_type_accuracy": MetricDefinition("transfer_type_accuracy", "Transfer Type Accuracy", "pattern_transfer", "correct transfer type / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "warning gates", "Small taxonomy fixture set."),
    "structural_bridge_correctness": MetricDefinition("structural_bridge_correctness", "Structural Bridge Correctness", "pattern_transfer", "bridge marker successes / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "warning gates", "Marker-based structural check."),
    "same_topic_shortcut_rate": MetricDefinition("same_topic_shortcut_rate", "Same-topic Shortcut Rate", "pattern_transfer", "same-topic shortcut cases / case_count", "0.0 to 1.0", "lower_is_better", "suite", "0 when no cases", "blocking when above threshold", "Depends on workflow flag."),
    "routing_accuracy": MetricDefinition("routing_accuracy", "ADK Routing Accuracy", "adk_routing", "correct routing decisions / case_count", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "blocking when below threshold", "Small deterministic routing fixture set."),
    "trajectory_event_coverage": MetricDefinition("trajectory_event_coverage", "Trajectory Event Coverage", "adk_routing", "cases with required trajectory events / case_count", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "blocking when below threshold", "Checks required event presence, not full trace quality."),
    "trajectory_identity_completeness": MetricDefinition("trajectory_identity_completeness", "Trajectory Identity Completeness", "adk_routing", "cases with trajectory ID, session ID, and schema version / case_count", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "blocking when below threshold", "Checks trace handles, not persistence."),
    "fallback_policy_accuracy": MetricDefinition("fallback_policy_accuracy", "Fallback Policy Accuracy", "adk_routing", "cases with expected fallback behavior / case_count", "0.0 to 1.0", "higher_is_better", "suite", "0 when no cases", "blocking when below threshold", "Current suite expects deterministic fallback because live ADK is disabled."),
    "live_boundary_accuracy": MetricDefinition("live_boundary_accuracy", "Live ADK Boundary Accuracy", "adk_live_runtime", "live boundary cases passing runtime/event expectations / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "blocking in explicit suite", "Uses bounded mock live invokers in CI; does not call Gemini."),
    "live_fallback_accuracy": MetricDefinition("live_fallback_accuracy", "Live ADK Fallback Accuracy", "adk_live_runtime", "live fallback cases passing fallback expectations / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "blocking in explicit suite", "Checks fallback behavior around live boundary failures."),
    "deterministic_parity_accuracy": MetricDefinition("deterministic_parity_accuracy", "Deterministic Parity Accuracy", "adk_live_runtime", "live/disabled cases matching expected deterministic route / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "blocking in explicit suite", "Compares route contract, not full model quality."),
    "tool_request_execution_accuracy": MetricDefinition("tool_request_execution_accuracy", "ADK Tool Request Execution Accuracy", "adk_tool_orchestration", "cases with expected allowed tool completions / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "blocking in explicit suite", "Checks narrow policy-gated tool requests, not broad tool autonomy."),
    "tool_policy_enforcement_accuracy": MetricDefinition("tool_policy_enforcement_accuracy", "ADK Tool Policy Enforcement Accuracy", "adk_tool_orchestration", "cases with expected denied tool requests and reason codes / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "blocking in explicit suite", "Depends on deterministic semantic policy fixtures."),
    "tool_trajectory_coverage": MetricDefinition("tool_trajectory_coverage", "ADK Tool Trajectory Coverage", "adk_tool_orchestration", "cases with required ADK tool request and gateway events / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "blocking in explicit suite", "Checks event presence, not full trace quality."),
    "tool_fallback_non_bypass_accuracy": MetricDefinition("tool_fallback_non_bypass_accuracy", "ADK Tool Fallback Non-Bypass Accuracy", "adk_tool_orchestration", "denied tool-request cases without prohibited completion / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "blocking in explicit suite", "Verifies denied requests do not silently execute through fallback."),
    "semantic_policy_accuracy": MetricDefinition("semantic_policy_accuracy", "Semantic Policy Accuracy", "semantic_tool_policy", "correct semantic policy outcomes / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "blocking in explicit suite", "Deterministic fixture coverage, not full semantic understanding."),
    "safe_allow_accuracy": MetricDefinition("safe_allow_accuracy", "Safe Allow Accuracy", "semantic_tool_policy", "safe allow cases passed / safe allow cases", "0.0 to 1.0", "higher_is_better", "suite/split", "1 when no cases", "warning/manual", "Small fixture set."),
    "unsafe_deny_accuracy": MetricDefinition("unsafe_deny_accuracy", "Unsafe Deny Accuracy", "semantic_tool_policy", "unsafe deny cases passed / unsafe deny cases", "0.0 to 1.0", "higher_is_better", "suite/split", "1 when no cases", "warning/manual", "Small fixture set."),
    "intent_alignment_accuracy": MetricDefinition("intent_alignment_accuracy", "Intent Alignment Accuracy", "semantic_tool_policy", "intent alignment cases passed / intent cases", "0.0 to 1.0", "higher_is_better", "suite/split", "1 when no cases", "warning/manual", "Intent labels are fixture-derived."),
    "capability_alignment_accuracy": MetricDefinition("capability_alignment_accuracy", "Capability Alignment Accuracy", "semantic_tool_policy", "capability alignment cases passed / capability cases", "0.0 to 1.0", "higher_is_better", "suite/split", "1 when no cases", "warning/manual", "Checks explicit mapping only."),
    "mentoring_mode_enforcement_accuracy": MetricDefinition("mentoring_mode_enforcement_accuracy", "Mentoring Mode Enforcement Accuracy", "semantic_tool_policy", "mentoring mode cases passed / mode cases", "0.0 to 1.0", "higher_is_better", "suite/split", "1 when no cases", "warning/manual", "Current modes are bounded to implemented runtime context."),
    "solution_leakage_policy_accuracy": MetricDefinition("solution_leakage_policy_accuracy", "Solution Leakage Policy Accuracy", "semantic_tool_policy", "leakage-policy cases passed / leakage cases", "0.0 to 1.0", "higher_is_better", "suite/split", "1 when no cases", "blocking in explicit suite", "Does not prove absence of all leakage."),
    "injection_suspicion_recall": MetricDefinition("injection_suspicion_recall", "Injection Suspicion Recall", "semantic_tool_policy", "labeled injection cases detected / injection cases", "0.0 to 1.0", "higher_is_better", "suite/split", "1 when no cases", "warning/manual", "Detects obvious patterns only."),
    "false_positive_deny_rate": MetricDefinition("false_positive_deny_rate", "False Positive Deny Rate", "semantic_tool_policy", "safe allow cases denied / safe allow cases", "0.0 to 1.0", "lower_is_better", "suite/split", "0 when no cases", "blocking in explicit suite", "Only fixture-labeled safe allows."),
    "structural_precedence_accuracy": MetricDefinition("structural_precedence_accuracy", "Structural Precedence Accuracy", "semantic_tool_policy", "structural precedence cases passed / structural cases", "0.0 to 1.0", "higher_is_better", "suite/split", "1 when no cases", "blocking in explicit suite", "Checks structural deny dominance."),
    "persistence_completeness": MetricDefinition("persistence_completeness", "Persistence Completeness", "semantic_tool_policy", "policy records with semantic fields / persistence cases", "0.0 to 1.0", "higher_is_better", "suite/split", "1 when no cases", "warning/manual", "Eval simulates record shape; API tests verify database persistence."),
    "trajectory_policy_event_coverage": MetricDefinition("trajectory_policy_event_coverage", "Trajectory Policy Event Coverage", "semantic_tool_policy", "cases with required policy events / trajectory cases", "0.0 to 1.0", "higher_is_better", "suite/split", "1 when no cases", "warning/manual", "Checks event presence, not trace quality."),
    "fallback_non_bypass_accuracy": MetricDefinition("fallback_non_bypass_accuracy", "Fallback Non-Bypass Accuracy", "semantic_tool_policy", "fallback non-bypass cases passed / fallback cases", "0.0 to 1.0", "higher_is_better", "suite/split", "1 when no cases", "blocking in explicit suite", "Route tests provide stronger runtime proof."),
    "structured_output_validity": MetricDefinition("structured_output_validity", "Semantic Policy Structured Output Validity", "semantic_tool_policy", "valid decision outputs / case_count", "0.0 to 1.0", "higher_is_better", "suite/split", "0 when no cases", "warning/manual", "Dataclass shape validation only."),
}


def metric_catalog() -> list[dict[str, str]]:
    return [definition.to_dict() for definition in METRIC_REGISTRY.values()]
