from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4


class ReviewIntent(StrEnum):
    REVIEW_CODE = "REVIEW_CODE"
    FIND_BUG = "FIND_BUG"
    ONE_HINT = "ONE_HINT"
    EXPLAIN_FAILURE = "EXPLAIN_FAILURE"
    ANALYZE_COMPLEXITY = "ANALYZE_COMPLEXITY"
    SUGGEST_IMPROVEMENTS = "SUGGEST_IMPROVEMENTS"
    DO_NOT_REWRITE = "DO_NOT_REWRITE"
    PROVIDE_CORRECTED_CODE = "PROVIDE_CORRECTED_CODE"
    COMPARE_APPROACHES = "COMPARE_APPROACHES"


class FindingCategory(StrEnum):
    CORRECTNESS = "correctness"
    SYNTAX = "syntax"
    BOUNDARY = "boundary"
    DP_TRANSITION = "dp_transition"
    DP_BASE_CASE = "dp_base_case"
    BINARY_SEARCH_INVARIANT = "binary_search_invariant"
    GRAPH_VISITATION = "graph_visitation"
    MUTATION_DURING_ITERATION = "mutation_during_iteration"
    INTEGER_OVERFLOW = "integer_overflow"
    COMPLEXITY = "complexity"
    READABILITY = "readability"
    UNSUPPORTED_LANGUAGE = "unsupported_language"
    AMBIGUOUS = "ambiguous"


class FindingSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceType(StrEnum):
    AST_PARSE = "ast_parse"
    AST_PATTERN = "ast_pattern"
    TEXT_PATTERN = "text_pattern"
    STRUCTURAL_COUNT = "structural_count"
    LANGUAGE_CAPABILITY = "language_capability"
    INFERENCE = "inference"


@dataclass(frozen=True)
class CodeReviewContext:
    title: str
    language: str
    code: str
    problem_description: str | None = None
    user_intent: str | None = None
    learner_state: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FindingLocation:
    line_start: int | None = None
    line_end: int | None = None

    def to_dict(self) -> dict[str, int | None]:
        return {"line_start": self.line_start, "line_end": self.line_end}


@dataclass(frozen=True)
class CodeFinding:
    finding_id: str
    category: FindingCategory
    severity: FindingSeverity
    confidence: float
    evidence_type: EvidenceType
    evidence: str
    location: FindingLocation
    message: str
    pedagogical_action: str
    provenance: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "evidence_type": self.evidence_type.value,
            "evidence": self.evidence,
            "location": self.location.to_dict(),
            "message": self.message,
            "pedagogical_action": self.pedagogical_action,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class CodeReviewResult:
    intent: ReviewIntent
    language: str
    language_supported: bool
    analysis_layers: list[str]
    findings: list[CodeFinding]
    correctness: str
    time_complexity: str
    space_complexity: str
    edge_cases: list[str]
    optimization_opportunities: list[str]
    readability_feedback: list[str]
    alternative_approaches: list[str]
    suspected_mistakes: list[str]
    senior_engineer_summary: str
    corrected_code: str | None = None
    rewrite_allowed: bool = False
    unsupported_claims: list[str] = field(default_factory=list)


