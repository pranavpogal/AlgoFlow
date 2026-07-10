from __future__ import annotations


def review_code_heuristics(language: str, code: str) -> dict:
    """Static mentoring heuristics that complement the LLM review agent."""
    lowered = code.lower()
    mistakes: list[str] = []
    if any(token in lowered for token in ["range(len", "i+1", "i - 1", "<="]):
        mistakes.append("Off-by-one / boundary handling")
    if "dp" in lowered and not any(token in lowered for token in ["dp[0]", "base", "prev"]):
        mistakes.append("DP initialization clarity")
    if any(token in lowered for token in ["while left", "while l", "binary"]):
        mistakes.append("Binary search boundary reasoning")
    if "visited" in lowered and "graph" in lowered and "add" not in lowered:
        mistakes.append("Graph visitation update timing")

    nested_loop = code.count("for ") + code.count("while ") >= 2
    complexity = "O(n^2) or higher, verify nested iteration bounds" if nested_loop else "O(n) or O(log n), verify with constraints"
    return {
        "correctness": "Needs test-backed validation" if mistakes else "Likely correct pending edge-case tests",
        "time_complexity": complexity,
        "space_complexity": "Depends on auxiliary structures; appears O(n) unless optimized variables are used",
        "edge_cases": [
            "Empty input or minimum constraint size",
            "Single-element input",
            "Duplicate values or ties",
            "Maximum constraints and integer growth",
        ],
        "optimization_opportunities": [
            "State whether each data structure is essential",
            "Look for rolling-state compression when only previous DP states are needed",
        ],
        "readability_feedback": [
            f"Use idiomatic {language} names for state variables",
            "Add a short invariant comment for the core loop",
        ],
        "alternative_approaches": ["Brute-force baseline for explanation", "Optimized pattern-based approach"],
        "suspected_mistakes": mistakes,
    }
