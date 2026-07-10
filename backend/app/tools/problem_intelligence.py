from __future__ import annotations

from app.skills.problem_intelligence.workflow import (
    ProblemClassificationContext,
    classify_problem,
    legacy_detect_problem_pattern,
)

RELATED_PROBLEMS = {
    "Dynamic Programming": [
        {"number": 70, "title": "Climbing Stairs", "difficulty": "Easy", "variation": "base 1D recurrence"},
        {"number": 213, "title": "House Robber II", "difficulty": "Medium", "variation": "circular constraint"},
        {"number": 337, "title": "House Robber III", "difficulty": "Medium", "variation": "tree-shaped decisions"},
        {"number": 740, "title": "Delete and Earn", "difficulty": "Medium", "variation": "value compression into House Robber"},
    ],
    "Graphs": [
        {"number": 200, "title": "Number of Islands", "difficulty": "Medium", "variation": "grid DFS/BFS"},
        {"number": 207, "title": "Course Schedule", "difficulty": "Medium", "variation": "cycle detection"},
        {"number": 994, "title": "Rotting Oranges", "difficulty": "Medium", "variation": "multi-source BFS"},
    ],
    "Sliding Window": [
        {"number": 3, "title": "Longest Substring Without Repeating Characters", "difficulty": "Medium", "variation": "set-backed window"},
        {"number": 424, "title": "Longest Repeating Character Replacement", "difficulty": "Medium", "variation": "window with replacement budget"},
        {"number": 76, "title": "Minimum Window Substring", "difficulty": "Hard", "variation": "contracting requirement window"},
    ],
}


def detect_problem_pattern(
    title: str,
    description: str,
    problem_number: str | None = None,
    *,
    use_canonical_title_catalog: bool = False,
) -> dict:
    """Classify a problem with typed evidence while preserving legacy response keys."""
    return classify_problem(
        ProblemClassificationContext(
            title=title,
            description=description,
            problem_number=problem_number,
            use_canonical_title_catalog=use_canonical_title_catalog,
        )
    ).to_legacy_dict()


def recommend_related_problems(pattern: str) -> list[dict]:
    """Return curated related problems for a detected topic/pattern label."""
    return RELATED_PROBLEMS.get(
        pattern,
        [
            {"number": 1, "title": "Two Sum", "difficulty": "Easy", "variation": "hash lookup baseline"},
            {"number": 15, "title": "3Sum", "difficulty": "Medium", "variation": "sorting plus two pointers"},
        ],
    )


__all__ = ["detect_problem_pattern", "legacy_detect_problem_pattern", "recommend_related_problems"]
