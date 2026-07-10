# ADK Code Review Route Runtime Audit

Status: Current
Owner: AlgoFlow
Phase: 24 - Governed Code Review Capability Routing

## Audit Purpose

Audit the next ADK expansion after governed pattern-transfer routing. The goal is to add one code-review runtime slice without broadening ADK autonomy, executing learner code, or reviving decorative multi-agent architecture.

## Pre-Phase State

The governed `/mentor/route` supported:

- `problem_analysis`
- `next_hint`
- `recommendations`
- `pattern_transfer`

The deterministic `/code-review` endpoint used the Code Review Skill directly and persisted learning events. No code-review tool existed in `ToolGateway`, and `/mentor/route` could not select `code_review`.

## Planned Phase 24 Slice

`/mentor/route` should accept and select:

- `code_review`

Planned runtime behavior:

```text
POST /api/v1/mentor/route
  -> AdkCoordinatorRuntime.route
  -> selected_capability = code_review
  -> optional tool_requests = code.review_static
  -> ADK_TOOL_REQUESTED
  -> ToolGateway structural policy
  -> semantic policy with CODE_REVIEW + CODE_REVIEW
  -> CodeReviewResponse
```

## Safety Boundary

The route must not execute learner code. The new tool, if added, is a deterministic static-review draft tool only.

The ADK Agent must still receive no executable direct tools. `Agent(..., tools=[], sub_agents=[])` remains the boundary.

If no approved code-review tool request exists, `/mentor/route` should return a safe code-review fallback instead of silently calling the legacy `/code-review` path.

## Existing Compatibility Path

The legacy `/code-review` endpoint remains unchanged as the direct deterministic Skill path. Phase 24 only governs the ADK `/mentor/route` slice.

## Non-Goals

- No code execution or sandbox work.
- No broad Gemini/model review.
- No memory retrieval/RAG changes.
- No cloud/deployment changes.
- No accepted deterministic baseline change.