def review_code_workflow(context: CodeReviewContext) -> CodeReviewResult:
    language = normalize_language(context.language)
    intent = detect_review_intent(context.user_intent, context.code)
    rewrite_allowed = intent is ReviewIntent.PROVIDE_CORRECTED_CODE
    findings: list[CodeFinding] = []
    layers = ["intent_analysis", "language_detection"]
    unsupported_claims: list[str] = []

    if language == "python":
        layers.extend(["python_ast_parse", "python_ast_patterns", "structural_text_patterns"])
        findings.extend(_python_findings(context))
    elif language in {"java", "cpp", "c++", "javascript", "typescript", "go"}:
        layers.extend(["limited_text_patterns"])
        findings.extend(_limited_text_findings(context, language))
    else:
        layers.append("unsupported_language_notice")
        findings.append(
            _finding(
                FindingCategory.UNSUPPORTED_LANGUAGE,
                FindingSeverity.LOW,
                0.95,
                EvidenceType.LANGUAGE_CAPABILITY,
                f"Language '{context.language}' does not have a supported structural adapter in Phase 4B.",
                None,
                "This review is limited because AlgoFlow does not yet have a structural adapter for this language.",
                "Use the feedback as general mentoring guidance, not a correctness verdict.",
                "code_review_workflow.language_capability",
            )
        )

    findings = _dedupe_findings(findings)
    finding_categories = {finding.category for finding in findings}
    suspected_mistakes = [_mistake_label(finding) for finding in findings if finding.severity != FindingSeverity.INFO]

    correctness = _correctness_summary(findings, language)
    time_complexity = _time_complexity_summary(findings)
    space_complexity = _space_complexity_summary(context.code)
    edge_cases = _edge_cases(context.title, finding_categories)
    optimization_opportunities = _optimization_opportunities(findings, intent)
    readability_feedback = _readability_feedback(context, findings)
    alternative_approaches = _alternative_approaches(context.title, intent)
    senior_summary = _senior_summary(intent, findings, context.learner_state, rewrite_allowed)
    corrected_code = _corrected_code_stub(context, findings) if rewrite_allowed else None

    if language != "python":
        unsupported_claims.append("No AST-backed or execution-backed correctness claim for this language.")
    unsupported_claims.append("No learner code was executed; correctness remains evidence-limited.")

    return CodeReviewResult(
        intent=intent,
        language=language,
        language_supported=language == "python",
        analysis_layers=layers,
        findings=findings,
        correctness=correctness,
        time_complexity=time_complexity,
        space_complexity=space_complexity,
        edge_cases=edge_cases,
        optimization_opportunities=optimization_opportunities,
        readability_feedback=readability_feedback,
        alternative_approaches=alternative_approaches,
        suspected_mistakes=suspected_mistakes,
        senior_engineer_summary=senior_summary,
        corrected_code=corrected_code,
        rewrite_allowed=rewrite_allowed,
        unsupported_claims=unsupported_claims,
    )


def detect_review_intent(user_intent: str | None, code: str) -> ReviewIntent:
    text = (user_intent or "").lower()
    if "corrected code" in text or "fix my code" in text or "give corrected" in text:
        return ReviewIntent.PROVIDE_CORRECTED_CODE
    if "one hint" in text or "hint" in text:
        return ReviewIntent.ONE_HINT
    if "don't rewrite" in text or "do not rewrite" in text or "no rewrite" in text:
        return ReviewIntent.DO_NOT_REWRITE
    if "why" in text and ("fail" in text or "wrong" in text):
        return ReviewIntent.EXPLAIN_FAILURE
    if "find" in text and "bug" in text:
        return ReviewIntent.FIND_BUG
    if "complexity" in text or "big o" in text:
        return ReviewIntent.ANALYZE_COMPLEXITY
    if "improve" in text or "clean" in text or "readab" in text:
        return ReviewIntent.SUGGEST_IMPROVEMENTS
    if "compare" in text or "another approach" in text:
        return ReviewIntent.COMPARE_APPROACHES
    if not code.strip():
        return ReviewIntent.FIND_BUG
    return ReviewIntent.REVIEW_CODE


def normalize_language(language: str) -> str:
    lowered = language.strip().lower()
    aliases = {"py": "python", "python3": "python", "js": "javascript", "ts": "typescript", "c plus plus": "cpp"}
    return aliases.get(lowered, lowered)


def _python_findings(context: CodeReviewContext) -> list[CodeFinding]:
    findings: list[CodeFinding] = []
    try:
        tree = ast.parse(context.code)
    except SyntaxError as exc:
        return [
            _finding(
                FindingCategory.SYNTAX,
                FindingSeverity.HIGH,
                0.99,
                EvidenceType.AST_PARSE,
                exc.msg,
                exc.lineno,
                "Python could not parse this submission, so correctness review must stop at the syntax issue.",
                "Fix the syntax first, then rerun review for logic feedback.",
                "python.ast.parse",
            )
        ]

    findings.extend(_python_boundary_findings(tree, context.code))
    findings.extend(_python_dp_findings(tree, context))
    findings.extend(_python_mutation_findings(tree))
    findings.extend(_structural_findings(context.code, "python"))
    if not findings and context.code.strip():
        findings.append(
            _finding(
                FindingCategory.CORRECTNESS,
                FindingSeverity.INFO,
                0.55,
                EvidenceType.AST_PARSE,
                "Python parsed successfully and no Phase 4B structural risk pattern matched.",
                None,
                "No deterministic issue was found, but this is not a proof of correctness.",
                "Validate with boundary cases and explain the invariant aloud.",
                "python.ast.parse+code_review_workflow",
            )
        )
    return findings


