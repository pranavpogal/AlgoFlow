from app.tools.problem_intelligence import detect_problem_pattern, recommend_related_problems


def test_detects_house_robber_as_dp():
    result = detect_problem_pattern("House Robber", "Find the maximum amount you can rob using memo state")
    assert result["pattern"] == "Dynamic Programming"
    assert "1D DP" in result["sub_patterns"]


def test_recommendations_have_progression():
    related = recommend_related_problems("Dynamic Programming")
    assert related[0]["number"] == 70
    assert any(item["title"] == "House Robber II" for item in related)


def test_detects_largest_divisible_subset_as_lis_style_dp():
    result = detect_problem_pattern(
        "Largest Divisible Subset",
        "Given a set of distinct positive integers nums, return the largest subset answer "
        "such that every pair is divisible.",
    )
    assert result["difficulty"] == "Medium"
    assert result["pattern"] == "Dynamic Programming"
    assert result["sub_patterns"] == ["LIS-style DP", "Sorting", "Path Reconstruction"]
