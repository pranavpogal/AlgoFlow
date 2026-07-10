from app.evaluation.hint_eval import evaluate_hint_cases


def test_hint_eval_cases_have_no_leakage_failures():
    result = evaluate_hint_cases("../evals/hint_leakage/cases.jsonl")

    assert result["case_count"] == 5
    assert result["failed"] == []
