from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


TAXONOMY_VERSION = "problem-intelligence-taxonomy-v1"


class Provenance(StrEnum):
    CURATED_METADATA = "CURATED_METADATA"
    TITLE_HEURISTIC = "TITLE_HEURISTIC"
    STATEMENT_EVIDENCE = "STATEMENT_EVIDENCE"
    CONSTRAINT_EVIDENCE = "CONSTRAINT_EVIDENCE"
    STRUCTURAL_RULE = "STRUCTURAL_RULE"
    MODEL_INFERENCE = "MODEL_INFERENCE"


@dataclass(frozen=True)
class TaxonomyNode:
    id: str
    label: str
    kind: str


@dataclass(frozen=True)
class ClassificationEvidence:
    observed_evidence: str
    inferred_label: str
    confidence: float
    provenance: Provenance
    cue_type: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "observed_evidence": self.observed_evidence,
            "inferred_label": self.inferred_label,
            "confidence": self.confidence,
            "provenance": self.provenance.value,
            "cue_type": self.cue_type,
        }


@dataclass(frozen=True)
class ProblemClassificationContext:
    title: str
    description: str
    problem_number: str | None = None
    url: str | None = None
    known_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProblemClassificationResult:
    problem: str
    difficulty: str
    primary_topic: str
    secondary_topics: list[str]
    primary_pattern: str
    subpatterns: list[str]
    structural_cues: list[str]
    prerequisites: list[str]
    related_patterns: list[str]
    difficulty_signals: list[str]
    confidence: float
    evidence: list[ClassificationEvidence]
    provenance: list[Provenance]
    unsupported_claims: list[str]
    reasoning: str
    taxonomy_version: str = TAXONOMY_VERSION

    def to_legacy_dict(self) -> dict[str, Any]:
        return {
            "difficulty": self.difficulty,
            "pattern": self.primary_topic,
            "sub_patterns": self.subpatterns,
            "prerequisites": self.prerequisites,
            "reasoning": self.reasoning,
            "primary_topic": self.primary_topic,
            "secondary_topics": self.secondary_topics,
            "primary_pattern": self.primary_pattern,
            "structural_cues": self.structural_cues,
            "related_patterns": self.related_patterns,
            "difficulty_signals": self.difficulty_signals,
            "confidence": self.confidence,
            "evidence": [item.to_dict() for item in self.evidence],
            "provenance": [item.value for item in self.provenance],
            "unsupported_claims": self.unsupported_claims,
            "taxonomy_version": self.taxonomy_version,
        }


TOPICS = {
    "arrays": TaxonomyNode("topic.arrays", "Arrays", "TOPIC"),
    "hashing": TaxonomyNode("topic.hashing", "Hashing", "TOPIC"),
    "two_pointers": TaxonomyNode("topic.two_pointers", "Two Pointers", "TOPIC"),
    "sliding_window": TaxonomyNode("topic.sliding_window", "Sliding Window", "TOPIC"),
    "binary_search": TaxonomyNode("topic.binary_search", "Binary Search", "TOPIC"),
    "stacks": TaxonomyNode("topic.stacks", "Stacks", "TOPIC"),
    "linked_lists": TaxonomyNode("topic.linked_lists", "Linked Lists", "TOPIC"),
    "trees": TaxonomyNode("topic.trees", "Trees", "TOPIC"),
    "graphs": TaxonomyNode("topic.graphs", "Graphs", "TOPIC"),
    "greedy": TaxonomyNode("topic.greedy", "Greedy", "TOPIC"),
    "intervals": TaxonomyNode("topic.intervals", "Intervals", "TOPIC"),
    "dynamic_programming": TaxonomyNode("topic.dynamic_programming", "Dynamic Programming", "TOPIC"),
    "bit_manipulation": TaxonomyNode("topic.bit_manipulation", "Bit Manipulation", "TOPIC"),
    "prefix_sums": TaxonomyNode("topic.prefix_sums", "Prefix Sums", "TOPIC"),
    "backtracking": TaxonomyNode("topic.backtracking", "Backtracking", "TOPIC"),
    "tries": TaxonomyNode("topic.tries", "Tries", "TOPIC"),
    "general": TaxonomyNode("topic.general", "General Problem Solving", "TOPIC"),
}

