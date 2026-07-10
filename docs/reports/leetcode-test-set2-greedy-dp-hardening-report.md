# LeetCode Test Set 2 Greedy-vs-DP Hardening Report

## Scope

Use `evals/Leetcode tests/test_set2.md` to improve deterministic problem classification for Greedy-vs-DP, LIS, and weighted-interval confusion cases.

This is a controlled supplemental benchmark hardening step. It does not add live Gemini behavior, does not broaden ADK routing, and does not mutate the accepted deterministic CI baseline.

## Benchmark Coverage

Source file:

- `evals/Leetcode tests/test_set2.md`

Coverage:

- 24 total problems
- 12 Greedy-focused cases
- 12 Dynamic Programming, LIS, LCS, and weighted scheduling controls

Important discriminator examples:

- `55 Jump Game`: farthest reach greedy, not generic DP
- `45 Jump Game II`: greedy range expansion, not minimum-state DP
- `646 Maximum Length of Pair Chain`: unweighted interval scheduling greedy, despite longest-chain wording
- `376 Wiggle Subsequence`: greedy trend tracking, despite subsequence wording
- `122 Stock II`: accumulated positive gains, despite stock-DP surface language
- `322 Coin Change`: DP required because greedy largest-coin choice is invalid for arbitrary denominations
- `1235 Maximum Profit in Job Scheduling`: weighted interval DP, not earliest-finish greedy

## Baseline Observation Before Hardening

Pre-change exact match result:

```text
2 / 24 passed
```

Observed weaknesses:

- Greedy problems with `minimum`, `maximum`, or `longest` wording were often routed to DP or generic patterns.
- Several canonical Greedy patterns collapsed into the coarse `Greedy Sorting` label.
- Weighted interval and weighted LIS controls were confused with generic Greedy or generic LIS labels.
- Difficulty remained `Unknown` when it was not inferable from the prompt text alone.

## Architecture Changes

Extended canonical problem-number metadata in `CURATED_PROBLEMS_BY_NUMBER`:

- Greedy farthest reach
- Greedy level expansion
- Earliest finish time
- Interval endpoint greedy
- Greedy boundary expansion
- Opportunity-cost sorting
- Greedy two-pointer pairing
- Frequency-based greedy scheduling
- Greedy trend tracking
- Positive-gain stock greedy
- Circular take-or-skip DP
- Unbounded knapsack DP
- Prefix segmentation DP
- Prefix counting DP
- 0/1 knapsack
- LIS with binary-search optimization
- LIS count tracking
- Sort-and-reduce-to-LIS
- Weighted LIS
- Weighted interval scheduling
- Two-sequence DP

The metadata includes topic, canonical pattern, subpatterns, prerequisites, structural cues, related patterns, difficulty, and confidence.

## Evaluation Results

Focused supplemental tests:

```text
7 passed
```

LeetCode benchmark coverage now includes:

- `test_set1`: 20 / 20 passed
- `test_set2`: 24 / 24 passed

Full backend tests:

```text
113 passed, 5 warnings
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

- This phase primarily improves canonical problem-number classification.
- Numberless descriptions still need a dedicated statement-only benchmark before claiming broad Greedy-vs-DP generalization.
- The current pattern taxonomy still uses some broad internal IDs, while user-facing canonical labels are supplied through curated metadata.
- No live Gemini reasoning or model judge was introduced in this phase.

## Next Recommendation

Create a numberless Greedy-vs-DP test set where titles and problem numbers are omitted or anonymized. That will measure whether structural cues alone can distinguish Greedy, DP, LIS, and weighted scheduling patterns.
