# Title Canonical Classification Fix Report

## Scope

Address poor Greedy problem classification when users provide a known LeetCode title but omit or inconsistently use the problem number.

## Root Cause

The previous Greedy-vs-DP hardening improved `problem_number`-keyed canonical metadata, but title-only classification still fell back to broad deterministic rules.

Observed diagnostic before this fix:

```text
test_set2 title-only exact match: 0 / 24
```

This meant the Analyze page could still perform poorly if the problem number was missing, even for canonical titles like `Jump Game`, `Task Scheduler`, or `Maximum Profit in Job Scheduling`.

## Changes

Added a controlled canonical title catalog:

- Exact title to problem-number mapping for benchmarked LeetCode problems
- Opt-in via `ProblemClassificationContext.use_canonical_title_catalog`
- Keeps accepted baseline and legacy helper behavior unchanged by default

Updated supplemental evaluation:

- `evaluate_leetcode_problem_set(..., use_problem_number=False)` now verifies title-only classification
- `test_set2` must pass even when problem numbers are omitted

Updated user-facing Analyze path:

- `mentor_service.analyze_problem` now passes `payload.problem_number`
- The Analyze path explicitly opts into canonical title matching

## Results

Focused tests:

```text
10 passed
```

Full backend tests:

```text
114 passed, 5 warnings
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

## Known Limitations

- This fixes exact canonical title recognition, not fully anonymized statement-only reasoning.
- If users paste a problem with no number and a modified/non-canonical title, generic rules can still be weaker than Gemini or curated metadata.
- The next useful benchmark should remove both problem numbers and titles to test pure statement-level Greedy-vs-DP reasoning.