PATTERNS = {
    "hash_lookup": TaxonomyNode("pattern.hash_lookup", "Hash Lookup", "PATTERN"),
    "frequency_counting": TaxonomyNode("pattern.frequency_counting", "Frequency Counting", "PATTERN"),
    "opposing_pointers": TaxonomyNode("pattern.opposing_pointers", "Opposing Pointers", "PATTERN"),
    "variable_window": TaxonomyNode("pattern.variable_window", "Variable-Size Window", "PATTERN"),
    "binary_search_answer": TaxonomyNode("pattern.binary_search_answer", "Binary Search on Answer", "PATTERN"),
    "boundary_search": TaxonomyNode("pattern.boundary_search", "Boundary Search", "PATTERN"),
    "stack_matching": TaxonomyNode("pattern.stack_matching", "Stack Matching", "PATTERN"),
    "monotonic_stack": TaxonomyNode("pattern.monotonic_stack", "Monotonic Stack", "PATTERN"),
    "linked_list_pointers": TaxonomyNode("pattern.linked_list_pointers", "Linked List Pointer Manipulation", "PATTERN"),
    "tree_dfs": TaxonomyNode("pattern.tree_dfs", "Tree DFS", "PATTERN"),
    "bst_invariant": TaxonomyNode("pattern.bst_invariant", "BST Invariant", "PATTERN"),
    "graph_bfs": TaxonomyNode("pattern.graph_bfs", "BFS Traversal", "PATTERN"),
    "graph_dfs": TaxonomyNode("pattern.graph_dfs", "DFS Traversal", "PATTERN"),
    "shortest_path": TaxonomyNode("pattern.shortest_path", "Shortest Path", "PATTERN"),
    "topological_sort": TaxonomyNode("pattern.topological_sort", "Topological Sorting", "PATTERN"),
    "union_find": TaxonomyNode("pattern.union_find", "Union Find", "PATTERN"),
    "greedy_sorting": TaxonomyNode("pattern.greedy_sorting", "Greedy Sorting", "PATTERN"),
    "interval_merge": TaxonomyNode("pattern.interval_merge", "Interval Merge", "PATTERN"),
    "decision_dp": TaxonomyNode("pattern.decision_dp", "Decision DP", "PATTERN"),
    "knapsack_dp": TaxonomyNode("pattern.knapsack_dp", "Knapsack DP", "PATTERN"),
    "lis_dp": TaxonomyNode("pattern.lis_dp", "LIS-style DP", "PATTERN"),
    "lcs_dp": TaxonomyNode("pattern.lcs_dp", "LCS-style DP", "PATTERN"),
    "interval_dp": TaxonomyNode("pattern.interval_dp", "Interval DP", "PATTERN"),
    "digit_dp": TaxonomyNode("pattern.digit_dp", "Digit DP", "PATTERN"),
    "bitmasking": TaxonomyNode("pattern.bitmasking", "Bitmasking", "PATTERN"),
    "prefix_sum_lookup": TaxonomyNode("pattern.prefix_sum_lookup", "Prefix Sum Lookup", "PATTERN"),
    "choice_exploration": TaxonomyNode("pattern.choice_exploration", "Choice Exploration", "PATTERN"),
    "trie_prefix": TaxonomyNode("pattern.trie_prefix", "Trie Prefix Search", "PATTERN"),
    "general": TaxonomyNode("pattern.general", "General Reasoning", "PATTERN"),
}

