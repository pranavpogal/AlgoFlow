from app.tools.code_review import review_code_heuristics


def test_review_detects_boundary_risk():
    code = "for i in range(len(nums)):\n    if i + 1 <= len(nums): pass"
    result = review_code_heuristics("Python", code)
    assert "Off-by-one / boundary handling" in result["suspected_mistakes"]
