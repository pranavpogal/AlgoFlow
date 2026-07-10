from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4

from app.skills.problem_intelligence.workflow import ProblemClassificationContext, classify_problem

SKILL_VERSION = "pattern-transfer-skill-v1"


class TransferType(StrEnum):
    PREREQUISITE_REPAIR = "PREREQUISITE_REPAIR"
    REINFORCEMENT = "REINFORCEMENT"
    NEAR_TRANSFER = "NEAR_TRANSFER"
    FAR_TRANSFER = "FAR_TRANSFER"
    PATTERN_VARIATION = "PATTERN_VARIATION"
    DIFFICULTY_PROGRESSION = "DIFFICULTY_PROGRESSION"
    MISCONCEPTION_REMEDIATION = "MISCONCEPTION_REMEDIATION"
    INTERLEAVING = "INTERLEAVING"
    CONTRASTIVE_TRANSFER = "CONTRASTIVE_TRANSFER"
    NOVEL_COMPOSITION = "NOVEL_COMPOSITION"


TRANSFER_TAXONOMY = {
    TransferType.PREREQUISITE_REPAIR: "Repair missing prerequisite knowledge before progressing.",
    TransferType.REINFORCEMENT: "Practice substantially similar structure to stabilize uncertain capability.",
    TransferType.NEAR_TRANSFER: "Apply a known structural idea in a closely related formulation.",
    TransferType.FAR_TRANSFER: "Apply a known structural idea in a substantially different surface formulation.",
    TransferType.PATTERN_VARIATION: "Exercise a meaningful variation of an existing pattern.",
    TransferType.DIFFICULTY_PROGRESSION: "Move to a harder variant after sufficient evidence.",
    TransferType.MISCONCEPTION_REMEDIATION: "Select a problem that exposes or corrects a recurring misconception.",
    TransferType.INTERLEAVING: "Mix related structures to improve pattern discrimination.",
    TransferType.CONTRASTIVE_TRANSFER: "Compare similar-looking problems whose decision rules differ.",
    TransferType.NOVEL_COMPOSITION: "Combine multiple previously encountered structures in a new way.",
}

EVIDENCE_HIERARCHY = [
    {"type": "passive_exposure", "strength": 0.1, "may_influence_recommendation": True, "may_influence_mastery": False},
    {"type": "pattern_encountered", "strength": 0.18, "may_influence_recommendation": True, "may_influence_mastery": False},
    {"type": "hint_assisted_reasoning", "strength": 0.32, "may_influence_recommendation": True, "may_influence_mastery": False},
    {"type": "approach_submitted", "strength": 0.45, "may_influence_recommendation": True, "may_influence_mastery": False},
    {"type": "review_finding", "strength": 0.55, "may_influence_recommendation": True, "may_influence_mastery": False},
    {"type": "repeated_independent_success", "strength": 0.9, "may_influence_recommendation": True, "may_influence_mastery": True},
    {"type": "verified_successful_transfer", "strength": 1.0, "may_influence_recommendation": True, "may_influence_mastery": True},
]


@dataclass(frozen=True)
class TransferProblem:
    problem_id: str
    title: str
    difficulty: str
    description: str
    surface_domain: str


@dataclass(frozen=True)
class StructuralRelationship:
    source_problem_id: str
    target_problem_id: str
    relationship_type: TransferType
    shared_patterns: list[str]
    shared_subpatterns: list[str]
    shared_structural_cues: list[str]
    shared_prerequisites: list[str]
    important_differences: list[str]
    abstraction_distance: float
    confidence: float
    evidence: list[dict[str, Any]]
    provenance: list[str]


