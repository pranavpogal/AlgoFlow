from app.evaluation.code_review_eval import evaluate_code_review_cases


def test_code_review_eval_cases_pass_and_measure_baseline():
    result = evaluate_code_review_cases("../evals/code_review/cases.jsonl")

    assert result["case_count"] == 16
    assert result["passed"] == 16
    assert result["failed"] == []
    assert result["structured_output_validity_rate"] == 1
    assert result["rewrite_policy_compliance_rate"] == 1
    assert result["intent_satisfaction_rate"] == 1
    assert result["workflow_precision"] >= result["legacy_precision"]