PATTERN_TO_TOPIC = {
    "hash_lookup": "hashing",
    "frequency_counting": "hashing",
    "opposing_pointers": "two_pointers",
    "variable_window": "sliding_window",
    "binary_search_answer": "binary_search",
    "boundary_search": "binary_search",
    "stack_matching": "stacks",
    "monotonic_stack": "stacks",
    "linked_list_pointers": "linked_lists",
    "tree_dfs": "trees",
    "bst_invariant": "trees",
    "graph_bfs": "graphs",
    "graph_dfs": "graphs",
    "shortest_path": "graphs",
    "topological_sort": "graphs",
    "union_find": "graphs",
    "greedy_sorting": "greedy",
    "interval_merge": "intervals",
    "decision_dp": "dynamic_programming",
    "knapsack_dp": "dynamic_programming",
    "lis_dp": "dynamic_programming",
    "lcs_dp": "dynamic_programming",
    "interval_dp": "dynamic_programming",
    "digit_dp": "dynamic_programming",
    "bitmasking": "bit_manipulation",
    "prefix_sum_lookup": "prefix_sums",
    "choice_exploration": "backtracking",
    "trie_prefix": "tries",
    "general": "general",
}

CURATED_PROBLEMS = {
    "largest divisible subset": {
        "difficulty": "Medium",
        "primary_pattern": "lis_dp",
        "subpatterns": ["LIS-style DP", "Sorting", "Path Reconstruction"],
        "structural_cues": ["divisibility relation forms an ordered chain", "best chain ending at each index"],
        "prerequisites": ["Arrays", "Sorting", "Dynamic Programming"],
        "related_patterns": ["Knapsack DP", "Path Reconstruction"],
        "confidence": 0.96,
    },
    "house robber": {
        "difficulty": "Medium",
        "primary_pattern": "decision_dp",
        "subpatterns": ["1D DP", "Decision DP", "Rolling State"],
        "structural_cues": ["local rob-or-skip choice", "adjacent choices are incompatible"],
        "prerequisites": ["Arrays", "Recursion", "Memoization"],
        "related_patterns": ["Tree DP", "State Compression"],
        "confidence": 0.96,
    },
}