@dataclass(frozen=True)
class TransferRecommendation:
    recommendation_id: str
    recommendation_type: TransferType
    source_problem_id: str
    target_problem_id: str
    target_title: str
    target_difficulty: str
    source_pattern: str
    target_pattern: str
    shared_structures: list[str]
    important_differences: list[str]
    learner_evidence_used: list[dict[str, Any]]
    learner_state_confidence: float
    classification_confidence: float
    relationship_confidence: float
    recommendation_confidence: float
    reason: str
    transfer_bridge: str
    expected_learning_goal: str
    evidence: list[dict[str, Any]]
    provenance: list[str]
    unsupported_claims: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "recommendation_type": self.recommendation_type.value,
            "source_problem_id": self.source_problem_id,
            "target_problem_id": self.target_problem_id,
            "target_title": self.target_title,
            "target_difficulty": self.target_difficulty,
            "source_pattern": self.source_pattern,
            "target_pattern": self.target_pattern,
            "shared_structures": self.shared_structures,
            "important_differences": self.important_differences,
            "learner_evidence_used": self.learner_evidence_used,
            "learner_state_confidence": self.learner_state_confidence,
            "classification_confidence": self.classification_confidence,
            "relationship_confidence": self.relationship_confidence,
            "recommendation_confidence": self.recommendation_confidence,
            "reason": self.reason,
            "transfer_bridge": self.transfer_bridge,
            "expected_learning_goal": self.expected_learning_goal,
            "evidence": self.evidence,
            "provenance": self.provenance,
            "unsupported_claims": self.unsupported_claims,
        }


@dataclass(frozen=True)
class PatternTransferContext:
    title: str
    description: str
    learner_state: dict[str, Any]
    memory: dict[str, Any]
    previous_transfer_events: list[Any] = field(default_factory=list)
    max_recommendations: int = 3


@dataclass(frozen=True)
class PatternTransferResult:
    source_problem_id: str
    source_title: str
    source_topic: str
    source_pattern: str
    taxonomy_version: str
    classification_confidence: float
    learner_state_confidence_bucket: str
    learner_state_confidence: float
    recommendations: list[TransferRecommendation]
    fallback_reason: str | None
    evidence_hierarchy: list[dict[str, Any]]
    transfer_taxonomy: dict[str, str]
    same_topic_shortcut_used: bool = False
    skill_version: str = SKILL_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_problem_id": self.source_problem_id,
            "source_title": self.source_title,
            "source_topic": self.source_topic,
            "source_pattern": self.source_pattern,
            "taxonomy_version": self.taxonomy_version,
            "classification_confidence": self.classification_confidence,
            "learner_state_confidence_bucket": self.learner_state_confidence_bucket,
            "learner_state_confidence": self.learner_state_confidence,
            "recommendations": [item.to_dict() for item in self.recommendations],
            "fallback_reason": self.fallback_reason,
            "evidence_hierarchy": self.evidence_hierarchy,
            "transfer_taxonomy": {key.value: value for key, value in self.transfer_taxonomy.items()},
            "same_topic_shortcut_used": self.same_topic_shortcut_used,
            "skill_version": self.skill_version,
        }