def _python_boundary_findings(tree: ast.AST, code: str) -> list[CodeFinding]:
    findings: list[CodeFinding] = []
    lines = code.splitlines()
    len_bound_names = _names_assigned_len(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.BinOp):
            if _is_minus_index(node.slice):
                evidence = _line(lines, node.lineno)
                findings.append(
                    _finding(
                        FindingCategory.BOUNDARY,
                        FindingSeverity.HIGH,
                        0.86,
                        EvidenceType.AST_PATTERN,
                        evidence,
                        node.lineno,
                        "This index can become negative unless earlier base cases or loop bounds prevent it.",
                        "State what happens at the first one or two iterations before writing the recurrence.",
                        "python.ast.Subscript",
                    )
                )
        if isinstance(node, ast.Compare):
            if any(isinstance(op, (ast.LtE, ast.GtE)) for op in node.ops) and any(_mentions_len(part) for part in [node.left, *node.comparators]):
                findings.append(
                    _finding(
                        FindingCategory.BOUNDARY,
                        FindingSeverity.MEDIUM,
                        0.72,
                        EvidenceType.AST_PATTERN,
                        _line(lines, node.lineno),
                        node.lineno,
                        "Inclusive comparison with len(...) often needs a boundary check because the last valid index is len(...) - 1.",
                        "Test the smallest and largest valid index explicitly.",
                        "python.ast.Compare",
                    )
                )
            compared_names = {_node_name(part) for part in [node.left, *node.comparators]}
            if any(isinstance(op, (ast.LtE, ast.GtE)) for op in node.ops) and len_bound_names.intersection(
                name for name in compared_names if name
            ):
                findings.append(
                    _finding(
                        FindingCategory.BOUNDARY,
                        FindingSeverity.MEDIUM,
                        0.74,
                        EvidenceType.AST_PATTERN,
                        _line(lines, node.lineno),
                        node.lineno,
                        "An inclusive comparison uses a variable initialized to len(...), which can point one past the last valid index.",
                        "Decide whether the interval is closed [left, right] or half-open [left, right) and keep updates consistent.",
                        "python.ast.Assign+python.ast.Compare",
                    )
                )
    return findings


def _python_dp_findings(tree: ast.AST, context: CodeReviewContext) -> list[CodeFinding]:
    findings: list[CodeFinding] = []
    code = context.code.lower()
    lines = context.code.splitlines()
    if "dp" not in code:
        return findings

    has_base_case = any(token in code for token in ["dp[0]", "dp[1]", "prev", "if len", "if not"])
    if not has_base_case:
        line = _first_line_containing(lines, "dp")
        findings.append(
            _finding(
                FindingCategory.DP_BASE_CASE,
                FindingSeverity.MEDIUM,
                0.78,
                EvidenceType.TEXT_PATTERN,
                _line(lines, line) if line else "DP state appears without visible base-case handling.",
                line,
                "The DP state is introduced without clear base cases for the smallest inputs.",
                "Write the answer for n = 0, n = 1, and n = 2 before the loop.",
                "code_review_workflow.dp_base_case",
            )
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and _subscript_name(node) == "dp" and isinstance(node.slice, ast.BinOp):
            if _binop_minus_constant(node.slice, 1) and "house robber" in context.title.lower():
                findings.append(
                    _finding(
                        FindingCategory.DP_TRANSITION,
                        FindingSeverity.HIGH,
                        0.76,
                        EvidenceType.AST_PATTERN,
                        _line(lines, node.lineno),
                        node.lineno,
                        "For House Robber, using the immediately previous house in the rob branch can violate the non-adjacent constraint.",
                        "Separate the skip choice from the rob choice: what previous state is compatible with robbing the current house?",
                        "python.ast.Subscript+problem_title",
                    )
                )
    return findings


def _python_mutation_findings(tree: ast.AST) -> list[CodeFinding]:
    findings: list[CodeFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Name):
            iter_name = node.iter.id
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name) and child.func.value.id == iter_name:
                        if child.func.attr in {"append", "remove", "pop", "clear", "extend", "insert"}:
                            findings.append(
                                _finding(
                                    FindingCategory.MUTATION_DURING_ITERATION,
                                    FindingSeverity.MEDIUM,
                                    0.85,
                                    EvidenceType.AST_PATTERN,
                                    f"{iter_name}.{child.func.attr}(...) inside loop over {iter_name}",
                                    child.lineno,
                                    "The collection being iterated is mutated inside the loop, which can skip elements or create unstable traversal.",
                                    "Iterate over a copy or accumulate changes separately, then apply them after the loop.",
                                    "python.ast.For+python.ast.Call",
                                )
                            )
    return findings


