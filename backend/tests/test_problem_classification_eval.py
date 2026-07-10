from app.evaluation.problem_classification_eval import evaluate_problem_classification_cases


def test_problem_classification_eval_passes_and_beats_legacy_baseline():
    result = evaluate_problem_classification_cases("../evals/problem_classification/cases.jsonl")

    assert result["case_count"] == 30
    assert result["passed"] == 30
    assert result["failed"] == []
    assert result["new_metrics"]["primary_topic_accuracy"] > result["baseline_metrics"]["primary_topic_accuracy"]
    assert result["new_metrics"]["pattern_precision"] > result["baseline_metrics"]["pattern_precision"]
    assert result["unsupported_claim_rate"] == 0
    assert result["provenance_completeness_rate"] == 1
    assert result["structured_output_validity_rate"] == 1
    assert result["calibration_findings"]["overconfident_ambiguous_cases"] == []
