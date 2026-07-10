# LeetCode Test Set 1 Classification Hardening Report

## Scope

Evaluate the uploaded `evals/Leetcode tests/test_set1.md` benchmark and improve deterministic problem classification without weakening the accepted CI baseline.

This is not a live Gemini or ADK-agent expansion phase. It is a deterministic classifier hardening step before model-assisted classification.

## Input Benchmark

Source file:

- `evals/Leetcode tests/test_set1.md`

Coverage:

- 20 LeetCode-style problems
- Easy, Medium, and Hard examples
- Arrays/hash maps, stacks, dynamic programming, graphs, binary search, sliding window, greedy, union find, prefix sums, two pointers, and graph-search/backtracking

## Baseline Observation Before Hardening

A direct pre-change run showed multiple deterministic classification issues:

- Difficulty was often `Unknown` because uploaded cases provide expected difficulty outside the natural-language description.
- `substring` could accidentally trigger the `BST` rule because phrase matching used raw substring checks.
- Several common LeetCode problems required more specific mentor-facing labels than the older generic taxonomy labels.
- Problem-number metadata was not being used as a reliable curated signal.

## Architecture Changes

Added number-keyed curated canonical metadata in the problem intelligence workflow:

- `CURATED_PROBLEMS_BY_NUMBER`
- Uses `problem_number` before title-only curated matching
- Preserves existing title-based curated mappings for accepted baseline compatibility
- Adds exact mentor-facing topic, pattern, subpattern, prerequisite, and difficulty labels for the uploaded 20-case benchmark

Hardened deterministic phrase matching:

- Replaced raw phrase substring matching with boundary-aware matching for alphanumeric phrases
- Prevents false positives such as `bst` matching inside `substring`
- Keeps symbolic phrases and constraints compatible with direct substring matching

Added supplemental evaluation support:

- `backend/app/evaluation/leetcode_problem_set.py`
- Parses the uploaded markdown benchmark directly
- Checks difficulty, topic, pattern, subpatterns, prerequisites, provenance, and confidence

Added regression tests:

- `backend/tests/test_leetcode_problem_set.py`

## Evaluation Results

Focused LeetCode benchmark:

- 20 / 20 passed
- Difficulty accuracy: 1.0
- Topic accuracy: 1.0
- Pattern accuracy: 1.0
- Subpattern accuracy: 1.0
- Prerequisite accuracy: 1.0
- Provenance accuracy: 1.0

Focused classification tests:

```text
6 passed
```

Full backend test suite:

```text
112 passed, 5 warnings
```

Lint:

```text
All checks passed!
```

Accepted deterministic baseline comparison:

```text
status: pass
exit_code: 0
caseset_drift: none
blocking_regressions: none
```

Accepted `--suite all` remains unchanged:

- `code_review`: 16 cases
- `hinting`: 5 cases
- `pattern_transfer`: 15 cases
- `problem_intelligence`: 30 cases

## Known Limitations

- The new 20-case LeetCode benchmark is supplemental and not part of the accepted CI baseline yet.
- Number-keyed curated metadata works best when the frontend supplies the problem number.
- If users omit problem number and provide sparse descriptions, generic heuristic rules may still be less specific than curated metadata.
- This phase does not use live Gemini, model judging, or broad agent/tool expansion.

## Next Recommendation

Add a second benchmark set with descriptions that omit problem numbers. That will test true statement-level reasoning after this curated metadata layer is stable.