def _limited_text_findings(context: CodeReviewContext, language: str) -> list[CodeFinding]:
    findings = _structural_findings(context.code, language)
    lowered = context.code.lower()
    if language in {"java", "cpp", "c++"} and re.search(r"\bint\s+\w+", context.code) and any(op in context.code for op in ["+", "*"]):
        findings.append(
            _finding(
                FindingCategory.INTEGER_OVERFLOW,
                FindingSeverity.MEDIUM,
                0.66,
                EvidenceType.TEXT_PATTERN,
                "Uses int arithmetic in a submission with additive or multiplicative operations.",
                None,
                "Integer overflow may be possible if constraints allow large accumulated values.",
                "Check constraints and consider long/long long only if values can exceed 32-bit range.",
                f"limited_text_adapter.{language}",
            )
        )
    if "visited" in lowered and "graph" in lowered and "add" not in lowered:
        findings.append(
            _finding(
                FindingCategory.GRAPH_VISITATION,
                FindingSeverity.MEDIUM,
                0.62,
                EvidenceType.TEXT_PATTERN,
                "Graph traversal mentions visited without an obvious add/mark operation.",
                None,
                "The visited-state update may be missing or delayed, which can revisit nodes or loop on cycles.",
                "Mark a node when it enters the frontier unless your invariant requires a different timing.",
                f"limited_text_adapter.{language}",
            )
        )
    if not findings:
        findings.append(
            _finding(
                FindingCategory.UNSUPPORTED_LANGUAGE,
                FindingSeverity.INFO,
                0.9,
                EvidenceType.LANGUAGE_CAPABILITY,
                f"{language} has only limited text-pattern review in Phase 4B.",
                None,
                "No deterministic issue matched, but this language is not structurally analyzed yet.",
                "Use this as a mentoring pass and add language-specific adapter coverage before relying on it.",
                f"limited_text_adapter.{language}",
            )
        )
    return findings


def _structural_findings(code: str, language: str) -> list[CodeFinding]:
    findings: list[CodeFinding] = []
    lowered = code.lower()
    loop_count = len(re.findall(r"\b(for|while)\b", lowered))
    if loop_count >= 2:
        findings.append(
            _finding(
                FindingCategory.COMPLEXITY,
                FindingSeverity.LOW,
                0.64,
                EvidenceType.STRUCTURAL_COUNT,
                f"Detected {loop_count} loop keywords.",
                None,
                "Multiple loops may still be linear, but nested or repeated traversal should be justified against constraints.",
                "State whether the loops are nested, sequential, or amortized.",
                f"structural_text_patterns.{language}",
            )
        )
    if any(token in lowered for token in ["while left", "while l", "binary"]):
        findings.append(
            _finding(
                FindingCategory.BINARY_SEARCH_INVARIANT,
                FindingSeverity.MEDIUM,
                0.58,
                EvidenceType.TEXT_PATTERN,
                "Binary-search-like loop detected from textual markers.",
                None,
                "Binary search correctness depends on matching loop condition, mid update, and return invariant.",
                "Write the invariant: what does the search interval still contain after each update?",
                f"structural_text_patterns.{language}",
            )
        )
    if len(code.strip()) < 20:
        findings.append(
            _finding(
                FindingCategory.AMBIGUOUS,
                FindingSeverity.INFO,
                0.8,
                EvidenceType.STRUCTURAL_COUNT,
                "Submission is too short for meaningful structural review.",
                None,
                "There is not enough code to make a grounded review finding.",
                "Paste the full function or explain the missing context.",
                f"structural_text_patterns.{language}",
            )
        )
    return findings


