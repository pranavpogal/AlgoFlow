# ADK Tool Orchestration Evaluation

Status: Current
Owner: AlgoFlow
Suite: `adk_tool_orchestration`

## Purpose

Evaluate the first real tool-orchestrated ADK workflow without granting direct tool execution to ADK.

## Cases

Dataset: `evals/adk_tool_orchestration/cases.jsonl`

Current cases:

- `adk_tool_detect_allowed`: mocked ADK requests `problem.detect_pattern`; gateway allows and completes it.
- `adk_related_denied_in_hint_mode`: mocked ADK requests `problem.related_problems` during `next_hint`; semantic policy denies it.
- `adk_disabled_default_detect_preserved`: live ADK disabled; deterministic fallback still creates the default detect-pattern request.
- `adk_related_allowed_for_recommendations`: mocked ADK requests `problem.related_problems` during `recommendations`; semantic policy allows it.
- `adk_recommendations_disabled_no_tool_bypass`: live ADK disabled; recommendation route does not call raw recommendation fallback.
- `adk_related_allowed_for_pattern_transfer`: mocked ADK requests `problem.related_problems` during `pattern_transfer`; semantic policy allows it.
- `adk_pattern_transfer_disabled_no_tool_bypass`: live ADK disabled; pattern-transfer route does not call raw pattern-transfer fallback.
- `adk_code_review_static_allowed`: mocked ADK requests `code.review_static` during `code_review`; semantic policy allows it and the deterministic static review workflow runs through the gateway.
- `adk_code_review_disabled_no_tool_bypass`: live ADK disabled; code-review routing does not call the raw code-review fallback without an approved tool request.

## Metrics

- `tool_request_execution_accuracy`
- `tool_policy_enforcement_accuracy`
- `tool_trajectory_coverage`
- `tool_fallback_non_bypass_accuracy`

All four metrics have blocking threshold `>= 1.0` in the explicit suite.

## CI Role

The suite is blocking in GitHub Actions:

```bash
cd backend
python -m app.evaluation.cli run --suite adk_tool_orchestration
```

It is intentionally not part of `--suite all`, preserving the accepted deterministic baseline contract.

## Known Limits

- CI uses mocked ADK decisions, not live Gemini calls.
- Only the narrow `/mentor/route` slice is evaluated.
- The suite verifies event presence and policy outcomes, not broad model quality.
- Three tool IDs are in scope: `problem.detect_pattern`, `problem.related_problems`, and `code.review_static`.
- Recommendation and pattern-transfer routing currently require an explicit related-problems tool request.
- Governed code-review routing currently requires an explicit static-review tool request.
- The static code-review tool does not execute learner code and does not prove runtime correctness.