RULES = [
    ("binary_search_answer", 0.9, ["minimum capacity", "minimize maximum", "smallest maximum", "ship within", "koko", "monotonic predicate", "binary search on answer"], "monotonic feasibility predicate over answer space"),
    ("shortest_path", 0.88, ["shortest path", "minimum distance", "weighted graph", "dijkstra"], "shortest-path relaxation or distance objective"),
    ("topological_sort", 0.88, ["course schedule", "prerequisite", "topological", "directed acyclic"], "dependency ordering over directed edges"),
    ("union_find", 0.86, ["union", "disjoint", "connected components", "redundant connection"], "connectivity merges across components"),
    ("graph_bfs", 0.82, ["level order", "nearest", "minimum steps", "rotting oranges", "word ladder"], "level-by-level traversal cue"),
    ("graph_dfs", 0.8, ["island", "connected", "component", "visited", "dfs"], "visited-state traversal cue"),
    ("tree_dfs", 0.82, ["binary tree", "root", "ancestor", "path sum", "diameter"], "recursive tree structure cue"),
    ("bst_invariant", 0.86, ["bst", "binary search tree", "sorted iterator", "kth smallest"], "ordered binary-tree invariant"),
    ("variable_window", 0.84, ["longest substring", "minimum window", "at most", "contiguous subarray", "sliding window"], "contiguous window with expand/contract cue"),
    ("opposing_pointers", 0.78, ["two pointers", "sorted array", "pair sum", "3sum", "container with most water", "corner", "monotonic pointer movement"], "monotonic pointer movement cue"),
    ("boundary_search", 0.76, ["first occurrence", "last occurrence", "rotated sorted", "search insert", "sorted"], "ordered search boundary cue"),
    ("stack_matching", 0.82, ["valid parentheses", "matching parentheses", "nested brackets", "stack"], "last-in-first-out matching cue"),
    ("monotonic_stack", 0.86, ["next greater", "daily temperatures", "largest rectangle", "monotonic stack"], "nearest greater/smaller relation cue"),
    ("linked_list_pointers", 0.84, ["linked list", "cycle", "reverse list", "fast and slow"], "pointer-link structure cue"),
    ("interval_merge", 0.84, ["interval", "meeting rooms", "merge intervals", "overlap"], "range overlap structure cue"),
    ("greedy_sorting", 0.78, ["minimum number", "maximize", "jump game", "locally", "sort by", "non-overlap"], "local choice or exchange argument cue"),
    ("knapsack_dp", 0.86, ["capacity", "target sum", "partition", "choose items", "subset sum"], "prefix-and-capacity state cue"),
    ("lis_dp", 0.88, ["longest increasing", "divisible subset", "chain", "largest divisible"], "best chain ending at each index cue"),
    ("lcs_dp", 0.86, ["longest common", "edit distance", "two strings", "subsequence of two"], "two-sequence DP table cue"),
    ("interval_dp", 0.86, ["burst balloons", "matrix chain", "palindrome partition", "interval dp"], "dependency over sub-intervals cue"),
    ("digit_dp", 0.82, ["digit dp", "count numbers", "digits", "tight bound"], "digit-position state with bound cue"),
    ("decision_dp", 0.76, ["maximum amount", "minimum cost", "ways", "memo", "state", "recurrence", "rob"], "overlapping decision subproblem cue"),
    ("bitmasking", 0.82, ["bit", "xor", "mask", "subset mask", "power of two"], "bit-level representation cue"),
    ("prefix_sum_lookup", 0.82, ["prefix sum", "subarray sum", "range sum", "cumulative"], "cumulative aggregate lookup cue"),
    ("choice_exploration", 0.78, ["permutation", "combination", "backtracking", "valid parentheses", "n queens"], "recursive choice exploration cue"),
    ("trie_prefix", 0.84, ["trie", "prefix", "word search ii", "autocomplete"], "prefix tree lookup cue"),
    ("frequency_counting", 0.75, ["frequency", "anagram", "count", "character replacement"], "counting occurrences cue"),
    ("hash_lookup", 0.74, ["two sum", "duplicate", "hash map", "lookup", "seen set"], "constant-time lookup cue"),
]

TOPIC_LABELS = {key: node.label for key, node in TOPICS.items()}
PATTERN_LABELS = {key: node.label for key, node in PATTERNS.items()}
DEFAULT_PREREQUISITES = {
    "hashing": ["Hash Maps", "Set Membership"],
    "two_pointers": ["Arrays", "Sorting", "Pointer Invariants"],
    "sliding_window": ["Two Pointers", "Hash Maps", "Window Invariants"],
    "binary_search": ["Sorted Search", "Loop Invariants", "Monotonicity"],
    "stacks": ["Stacks", "Nearest Greater/Smaller Reasoning"],
    "linked_lists": ["Pointers", "Linked List Traversal"],
    "trees": ["Recursion", "Tree Traversal"],
    "graphs": ["Graph Modeling", "Visited-State Management"],
    "greedy": ["Sorting", "Exchange Arguments"],
    "intervals": ["Sorting", "Range Overlap Reasoning"],
    "dynamic_programming": ["Recursion", "Memoization", "State Transitions"],
    "bit_manipulation": ["Binary Representation", "Bit Operations"],
    "prefix_sums": ["Arrays", "Cumulative Sums", "Hash Maps"],
    "backtracking": ["Recursion", "Choice Trees", "Pruning"],
    "tries": ["Trees", "Prefix Matching"],
    "general": ["Complexity Analysis", "Edge Case Thinking"],
}

