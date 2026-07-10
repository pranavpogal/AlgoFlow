# ADK Runtime Integration Audit

Status: Complete
Owner: AlgoFlow
Phase: Real Google ADK Runtime Integration With Trajectory Capture

## Purpose

Audit the current ADK/runtime path before introducing live runtime behavior. This phase must avoid decorative multi-agent revival and preserve deterministic workflows, evaluation gates, and accepted-baseline semantics.

## Current Runtime Found

Existing request path before this phase:

```text
FastAPI route -> MentorService -> deterministic Skill/workflow/tool -> response
```

Existing ADK assets before this phase:

- `backend/app/agents/adk_agents.py`: defined a root coordinator and many sub-agents.
- `backend/app/agents/instructions.py`: prompt instructions for coordinator and specialists.
- `backend/app/core/config.py`: `enable_live_adk` setting, default `False`.
- `specs/architecture/adk-runtime.md`: planned bounded ADK runtime integration.

## Decorative Agent Risk

`backend/app/agents/adk_agents.py` attaches all named specialist agents to a root coordinator. The audit confirms this should not be wired wholesale into the request path because most current capabilities are deterministic Skills/workflows and do not require autonomous agent behavior.

## Request And Trace Identity Found

`backend/app/core/middleware.py` creates request and trace IDs and writes response headers:

- `x-request-id`
- `x-trace-id`

`backend/app/core/request_context.py` exposes these values through context variables.

## Evaluation And CI Constraints Found

Phase 13 unified evaluation platform and Phase 14 accepted-baseline contract exist. The accepted baseline covers the original four deterministic suites:

- hinting
- code_review
- problem_intelligence
- pattern_transfer

The ADK runtime slice must not mutate the accepted baseline or weaken existing gates.

## Integration Decision

Introduce a narrow ADK coordinator runtime dedicated to routing only between:

- `problem_analysis` -> `problem_intelligence_workflow`
- `next_hint` -> `progressive_hinting_workflow`

Do not invoke the old all-subagent root. Do not connect live Gemini in CI. Do not replace deterministic workflows.

## Runtime Path Added

```text
POST /api/v1/mentor/route
  -> request/trace context
  -> AdkCoordinatorRuntime
  -> real Google ADK Agent object created with structured output schema
  -> live invocation skipped unless ENABLE_LIVE_ADK and explicit invoker are configured
  -> deterministic routing fallback
  -> existing deterministic MentorService workflow
  -> structured trajectory returned
```

## Google ADK Verification

Local import verified:

- `google.adk` imports successfully.
- `google.adk.agents.Agent` resolves to `google.adk.agents.llm_agent.LlmAgent`.

## Trajectory Capture

Trajectory events now include:

- `REQUEST_RECEIVED`
- `ADK_AGENT_BUILT`
- `ADK_INVOCATION_SKIPPED`
- `ADK_INVOCATION_STARTED`
- `ADK_INVOCATION_COMPLETED`
- `ADK_INVOCATION_FAILED`
- `ROUTE_SELECTED`
- `DETERMINISTIC_FALLBACK_USED`
- `WORKFLOW_EXECUTED`
- `RESPONSE_VALIDATED`

## Known Limitations

- Live ADK model invocation is not enabled by default.
- No Gemini call is made in CI or deterministic local tests.
- No broad agent delegation is added.
- Trajectories are returned and evaluable but not persisted in a database table yet.
- Only two low-risk capabilities are routed through the new endpoint.
