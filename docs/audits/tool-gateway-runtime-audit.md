# Tool Gateway Runtime Audit

Status: Complete
Owner: AlgoFlow
Phase: Tool Gateway + Policy Integration

## Current State Before This Phase

Tools were plain Python functions called directly by services or listed on old decorative ADK agent definitions. The narrow Phase 15/16 ADK coordinator exposed no tools, which was safe but left no policy-gated tool execution path.

## Raw Tools Found

- `backend/app/tools/problem_intelligence.py::detect_problem_pattern`
- `backend/app/tools/problem_intelligence.py::recommend_related_problems`
- `backend/app/tools/code_review.py::review_code_heuristics`
- `backend/app/tools/learning_tools.py::build_weekly_plan`
- `backend/app/tools/learning_tools.py::readiness_score`

## Existing Policy Found

`backend/app/core/policy.py` had user-scope policy for own-user resources, but no centralized tool gateway, tool schema validation, caller allowlist, or tool trajectory event capture.

## Decorative Agent Risk

`backend/app/agents/adk_agents.py` still lists raw tools on broad specialist agents. This phase does not wire those agents into runtime. Tool authority is introduced only through a narrow gateway used by `/mentor/route`.

## Architecture Decision

Implement a local structural tool gateway first. Register only low-risk read/draft problem-intelligence tools. Deny unregistered callers. Deny all `act` operations unless explicit future policy exists. Record tool calls into trajectory events.

## Tool Gateway Runtime Path

```text
/mentor/route
  -> AdkCoordinatorRuntime route decision
  -> ToolGateway.call(problem.detect_pattern)
  -> structural policy decision
  -> typed input validation
  -> deterministic tool execution
  -> output validation
  -> TOOL_CALL_COMPLETED or TOOL_CALL_DENIED trajectory event
  -> deterministic workflow response
```

## Registered Tools

- `problem.detect_pattern`: read, low risk, allowed callers `adk_narrow_coordinator`, `mentor_service`.
- `problem.related_problems`: draft, low risk, allowed callers `adk_narrow_coordinator`, `mentor_service`.

## Denial Behavior

- Unknown tools raise `ToolGatewayError`.
- Disallowed callers receive policy ID `tool.caller.denied`.
- Act tools are denied by default with `tool.act.denied_without_explicit_policy`.
- Invalid inputs record failed/denied trajectory events.

## Evaluation Impact

The explicit `adk_routing` eval now requires `TOOL_CALL_COMPLETED` in trajectory events. This keeps tool-use evaluation outside the accepted deterministic baseline until explicitly promoted.

## Known Limitations

- Gateway is in-process, not a separate service.
- Only two low-risk tools are registered.
- Direct legacy service paths still call some raw tools to preserve baseline behavior.
- No async timeout enforcement yet.
- No persistent standalone policy-decision table yet.