RELATED_PATTERNS = {
    "decision_dp": ["Knapsack DP", "State Compression"],
    "knapsack_dp": ["Decision DP", "Subset Sum"],
    "lis_dp": ["Sorting", "Path Reconstruction"],
    "lcs_dp": ["Edit Distance", "Two-Sequence DP"],
    "binary_search_answer": ["Greedy Feasibility", "Boundary Search"],
    "graph_bfs": ["Shortest Path", "Multi-source BFS"],
    "graph_dfs": ["BFS Traversal", "Union Find"],
    "monotonic_stack": ["Stacks", "Range Contribution"],
    "prefix_sum_lookup": ["Hash Lookup", "Sliding Window"],
}


def classify_problem(context: ProblemClassificationContext) -> ProblemClassificationResult:
    haystack = _haystack(context)
    curated = _curated_match(context.title)
    if curated:
        return _result_from_curated(context, curated)

    scores: dict[str, float] = defaultdict(float)
    evidence: list[ClassificationEvidence] = []
    for pattern_id, weight, phrases, cue in RULES:
        matched = [phrase for phrase in phrases if phrase in haystack]
        if not matched:
            continue
        confidence = min(0.92, weight + min(0.05, (len(matched) - 1) * 0.02))
        scores[pattern_id] += weight * len(matched)
        source = _source_for_match(context.title, context.description, matched[0])
        evidence.append(
            ClassificationEvidence(
                observed_evidence=", ".join(matched[:3]),
                inferred_label=PATTERN_LABELS[pattern_id],
                confidence=round(confidence, 2),
                provenance=source,
                cue_type=cue,
            )
        )

    if context.known_tags:
        for tag in context.known_tags:
            pattern_id = _pattern_from_tag(tag)
            if pattern_id:
                scores[pattern_id] += 1.2
                evidence.append(
                    ClassificationEvidence(
                        observed_evidence=tag,
                        inferred_label=PATTERN_LABELS[pattern_id],
                        confidence=0.85,
                        provenance=Provenance.CURATED_METADATA,
                        cue_type="provided tag metadata",
                    )
                )

    if not scores:
        return _fallback_result(context)

    ranked = [pattern_id for pattern_id, _ in Counter(scores).most_common()]
    primary_pattern_id = ranked[0]
    secondary_pattern_ids = _secondary_patterns(ranked, scores)
    primary_topic_id = PATTERN_TO_TOPIC[primary_pattern_id]
    secondary_topics = _secondary_topics(primary_topic_id, secondary_pattern_ids)
    confidence = _calibrated_confidence(scores, evidence, primary_pattern_id)
    difficulty, difficulty_signals = _infer_difficulty(haystack)
    structural_cues = _structural_cues(evidence)
    prerequisites = _prerequisites(primary_topic_id, primary_pattern_id)
    related_patterns = _related_patterns(primary_pattern_id, secondary_pattern_ids)
    provenance = sorted({item.provenance for item in evidence}, key=lambda item: item.value)

    return ProblemClassificationResult(
        problem=context.title,
        difficulty=difficulty,
        primary_topic=TOPIC_LABELS[primary_topic_id],
        secondary_topics=[TOPIC_LABELS[item] for item in secondary_topics],
        primary_pattern=PATTERN_LABELS[primary_pattern_id],
        subpatterns=_subpatterns(primary_pattern_id),
        structural_cues=structural_cues,
        prerequisites=prerequisites,
        related_patterns=related_patterns,
        difficulty_signals=difficulty_signals,
        confidence=confidence,
        evidence=evidence,
        provenance=provenance,
        unsupported_claims=["No model inference was used; classification is deterministic and evidence-limited."],
        reasoning=_reasoning(primary_pattern_id, structural_cues, confidence),
    )