PROBLEM_CORPUS = [
    TransferProblem("lc_1", "Two Sum", "Easy", "hash lookup complement seen set target sum", "array lookup"),
    TransferProblem("lc_198", "House Robber", "Medium", "maximum amount without adjacent houses rob skip decision dp", "linear houses"),
    TransferProblem("lc_213", "House Robber II", "Medium", "maximum amount circular houses adjacent constraint decision dp", "circular houses"),
    TransferProblem("lc_337", "House Robber III", "Medium", "binary tree rob nodes without adjacent parent child tree dp", "tree houses"),
    TransferProblem("lc_740", "Delete and Earn", "Medium", "value compression into house robber choose number delete adjacent values", "number values"),
    TransferProblem("lc_368", "Largest Divisible Subset", "Medium", "largest divisible subset chain sorting best chain ending at each index", "divisibility chain"),
    TransferProblem("lc_416", "Partition Equal Subset Sum", "Medium", "choose items target sum capacity subset sum knapsack dp", "partition values"),
    TransferProblem("lc_494", "Target Sum", "Medium", "assign signs to reach target subset sum difference state", "signed values"),
    TransferProblem("lc_1143", "Longest Common Subsequence", "Medium", "two strings longest common subsequence two sequence dp table", "strings"),
    TransferProblem("lc_312", "Burst Balloons", "Hard", "interval dp choose last balloon split point", "interval game"),
    TransferProblem("lc_1011", "Capacity To Ship Packages Within D Days", "Medium", "minimum capacity monotonic predicate feasibility binary search on answer", "shipping schedule"),
    TransferProblem("lc_875", "Koko Eating Bananas", "Medium", "minimum speed finish before deadline monotonic feasibility binary search on answer", "eating speed"),
    TransferProblem("lc_410", "Split Array Largest Sum", "Hard", "minimize maximum subarray sum monotonic feasibility binary search on answer", "array partition"),
    TransferProblem("lc_704", "Binary Search", "Easy", "sorted array boundary search target", "array search"),
    TransferProblem("lc_3", "Longest Substring Without Repeating Characters", "Medium", "longest substring without duplicate contiguous window hash set", "string window"),
    TransferProblem("lc_209", "Minimum Size Subarray Sum", "Medium", "minimum length contiguous subarray positive numbers sliding window", "array window"),
    TransferProblem("lc_560", "Subarray Sum Equals K", "Medium", "prefix sum hash lookup cumulative values count subarrays", "array sums"),
    TransferProblem("lc_739", "Daily Temperatures", "Medium", "next greater temperature monotonic stack", "temperatures"),
    TransferProblem("lc_496", "Next Greater Element I", "Easy", "next greater element monotonic stack", "array relation"),
    TransferProblem("lc_200", "Number of Islands", "Medium", "grid graph connected components visited dfs bfs", "grid graph"),
    TransferProblem("lc_994", "Rotting Oranges", "Medium", "minimum steps level order bfs multiple sources grid", "grid graph"),
    TransferProblem("lc_743", "Network Delay Time", "Medium", "weighted graph shortest path minimum distance dijkstra relaxation", "network graph"),
    TransferProblem("lc_207", "Course Schedule", "Medium", "prerequisites directed edges topological ordering cycle", "course graph"),
    TransferProblem("lc_684", "Redundant Connection", "Medium", "union find connected components extra edge", "undirected graph"),
    TransferProblem("lc_56", "Merge Intervals", "Medium", "merge overlapping intervals sorting by start", "time intervals"),
    TransferProblem("lc_435", "Non-overlapping Intervals", "Medium", "minimum intervals remove non-overlap greedy sorting", "time intervals"),
    TransferProblem("lc_46", "Permutations", "Medium", "recursive choice exploration generate every permutation backtracking", "arrangements"),
    TransferProblem("lc_212", "Word Search II", "Hard", "trie prefix tree board dfs pruning", "word grid"),
]

CURATED_TRANSFER_RELATIONSHIPS = {
    ("lc_198", "lc_213"): TransferType.NEAR_TRANSFER,
    ("lc_198", "lc_337"): TransferType.DIFFICULTY_PROGRESSION,
    ("lc_198", "lc_740"): TransferType.FAR_TRANSFER,
    ("lc_1011", "lc_875"): TransferType.FAR_TRANSFER,
    ("lc_704", "lc_1011"): TransferType.MISCONCEPTION_REMEDIATION,
    ("lc_368", "lc_416"): TransferType.PATTERN_VARIATION,
    ("lc_200", "lc_994"): TransferType.NEAR_TRANSFER,
    ("lc_560", "lc_1"): TransferType.PREREQUISITE_REPAIR,
    ("lc_207", "lc_684"): TransferType.PATTERN_VARIATION,
    ("lc_56", "lc_435"): TransferType.PATTERN_VARIATION,
    ("lc_739", "lc_496"): TransferType.NEAR_TRANSFER,
    ("lc_1143", "lc_312"): TransferType.PATTERN_VARIATION,
}

DIFFICULTY_RANK = {"Easy": 1, "Medium": 2, "Hard": 3, "Unknown": 2}