def _finding(
    category: FindingCategory,
    severity: FindingSeverity,
    confidence: float,
    evidence_type: EvidenceType,
    evidence: str,
    line: int | None,
    message: str,
    pedagogical_action: str,
    provenance: str,
) -> CodeFinding:
    return CodeFinding(
        finding_id=f"finding_{uuid4().hex[:12]}",
        category=category,
        severity=severity,
        confidence=round(confidence, 2),
        evidence_type=evidence_type,
        evidence=evidence,
        location=FindingLocation(line, line),
        message=message,
        pedagogical_action=pedagogical_action,
        provenance=provenance,
    )


def _dedupe_findings(findings: list[CodeFinding]) -> list[CodeFinding]:
    seen: set[tuple[str, str, int | None]] = set()
    deduped: list[CodeFinding] = []
    for finding in findings:
        key = (finding.category.value, finding.evidence, finding.location.line_start)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped[:8]


def _is_minus_index(node: ast.BinOp) -> bool:
    return isinstance(node.op, ast.Sub) and isinstance(node.right, ast.Constant) and isinstance(node.right.value, int)


def _binop_minus_constant(node: ast.BinOp, value: int) -> bool:
    return isinstance(node.op, ast.Sub) and isinstance(node.right, ast.Constant) and node.right.value == value