def _result_from_curated(context: ProblemClassificationContext, curated: dict[str, Any]) -> ProblemClassificationResult:
    pattern_id = curated["primary_pattern"]
    topic_id = PATTERN_TO_TOPIC[pattern_id]
    evidence = [
        ClassificationEvidence(
            observed_evidence=context.title,
            inferred_label=PATTERN_LABELS[pattern_id],
            confidence=curated["confidence"],
            provenance=Provenance.CURATED_METADATA,
            cue_type="canonical problem metadata",
        )
    ]
    return ProblemClassificationResult(
        problem=context.title,
        difficulty=curated["difficulty"],
        primary_topic=TOPIC_LABELS[topic_id],
        secondary_topics=[],
        primary_pattern=PATTERN_LABELS[pattern_id],
        subpatterns=deepcopy(curated["subpatterns"]),
        structural_cues=deepcopy(curated["structural_cues"]),
        prerequisites=deepcopy(curated["prerequisites"]),
        related_patterns=deepcopy(curated["related_patterns"]),
        difficulty_signals=["canonical metadata"],
        confidence=curated["confidence"],
        evidence=evidence,
        provenance=[Provenance.CURATED_METADATA],
        unsupported_claims=["Curated classification does not imply learner mastery."],
        reasoning=_reasoning(pattern_id, curated["structural_cues"], curated["confidence"]),
    )


def _fallback_result(context: ProblemClassificationContext) -> ProblemClassificationResult:
    evidence = [
        ClassificationEvidence(
            observed_evidence="No strong structural cue matched.",
            inferred_label="General Problem Solving",
            confidence=0.35,
            provenance=Provenance.STATEMENT_EVIDENCE,
            cue_type="fallback after deterministic rule scan",
        )
    ]
    difficulty, difficulty_signals = _infer_difficulty(_haystack(context))
    return ProblemClassificationResult(
        problem=context.title,
        difficulty=difficulty,
        primary_topic="General Problem Solving",
        secondary_topics=[],
        primary_pattern="General Reasoning",
        subpatterns=["Brute Force Baseline", "Optimization Search"],
        structural_cues=[],
        prerequisites=DEFAULT_PREREQUISITES["general"],
        related_patterns=[],
        difficulty_signals=difficulty_signals,
        confidence=0.35,
        evidence=evidence,
        provenance=[Provenance.STATEMENT_EVIDENCE],
        unsupported_claims=["Insufficient structural evidence for a high-confidence classification."],
        reasoning="No strong structural cue matched, so the classifier returns a low-confidence general label.",
    )


def _curated_match(title: str) -> dict[str, Any] | None:
    lowered = title.lower()
    for known_title, metadata in CURATED_PROBLEMS.items():
        if known_title in lowered:
            return metadata
    return None


def _haystack(context: ProblemClassificationContext) -> str:
    tags = " ".join(context.known_tags)
    return f"{context.title} {context.description} {tags}".lower()


def _source_for_match(title: str, description: str, phrase: str) -> Provenance:
    if phrase in title.lower():
        return Provenance.TITLE_HEURISTIC
    if any(marker in description.lower() for marker in ["constraint", "1 <=", "10^", "10**"]):
        return Provenance.CONSTRAINT_EVIDENCE
    return Provenance.STATEMENT_EVIDENCE


def _pattern_from_tag(tag: str) -> str | None:
    lowered = tag.lower().replace(" ", "_")
    if lowered in PATTERN_TO_TOPIC:
        return lowered
    for key, node in PATTERNS.items():
        if tag.lower() == node.label.lower():
            return key
    return None


def _secondary_patterns(ranked: list[str], scores: dict[str, float]) -> list[str]:
    if not ranked:
        return []
    top_score = scores[ranked[0]]
    return [pattern_id for pattern_id in ranked[1:4] if scores[pattern_id] >= top_score * 0.3]


def _secondary_topics(primary_topic_id: str, secondary_pattern_ids: list[str]) -> list[str]:
    seen: list[str] = []
    for pattern_id in secondary_pattern_ids:
        topic_id = PATTERN_TO_TOPIC[pattern_id]
        if topic_id != primary_topic_id and topic_id not in seen:
            seen.append(topic_id)
    return seen