def generate_pattern_transfer(context: PatternTransferContext) -> PatternTransferResult:
    source_classification = classify_problem(
        ProblemClassificationContext(title=context.title, description=context.description)
    )
    source_id = _source_id(context.title)
    learner_bucket = context.learner_state.get("confidence", "unknown")
    learner_confidence = _learner_confidence(context.learner_state)
    learner_evidence = _learner_evidence(context.memory, source_classification.primary_topic)
    previous_targets = _previous_targets(context.previous_transfer_events)

    recommendations: list[TransferRecommendation] = []
    for candidate in PROBLEM_CORPUS:
        if candidate.title.lower() == context.title.lower() or candidate.problem_id in previous_targets:
            continue
        target_classification = classify_problem(
            ProblemClassificationContext(title=candidate.title, description=candidate.description)
        )
        relationship = build_relationship(source_id, source_classification, candidate, target_classification)
        if relationship.confidence >= 0.36:
            transfer_type = decide_transfer_type(
                relationship,
                source_classification.to_legacy_dict(),
                target_classification.to_legacy_dict(),
                context.learner_state,
                learner_evidence,
            )
            recommendations.append(
                _recommendation(
                    relationship=relationship,
                    transfer_type=transfer_type,
                    source_title=context.title,
                    source_classification=source_classification.to_legacy_dict(),
                    candidate=candidate,
                    target_classification=target_classification.to_legacy_dict(),
                    learner_evidence=learner_evidence,
                    learner_confidence=learner_confidence,
                )
            )

    recommendations.sort(
        key=lambda item: (
            "CURATED_TRANSFER_RELATION" in item.provenance,
            _policy_priority(item.recommendation_type),
            item.recommendation_confidence,
        ),
        reverse=True,
    )
    recommendations = recommendations[: context.max_recommendations]

    fallback = None
    if not recommendations:
        fallback = "Insufficient structural relationships in the current bounded corpus for a strong transfer recommendation."

    return PatternTransferResult(
        source_problem_id=source_id,
        source_title=context.title,
        source_topic=source_classification.primary_topic,
        source_pattern=source_classification.primary_pattern,
        taxonomy_version=source_classification.taxonomy_version,
        classification_confidence=source_classification.confidence,
        learner_state_confidence_bucket=learner_bucket,
        learner_state_confidence=learner_confidence,
        recommendations=recommendations,
        fallback_reason=fallback,
        evidence_hierarchy=EVIDENCE_HIERARCHY,
        transfer_taxonomy=TRANSFER_TAXONOMY,
        same_topic_shortcut_used=False,
    )


def build_relationship(
    source_problem_id: str,
    source: Any,
    candidate: TransferProblem,
    target: Any,
) -> StructuralRelationship:
    source_dict = source.to_legacy_dict() if hasattr(source, "to_legacy_dict") else source
    target_dict = target.to_legacy_dict() if hasattr(target, "to_legacy_dict") else target
    shared_patterns = _shared([source_dict.get("primary_pattern")], [target_dict.get("primary_pattern")])
    shared_subpatterns = _shared(source_dict.get("sub_patterns", []), target_dict.get("sub_patterns", []))
    shared_cues = _shared_tokens(source_dict.get("structural_cues", []), target_dict.get("structural_cues", []))
    shared_prereqs = _shared(source_dict.get("prerequisites", []), target_dict.get("prerequisites", []))
    topic_same = source_dict.get("primary_topic") == target_dict.get("primary_topic")
    pattern_same = bool(shared_patterns)
    curated_type = CURATED_TRANSFER_RELATIONSHIPS.get((source_problem_id, candidate.problem_id))
    domain_distance = 0.1 if candidate.surface_domain in source_problem_id.lower() else 0.45
    if source_dict.get("primary_pattern") != target_dict.get("primary_pattern"):
        domain_distance += 0.2
    if not topic_same:
        domain_distance += 0.15
    abstraction_distance = round(min(1.0, domain_distance), 2)
    confidence = 0.18
    confidence += 0.34 if pattern_same else 0
    confidence += min(0.18, len(shared_subpatterns) * 0.06)
    confidence += min(0.16, len(shared_prereqs) * 0.03)
    confidence += min(0.14, len(shared_cues) * 0.04)
    if topic_same and not pattern_same:
        confidence += 0.08
    if curated_type:
        confidence += 0.22
    confidence = round(min(0.95, confidence), 2)
    relationship_type = curated_type or _initial_relationship_type(
        topic_same, pattern_same, abstraction_distance, source_dict, target_dict
    )
    differences = _differences(source_dict, target_dict, candidate)
    evidence = [
        {"type": "shared_pattern", "value": shared_patterns, "strength": 0.34},
        {"type": "shared_subpatterns", "value": shared_subpatterns, "strength": min(0.18, len(shared_subpatterns) * 0.06)},
        {"type": "shared_prerequisites", "value": shared_prereqs, "strength": min(0.16, len(shared_prereqs) * 0.03)},
        {"type": "abstraction_distance", "value": abstraction_distance, "strength": 1 - abstraction_distance},
    ]
    return StructuralRelationship(
        source_problem_id=source_problem_id,
        target_problem_id=candidate.problem_id,
        relationship_type=relationship_type,
        shared_patterns=shared_patterns,
        shared_subpatterns=shared_subpatterns,
        shared_structural_cues=shared_cues,
        shared_prerequisites=shared_prereqs,
        important_differences=differences,
        abstraction_distance=abstraction_distance,
        confidence=confidence,
        evidence=evidence,
        provenance=[
            "PROBLEM_INTELLIGENCE_TAXONOMY",
            "STATIC_TRANSFER_CORPUS",
            "DETERMINISTIC_RELATIONSHIP_RULE",
            *(["CURATED_TRANSFER_RELATION"] if curated_type else []),
        ],
    )


