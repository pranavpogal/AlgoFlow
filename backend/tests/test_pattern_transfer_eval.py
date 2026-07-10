from app.evaluation.pattern_transfer_eval import evaluate_pattern_transfer_cases


def test_pattern_transfer_eval_passes_and_tracks_shortcuts():
    result = evaluate_pattern_transfer_cases("../evals/pattern_transfer/cases.jsonl")

    assert result["case_count"] == 15
    assert result["passed"] == 15
    assert result["failed"] == []
    assert result["new_metrics"]["recommendation_relevance"] >= result["baseline_metrics"]["same_topic_relevance"]
    assert result["same_topic_shortcut_rate"] == 0
    assert result["unsupported_claim_rate"] == 0
    assert result["provenance_completeness"] == 1
    assert result["structured_output_validity"] == 1