def _calibrated_confidence(
    scores: dict[str, float], evidence: list[ClassificationEvidence], primary_pattern_id: str
) -> float:
    top = scores[primary_pattern_id]
    total = sum(scores.values())
    separation = top / total if total else 0.0
    evidence_bonus = min(0.12, max(0, len(evidence) - 1) * 0.03)
    max_evidence = max((item.confidence for item in evidence if item.inferred_label == PATTERN_LABELS[primary_pattern_id]), default=0.35)
    confidence = min(0.95, max_evidence * 0.75 + separation * 0.2 + evidence_bonus)
    return round(confidence, 2)


def _infer_difficulty(haystack: str) -> tuple[str, list[str]]:
    signals: list[str] = []
    for difficulty in ("easy", "medium", "hard"):
        if difficulty in haystack:
            signals.append(f"explicit difficulty token: {difficulty}")
            return difficulty.title(), signals
    if any(term in haystack for term in ["10^5", "10**5", "large constraints"]):
        signals.append("large input constraint suggests optimized approach")
    if any(term in haystack for term in ["all possible", "every permutation", "hard"]):
        signals.append("combinatorial search wording")
    return "Unknown", signals


def _structural_cues(evidence: list[ClassificationEvidence]) -> list[str]:
    cues: list[str] = []
    for item in evidence:
        if item.cue_type not in cues:
            cues.append(item.cue_type)
    return cues[:6]


def _prerequisites(topic_id: str, pattern_id: str) -> list[str]:
    prereqs = list(DEFAULT_PREREQUISITES.get(topic_id, DEFAULT_PREREQUISITES["general"]))
    if pattern_id == "binary_search_answer":
        prereqs.append("Feasibility Function Design")
    if pattern_id in {"lis_dp", "knapsack_dp", "lcs_dp", "interval_dp", "digit_dp"}:
        prereqs.append("DP State Design")
    return prereqs


def _related_patterns(primary_pattern_id: str, secondary_pattern_ids: list[str]) -> list[str]:
    related = list(RELATED_PATTERNS.get(primary_pattern_id, []))
    for pattern_id in secondary_pattern_ids:
        label = PATTERN_LABELS[pattern_id]
        if label not in related:
            related.append(label)
    return related[:5]


def _subpatterns(pattern_id: str) -> list[str]:
    mapping = {
        "binary_search_answer": ["Monotonic Predicate", "Feasibility Check", "Boundary Search"],
        "boundary_search": ["Loop Invariant", "Boundary Search"],
        "decision_dp": ["1D DP", "Decision DP"],
        "knapsack_dp": ["0/1 Choice DP", "Capacity State"],
        "lis_dp": ["LIS-style DP", "Sorting", "Path Reconstruction"],
        "lcs_dp": ["2D DP", "Two-Sequence State"],
        "interval_dp": ["Interval State", "Split Point Enumeration"],
        "digit_dp": ["Position State", "Tight Bound"],
        "variable_window": ["Two Pointers", "Frequency Window"],
        "monotonic_stack": ["Monotonic Stack", "Nearest Greater/Smaller"],
        "stack_matching": ["Stack", "Delimiter Matching"],
        "graph_bfs": ["BFS", "Visited-State Management"],
        "graph_dfs": ["DFS", "Visited-State Management"],
        "shortest_path": ["Relaxation", "Priority Queue"],
        "topological_sort": ["In-Degree", "DAG Ordering"],
        "union_find": ["Disjoint Set Union", "Path Compression"],
        "hash_lookup": ["Hash Lookup", "Complement Search"],
        "frequency_counting": ["Frequency Counting", "Hash Map"],
        "prefix_sum_lookup": ["Prefix Sums", "Hash Lookup"],
        "choice_exploration": ["Choice Exploration", "Pruning"],
        "trie_prefix": ["Trie", "Prefix Search"],
        "linked_list_pointers": ["Fast/Slow Pointers", "Pointer Rewiring"],
        "interval_merge": ["Sorting", "Overlap Merge"],
        "greedy_sorting": ["Local Choice", "Exchange Argument"],
        "bitmasking": ["Bitmasking", "Set Representation"],
    }
    return mapping.get(pattern_id, ["Brute Force Baseline", "Optimization Search"])