def decide_transfer_type(
    relationship: StructuralRelationship,
    source: dict[str, Any],
    target: dict[str, Any],
    learner_state: dict[str, Any],
    learner_evidence: list[dict[str, Any]],
) -> TransferType:
    mistakes = " ".join(item.get("category", "") for item in learner_state.get("common_mistakes", [])).lower()
    if any(token in mistakes for token in ["dp", "boundary", "binary", "graph"]):
        if _mistake_matches_target(mistakes, target):
            return TransferType.MISCONCEPTION_REMEDIATION
    if "CURATED_TRANSFER_RELATION" in relationship.provenance:
        if relationship.relationship_type == TransferType.DIFFICULTY_PROGRESSION:
            if _has_strong_evidence(learner_evidence):
                return TransferType.DIFFICULTY_PROGRESSION
        elif relationship.relationship_type == TransferType.PREREQUISITE_REPAIR:
            return TransferType.PREREQUISITE_REPAIR
        elif learner_state.get("confidence") not in {"unknown", "low"}:
            return relationship.relationship_type
    if relationship.shared_prerequisites and learner_state.get("confidence") in {"unknown", "low"}:
        return TransferType.PREREQUISITE_REPAIR
    if source.get("primary_pattern") == target.get("primary_pattern"):
        if relationship.abstraction_distance <= 0.45:
            return TransferType.NEAR_TRANSFER
        return TransferType.FAR_TRANSFER
    if source.get("primary_topic") == target.get("primary_topic"):
        if relationship.confidence < 0.55:
            return TransferType.CONTRASTIVE_TRANSFER
        return TransferType.PATTERN_VARIATION
    if len(relationship.shared_prerequisites) >= 2 and relationship.confidence >= 0.55:
        return TransferType.FAR_TRANSFER
    if source.get("secondary_topics") or target.get("secondary_topics"):
        return TransferType.NOVEL_COMPOSITION
    return relationship.relationship_type


