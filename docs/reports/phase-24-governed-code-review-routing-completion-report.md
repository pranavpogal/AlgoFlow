# Phase 24 Completion Report: Governed Code Review Capability Routing

Status: Complete
Owner: AlgoFlow
Date: 2026-07-10

## Objective

Extend the narrow ADK route from problem analysis, hinting, recommendations, and pattern transfer to one additional governed capability: code review. Preserve deterministic workflows, no-execution code review boundaries, semantic policy, trajectory capture, policy-decision records, and accepted-baseline stability.

## Architecture Changes

- Extended `CoordinatorCapability` to include `code_review`.
- Extended `CoordinatorToolId` to include `code.review_static`.
- Extended `MentorRouteRequest` with route-level `language`, `code`, and `problem_description` fields.
- Updated deterministic routing to select `code_review_workflow` for explicit code-review requests or review-oriented messages.
- Added `code.review_static` to `ToolGateway` as a medium-risk draft tool.
- Routed `code.review_static` through the deterministic static code-review workflow without executing learner code.
- Added semantic policy allowlists for `code_review` capability, `CODE_REVIEW` intent, and `CODE_REVIEW` mentoring mode.
- Added governed code-review response assembly from gateway output.
- Added safe code-review fallback when no approved static-review tool request exists.
- Preserved legacy `/code-review` compatibility behavior outside the governed `/mentor/route` path.

## Runtime Paths

Allowed governed code-review path:

```text
ADK coordinator decision
  -> selected_capability: code_review
  -> tool_requests: code.review_static
  -> ADK_TOOL_REQUESTED
  -> structural allow: tool.draft.allowed
  -> semantic allow: INTENT_ALIGNED
  -> TOOL_CALL_COMPLETED
  -> deterministic static code-review workflow
  -> CodeReviewResponse
  -> code-review learning events and vector-memory note
```

No-tool fallback path:

```text
ENABLE_LIVE_ADK=false or no tool request
  -> selected_capability: code_review
  -> no code.review_static execution
  -> safe CodeReviewResponse explaining that no governed review was performed
```

Denied drift path remains:

```text
selected_capability or mentoring mode does not match code_review
  -> tool_requests: code.review_static
  -> semantic deny
  -> TOOL_CALL_DENIED
  -> no raw code-review bypass
```

## Trajectory And Policy Schema

No schema version change was required. Existing trajectory and policy-decision records now cover the new tool ID.

Representative trajectory events for the allowed path:

- `REQUEST_RECEIVED`
- `ADK_AGENT_BUILT`
- `ADK_INVOCATION_STARTED`
- `ADK_INVOCATION_COMPLETED`
- `ROUTE_SELECTED`
- `ADK_TOOL_REQUESTED`
- `STRUCTURAL_POLICY_EVALUATED`
- `SEMANTIC_POLICY_EVALUATED`
- `TOOL_CALL_COMPLETED`

Representative policy-decision fields:

```json
{
  "tool_id": "code.review_static",
  "caller": "adk_narrow_coordinator",
  "operation": "draft",
  "risk": "medium",
  "semantic_decision": {
    "decision": "allow",
    "reason_code": "INTENT_ALIGNED",
    "selected_capability": "code_review",
    "user_intent": "CODE_REVIEW",
    "mentoring_mode": "CODE_REVIEW"
  }
}
```

## Evaluation Changes

`adk_routing` now includes:

- `route_code_review_requested_capability`

`adk_tool_orchestration` now includes:

- `adk_code_review_static_allowed`
- `adk_code_review_disabled_no_tool_bypass`

`semantic_tool_policy` now includes:

- `safe_allow_static_code_review`

## Verification Results

Focused tests:

```text
cd backend && .venv/bin/pytest -q tests/test_adk_tool_orchestration.py tests/test_tool_gateway.py tests/test_semantic_tool_policy.py tests/test_evaluation_platform.py
38 passed, 4 warnings
```

Full backend tests:

```text
cd backend && .venv/bin/pytest -q
95 passed, 5 warnings
```

Lint:

```text
cd backend && .venv/bin/ruff check app tests
All checks passed
```

Explicit evaluations:

```text
adk_routing: 6 passed / 6
adk_tool_orchestration: 9 passed / 9
semantic_tool_policy: 19 passed / 19
suite all: 66 passed / 66
```

Accepted deterministic baseline:

```text
status: pass
current_run_id: eval_20260710T075842Z_f2d7abe2
caseset_drift: false for code_review, hinting, pattern_transfer, problem_intelligence
blocking_regressions: []
warnings: []
```

Frontend build:

```text
cd frontend && node node_modules/next/dist/bin/next build
Compiled successfully
Generated 12 static pages
```

## Baseline Impact

No accepted deterministic baseline suite was changed. The accepted `--suite all` baseline remains 66 cases and comparison passed without metric regressions or caseset drift. New routing, tool-orchestration, and semantic-policy cases remain explicit ADK/policy suites.

## Fallbacks

- `ENABLE_LIVE_ADK=false` still uses deterministic route selection.
- Governed `code_review` does not call the raw review workflow unless an approved `code.review_static` request exists.
- Missing or denied code-review tool requests return an explicit policy-gated no-review response.
- Direct `/code-review` remains available as the deterministic compatibility endpoint.

## Known Limitations

- The static review tool does not execute learner code and does not prove runtime correctness.
- CI uses mocked ADK decisions for tool-orchestration behavior and does not call Gemini.
- The governed route currently requires an explicit `code.review_static` request; deterministic disabled routing intentionally does not auto-review code.
- Legacy `/code-review` remains outside the governed ADK route and is documented as a compatibility path.
- No memory retrieval, BKT update, secure execution sandbox, or broad multi-agent expansion was added in this phase.
