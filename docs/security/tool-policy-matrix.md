# Tool Policy Matrix

Status: Current
Owner: AlgoFlow

| Tool ID | Purpose | Operation | Risk | Allowed Callers | Allowed Capabilities | Allowed Mentoring Modes | Semantic Preconditions | Leakage Considerations | Input Trust | Output Trust | Failure Behavior |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `problem.detect_pattern` | Classify problem pattern/topic metadata | read | low | `adk_narrow_coordinator`, `mentor_service` | `problem_analysis`, `next_hint` | `EXPLAIN_CONCEPT`, `HINT_ONLY`, `VALIDATE_APPROACH`, `EXPLICIT_SOLUTION` | problem title/description present; tool title matches task title; intent is problem analysis, hint, validation, or authorized reveal | May support hints, but does not produce final code; denied if full-solution intent lacks explicit reveal authorization | title/description are untrusted user/problem data | deterministic internal classifier, conditionally trusted | structural/semantic deny records trajectory event and policy decision where caller persists it |
| `problem.related_problems` | Return curated related problems for a pattern | draft | low | `adk_narrow_coordinator`, `mentor_service` | `recommendations`, `pattern_transfer` | `RECOMMEND_TRANSFER` | pattern argument present; user intent is recommendation/transfer | Not allowed in hint-only mode to avoid capability drift from one hint into a learning path | pattern is derived or user-provided data; must not redefine policy | deterministic curated list, conditionally trusted | denied on intent/capability/mode mismatch |

## Direct Legacy Paths

- `/problems/analyze` still calls `detect_problem_pattern` directly for compatibility.
- `/hints/next` still calls `detect_problem_pattern` inside the deterministic hint workflow.
- `/recommendations` still calls `recommend_related_problems` directly.
- `/pattern-transfer` uses its deterministic Skill directly.

These are retained in Phase 19 and documented as migration candidates. The governed `/mentor/route` path must not bypass the gateway after semantic denial.

## ADK Tool Request Boundary

Phase 21 allows the narrow ADK coordinator to emit structured tool requests in
`CoordinatorDecision.tool_requests`. This is not direct ADK tool execution.

- Allowed request IDs are limited to `problem.detect_pattern` and `problem.related_problems`.
- The server records each request as `ADK_TOOL_REQUESTED`.
- The server rebuilds executable arguments from trusted route context before calling the gateway.
- `ToolGateway` still performs structural policy, semantic policy, input validation, output validation, and trajectory recording.
- Misaligned requests, such as `problem.related_problems` during `next_hint`, are denied and recorded as `TOOL_CALL_DENIED`.
- Aligned `problem.related_problems` requests are allowed only for governed `recommendations` or `pattern_transfer` route decisions with transfer-oriented semantic context.