def _recommendation(
    *,
    relationship: StructuralRelationship,
    transfer_type: TransferType,
    source_title: str,
    source_classification: dict[str, Any],
    candidate: TransferProblem,
    target_classification: dict[str, Any],
    learner_evidence: list[dict[str, Any]],
    learner_confidence: float,
) -> TransferRecommendation:
    classification_confidence = min(
        float(source_classification.get("confidence") or 0.35), float(target_classification.get("confidence") or 0.35)
    )
    relationship_confidence = relationship.confidence
    recommendation_confidence = round(
        min(0.95, classification_confidence * 0.35 + relationship_confidence * 0.45 + learner_confidence * 0.2), 2
    )
    shared = relationship.shared_patterns + relationship.shared_subpatterns + relationship.shared_structural_cues
    if not shared:
        shared = relationship.shared_prerequisites[:2]
    reason = _reason(transfer_type, source_title, candidate.title, shared, learner_confidence)
    bridge = _bridge(source_title, candidate.title, source_classification, target_classification, relationship)
    unsupported = [
        "Recommendation shown is not mastery evidence.",
        "Classification evidence and learner-performance evidence are kept separate.",
    ]
    if learner_confidence < 0.45:
        unsupported.append("Insufficient evidence for a strongly personalized transfer recommendation.")
    return TransferRecommendation(
        recommendation_id=f"transfer_{uuid4().hex[:12]}",
        recommendation_type=transfer_type,
        source_problem_id=relationship.source_problem_id,
        target_problem_id=relationship.target_problem_id,
        target_title=candidate.title,
        target_difficulty=candidate.difficulty,
        source_pattern=source_classification.get("primary_pattern", "Unknown"),
        target_pattern=target_classification.get("primary_pattern", "Unknown"),
        shared_structures=shared[:5],
        important_differences=relationship.important_differences,
        learner_evidence_used=learner_evidence[:5],
        learner_state_confidence=learner_confidence,
        classification_confidence=round(classification_confidence, 2),
        relationship_confidence=relationship_confidence,
        recommendation_confidence=recommendation_confidence,
        reason=reason,
        transfer_bridge=bridge,
        expected_learning_goal=_learning_goal(transfer_type, target_classification),
        evidence=relationship.evidence,
        provenance=relationship.provenance + ["LEARNER_STATE_DERIVED_EVIDENCE"],
        unsupported_claims=unsupported,
    )


def _source_id(title: str) -> str:
    slug = "_".join(title.lower().replace("/", " ").split())[:40]
    for problem in PROBLEM_CORPUS:
        if problem.title.lower() == title.lower():
            return problem.problem_id
    return f"input_{slug or 'problem'}"


def _learner_confidence(learner_state: dict[str, Any]) -> float:
    bucket = learner_state.get("confidence", "unknown")
    return {"unknown": 0.2, "low": 0.35, "medium": 0.62, "high": 0.82}.get(bucket, 0.2)


def _learner_evidence(memory: dict[str, Any], topic: str) -> list[dict[str, Any]]:
    evidence = []
    pattern_counts = memory.get("pattern_counts", {})
    if topic in pattern_counts:
        evidence.append({"type": "pattern_encountered", "concept": topic, "count": pattern_counts[topic], "strength": 0.18})
    for mistake, count in memory.get("mistake_counts", {}).items():
        if topic.lower() in mistake.lower() or any(token in mistake.lower() for token in ["dp", "binary", "graph", "boundary"]):
            evidence.append({"type": "review_finding", "concept": mistake, "count": count, "strength": 0.55})
    for event_type, count in memory.get("learning_event_counts", {}).items():
        if event_type in {"HintDelivered", "ReviewDelivered", "CodeReviewCompleted"}:
            evidence.append({"type": event_type, "count": count, "strength": 0.32})
    return evidence


def _previous_targets(events: list[Any]) -> set[str]:
    targets = set()
    for event in events:
        evidence = getattr(event, "evidence", {}) or {}
        target_id = evidence.get("target_problem_id")
        if target_id:
            targets.add(target_id)
    return targets


def _shared(left: list[Any], right: list[Any]) -> list[str]:
    left_set = {str(item) for item in left if item}
    right_set = {str(item) for item in right if item}
    return sorted(left_set & right_set)


def _shared_tokens(left: list[str], right: list[str]) -> list[str]:
    shared = []
    for item in left:
        item_tokens = set(item.lower().split())
        if any(item_tokens & set(other.lower().split()) for other in right):
            shared.append(item)
    return shared[:4]


