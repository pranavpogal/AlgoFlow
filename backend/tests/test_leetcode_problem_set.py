from app.evaluation.leetcode_problem_set import (
    evaluate_leetcode_problem_set,
    load_leetcode_markdown_cases,
)


LEETCODE_SET_1 = "../evals/Leetcode tests/test_set1.md"
LEETCODE_SET_2 = "../evals/Leetcode tests/test_set2.md"


def test_leetcode_markdown_test_set_loads_all_cases():
    cases = load_leetcode_markdown_cases(LEETCODE_SET_1)

    assert len(cases) == 20
    assert cases[0]["problem_number"] == "1"
    assert cases[0]["title"] == "Two Sum"
    assert cases[0]["expected_sub_patterns"] == ["Complement Search", "One-Pass Hashing"]


def test_leetcode_test_set1_classification_contract():
    result = evaluate_leetcode_problem_set(LEETCODE_SET_1)

    assert result["case_count"] == 20
    assert result["passed"] == 20
    assert result["failed"] == []
    assert result["metrics"]["difficulty_accuracy"] == 1
    assert result["metrics"]["topic_accuracy"] == 1
    assert result["metrics"]["pattern_accuracy"] == 1
    assert result["metrics"]["subpatterns_accuracy"] == 1
    assert result["metrics"]["prerequisites_accuracy"] == 1
    assert result["metrics"]["provenance_accuracy"] == 1


def test_leetcode_test_set2_greedy_dp_classification_contract():
    result = evaluate_leetcode_problem_set(LEETCODE_SET_2)

    assert result["case_count"] == 24
    assert result["passed"] == 24
    assert result["failed"] == []
    assert result["metrics"]["difficulty_accuracy"] == 1
    assert result["metrics"]["topic_accuracy"] == 1
    assert result["metrics"]["pattern_accuracy"] == 1
    assert result["metrics"]["subpatterns_accuracy"] == 1
    assert result["metrics"]["prerequisites_accuracy"] == 1
    assert result["metrics"]["provenance_accuracy"] == 1


def test_leetcode_test_set2_title_only_greedy_dp_contract():
    result = evaluate_leetcode_problem_set(LEETCODE_SET_2, use_problem_number=False)

    assert result["case_count"] == 24
    assert result["passed"] == 24
    assert result["failed"] == []
    assert result["metrics"]["difficulty_accuracy"] == 1
    assert result["metrics"]["topic_accuracy"] == 1
    assert result["metrics"]["pattern_accuracy"] == 1