def _reasoning(pattern_id: str, cues: list[str], confidence: float) -> str:
    cue_text = "; ".join(cues[:2]) if cues else "available statement evidence"
    return (
        f"Detected {PATTERN_LABELS[pattern_id]} from {cue_text}. "
        f"Confidence is {confidence:.2f}, so downstream systems should preserve uncertainty."
    )


def legacy_detect_problem_pattern(title: str, description: str) -> dict[str, Any]:
    haystack = f"{title} {description}".lower()
    for known_title, metadata in CURATED_PROBLEMS.items():
        if known_title in title.lower():
            topic_id = PATTERN_TO_TOPIC[metadata["primary_pattern"]]
            return {
                "difficulty": metadata["difficulty"],
                "pattern": TOPIC_LABELS[topic_id],
                "sub_patterns": deepcopy(metadata["subpatterns"]),
                "prerequisites": deepcopy(metadata["prerequisites"]),
                "reasoning": "Curated canonical problem metadata.",
            }
    keyword_map = {
        "Dynamic Programming": ["maximum", "minimum", "ways", "subsequence", "rob", "state", "memo"],
        "Graphs": ["graph", "node", "edge", "connected", "island", "shortest", "course"],
        "Sliding Window": ["substring", "subarray", "window", "longest", "at most", "contiguous"],
        "Binary Search": ["sorted", "search", "minimum capacity", "koko", "rotated", "monotonic"],
        "Trees": ["tree", "root", "ancestor", "traversal", "binary tree"],
        "Backtracking": ["permutation", "combination", "subset", "valid", "choices"],
        "Greedy": ["interval", "minimum number", "maximize", "locally", "jump"],
        "Hash Maps": ["frequency", "duplicate", "anagram", "two sum", "count"],
    }
    scores = Counter()
    for pattern, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword in haystack:
                scores[pattern] += 1
    pattern = scores.most_common(1)[0][0] if scores else "General Problem Solving"
    sub_patterns = {
        "Dynamic Programming": ["1D DP", "Decision DP"],
        "Graphs": ["Traversal", "Visited-State Management"],
        "Sliding Window": ["Two Pointers", "Frequency Window"],
        "Binary Search": ["Monotonic Predicate", "Boundary Search"],
        "Trees": ["DFS", "Recursive State"],
        "Backtracking": ["Choice Exploration", "Pruning"],
        "Greedy": ["Local Optimal Choice", "Exchange Argument"],
        "Hash Maps": ["Frequency Counting", "Constant-Time Lookup"],
    }.get(pattern, ["Brute Force Baseline", "Optimization Search"])
    prerequisites = {
        "Dynamic Programming": ["Recursion", "Memoization", "State Transitions"],
        "Graphs": ["DFS", "BFS", "Adjacency Modeling"],
        "Sliding Window": ["Two Pointers", "Hash Maps"],
        "Binary Search": ["Sorted Arrays", "Loop Invariants"],
        "Trees": ["Recursion", "Tree Traversal"],
    }.get(pattern, ["Complexity Analysis", "Edge Case Thinking"])
    difficulty = "Unknown"
    for token in ("easy", "medium", "hard"):
        if token in haystack:
            difficulty = token.title()
            break
    return {
        "difficulty": difficulty,
        "pattern": pattern,
        "sub_patterns": sub_patterns,
        "prerequisites": prerequisites,
        "reasoning": f"Detected {pattern} from recurring constraints and language in the prompt.",
    }