def _initial_relationship_type(topic_same: bool, pattern_same: bool, distance: float, source: dict[str, Any], target: dict[str, Any]) -> TransferType:
    if pattern_same and distance <= 0.45:
        return TransferType.NEAR_TRANSFER
    if pattern_same:
        return TransferType.FAR_TRANSFER
    if topic_same:
        return TransferType.PATTERN_VARIATION
    if set(source.get("prerequisites", [])) & set(target.get("prerequisites", [])):
        return TransferType.INTERLEAVING
    return TransferType.CONTRASTIVE_TRANSFER


def _differences(source: dict[str, Any], target: dict[str, Any], candidate: TransferProblem) -> list[str]:
    differences = []
    if source.get("primary_pattern") != target.get("primary_pattern"):
        differences.append(f"Pattern changes from {source.get('primary_pattern')} to {target.get('primary_pattern')}.")
    if source.get("primary_topic") != target.get("primary_topic"):
        differences.append(f"Topic shifts from {source.get('primary_topic')} to {target.get('primary_topic')}.")
    if candidate.difficulty != source.get("difficulty"):
        differences.append(f"Difficulty changes to {candidate.difficulty}.")
    if not differences:
        differences.append(f"Surface domain changes to {candidate.surface_domain}.")
    return differences[:4]


def _mistake_matches_target(mistakes: str, target: dict[str, Any]) -> bool:
    combined = f"{target.get('primary_topic')} {target.get('primary_pattern')} {' '.join(target.get('sub_patterns', []))}".lower()
    return any(token in mistakes and token in combined for token in ["dp", "binary", "graph", "boundary"])


def _has_strong_evidence(evidence: list[dict[str, Any]]) -> bool:
    return sum(item.get("count", 1) * item.get("strength", 0) for item in evidence) >= 1.2


def _difficulty_rank(difficulty: str | None) -> int:
    return DIFFICULTY_RANK.get(difficulty or "Unknown", 2)


def _policy_priority(transfer_type: TransferType) -> int:
    order = {
        TransferType.MISCONCEPTION_REMEDIATION: 10,
        TransferType.PREREQUISITE_REPAIR: 9,
        TransferType.DIFFICULTY_PROGRESSION: 9,
        TransferType.NEAR_TRANSFER: 8,
        TransferType.PATTERN_VARIATION: 7,
        TransferType.FAR_TRANSFER: 6,
        TransferType.CONTRASTIVE_TRANSFER: 4,
        TransferType.INTERLEAVING: 3,
        TransferType.NOVEL_COMPOSITION: 2,
        TransferType.REINFORCEMENT: 1,
    }
    return order[transfer_type]


def _reason(transfer_type: TransferType, source_title: str, target_title: str, shared: list[str], learner_confidence: float) -> str:
    shared_text = ", ".join(shared[:2]) if shared else "a prerequisite reasoning structure"
    learner_note = " Learner evidence is sparse, so this is cautious." if learner_confidence < 0.45 else ""
    return f"{transfer_type.value} from {source_title} to {target_title}: shared structure is {shared_text}.{learner_note}"


def _bridge(source_title: str, target_title: str, source: dict[str, Any], target: dict[str, Any], relationship: StructuralRelationship) -> str:
    return (
        f"In {source_title}, focus on {source.get('primary_pattern')}. In {target_title}, carry over "
        f"{', '.join(relationship.shared_subpatterns or relationship.shared_prerequisites[:2]) or 'the invariant'} while adjusting for "
        f"{'; '.join(relationship.important_differences[:2])}"
    )


def _learning_goal(transfer_type: TransferType, target: dict[str, Any]) -> str:
    if transfer_type == TransferType.PREREQUISITE_REPAIR:
        return f"Repair prerequisites for {target.get('primary_pattern')} before increasing difficulty."
    if transfer_type == TransferType.CONTRASTIVE_TRANSFER:
        return "Explain why the apparent similarity does not imply the same decision rule."
    if transfer_type == TransferType.MISCONCEPTION_REMEDIATION:
        return "Expose the recurring misconception in a smaller, inspectable setting."
    return f"Practice recognizing {target.get('primary_pattern')} from structural cues rather than title keywords."