def _mentions_len(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len"


def _names_assigned_len(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _mentions_len(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Tuple):
            for target in node.targets:
                if not isinstance(target, ast.Tuple):
                    continue
                for tuple_target, tuple_value in zip(target.elts, node.value.elts, strict=False):
                    if isinstance(tuple_target, ast.Name) and _mentions_len(tuple_value):
                        names.add(tuple_target.id)
        if isinstance(node, ast.AnnAssign) and node.value is not None and _mentions_len(node.value):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
    return names


def _node_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return None


def _subscript_name(node: ast.Subscript) -> str | None:
    if isinstance(node.value, ast.Name):
        return node.value.id
    return None


def _line(lines: list[str], line: int | None) -> str:
    if line is None or line < 1 or line > len(lines):
        return ""
    return lines[line - 1].strip()


def _first_line_containing(lines: list[str], token: str) -> int | None:
    for index, line in enumerate(lines, start=1):
        if token in line:
            return index
    return None


def _mistake_label(finding: CodeFinding) -> str:
    labels = {
        FindingCategory.SYNTAX: "Syntax issue",
        FindingCategory.BOUNDARY: "Off-by-one / boundary handling",
        FindingCategory.DP_TRANSITION: "DP transition mistake",
        FindingCategory.DP_BASE_CASE: "DP initialization clarity",
        FindingCategory.BINARY_SEARCH_INVARIANT: "Binary search boundary reasoning",
        FindingCategory.GRAPH_VISITATION: "Graph visitation update timing",
        FindingCategory.MUTATION_DURING_ITERATION: "Mutation during iteration",
        FindingCategory.INTEGER_OVERFLOW: "Integer overflow risk",
        FindingCategory.COMPLEXITY: "Complexity needs justification",
        FindingCategory.UNSUPPORTED_LANGUAGE: "Unsupported or limited language analysis",
        FindingCategory.AMBIGUOUS: "Ambiguous submission",
    }
    return labels.get(finding.category, finding.category.value)


def _correctness_summary(findings: list[CodeFinding], language: str) -> str:
    if any(f.category == FindingCategory.SYNTAX for f in findings):
        return "Not reviewable beyond syntax until the parse error is fixed"
    high = [f for f in findings if f.severity == FindingSeverity.HIGH]
    if high:
        return "Likely incorrect or incomplete based on high-confidence static evidence"
    if language != "python":
        return "Limited review only; no structural correctness claim for this language"
    if all(f.severity == FindingSeverity.INFO for f in findings):
        return "No deterministic issue found, but correctness is not proven without tests"
    return "Needs test-backed validation; static evidence found possible risks"


def _time_complexity_summary(findings: list[CodeFinding]) -> str:
    if any(f.category == FindingCategory.COMPLEXITY for f in findings):
        return "Potentially O(n^2) or higher; justify loop nesting against constraints"
    return "No nested-loop risk detected by Phase 4B static checks; verify against constraints"


def _space_complexity_summary(code: str) -> str:
    lowered = code.lower()
    if any(token in lowered for token in ["dp", "set(", "dict(", "{}", "[]"]):
        return "Uses auxiliary state; likely O(n) unless bounded by input-independent variables"
    return "No obvious auxiliary collection detected; verify recursion stack and hidden allocations"


def _edge_cases(title: str, categories: set[FindingCategory]) -> list[str]:
    cases = ["Empty or minimum-size input", "Single-element input", "Duplicate values or ties", "Maximum constraints"]
    if FindingCategory.BOUNDARY in categories or FindingCategory.DP_BASE_CASE in categories:
        cases.insert(1, "First two iterations / base cases")
    if "house robber" in title.lower():
        cases.append("Adjacent houses with equal values")
    return cases


def _optimization_opportunities(findings: list[CodeFinding], intent: ReviewIntent) -> list[str]:
    items = ["Name the loop invariant or DP state in one sentence"]
    if any(f.category in {FindingCategory.DP_BASE_CASE, FindingCategory.DP_TRANSITION} for f in findings):
        items.append("Check whether rolling state can replace a full DP array after correctness is fixed")
    if intent is ReviewIntent.ANALYZE_COMPLEXITY:
        items.append("Separate asymptotic analysis from constant-factor cleanup")
    return items


def _readability_feedback(context: CodeReviewContext, findings: list[CodeFinding]) -> list[str]:
    feedback = [f"Use idiomatic {context.language} names for state variables"]
    if any(f.category == FindingCategory.AMBIGUOUS for f in findings):
        feedback.append("Paste a complete function so feedback can be grounded in evidence")
    else:
        feedback.append("Add a short comment describing the invariant of the main loop")
    return feedback


def _alternative_approaches(title: str, intent: ReviewIntent) -> list[str]:
    approaches = ["Brute-force baseline for explanation", "Optimized pattern-based approach"]
    if "house robber" in title.lower():
        approaches.append("Rolling two-variable DP after base cases are clear")
    if intent is ReviewIntent.COMPARE_APPROACHES:
        approaches.append("Compare recursive memoization against bottom-up iteration")
    return approaches


def _senior_summary(
    intent: ReviewIntent, findings: list[CodeFinding], learner_state: dict[str, Any], rewrite_allowed: bool
) -> str:
    if intent is ReviewIntent.ONE_HINT:
        return "Smallest useful hint: focus on the first failing boundary or invariant before changing the whole solution."
    if intent is ReviewIntent.DO_NOT_REWRITE:
        return "I will not rewrite your code; the priority is to isolate the failure mechanism and let you make the fix."
    if rewrite_allowed:
        return "Corrected-code help is allowed by the request, but the root cause still matters more than the patch."
    confidence = learner_state.get("confidence", "unknown")
    if confidence in {"medium", "high"} and learner_state.get("weak_topics"):
        first_topic = learner_state["weak_topics"][0]
        topic = first_topic.get("topic", "the relevant pattern") if isinstance(first_topic, dict) else str(first_topic)
        return f"Review priority: connect this finding back to your recent evidence around {topic}."
    if not findings or all(f.severity == FindingSeverity.INFO for f in findings):
        return "No deterministic blocker was found; now prove the invariant and run boundary tests."
    return "The next best step is to fix the highest-severity finding, then rerun edge cases before optimizing."


def _corrected_code_stub(context: CodeReviewContext, findings: list[CodeFinding]) -> str | None:
    if normalize_language(context.language) != "python":
        return None
    if not any(f.category in {FindingCategory.DP_BASE_CASE, FindingCategory.DP_TRANSITION, FindingCategory.BOUNDARY} for f in findings):
        return None
    if "house robber" not in context.title.lower():
        return None
    return (
        "def rob(nums):\n"
        "    if not nums:\n"
        "        return 0\n"
        "    prev_two = 0\n"
        "    prev_one = 0\n"
        "    for value in nums:\n"
        "        prev_two, prev_one = prev_one, max(prev_one, prev_two + value)\n"
        "    return prev_one"
    )
