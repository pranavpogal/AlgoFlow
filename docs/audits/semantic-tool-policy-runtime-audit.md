# Semantic Tool Policy Runtime Audit

Status: Complete
Owner: AlgoFlow
Phase: 19 - Semantic Tool Policy + Intent Boundary Enforcement

## Runtime Path Audited

Current governed runtime path:

```text
POST /api/v1/mentor/route
  -> MentorService.route_mentor_request
  -> AdkCoordinatorRuntime.route
  -> deterministic selected_capability while live ADK is disabled
  -> ToolGateway.call(problem.detect_pattern)
  -> structural authorization
  -> Pydantic input validation
  -> deterministic tool handler
  -> output type validation
  -> trajectory event
  -> agent_trajectories persistence
  -> policy_decisions persistence
```

## Current Policy Architecture Found

Structural controls exist in `backend/app/core/tool_gateway.py` and `backend/app/core/policy.py`:

- registered tools only
- caller allowlists
- read/draft/act operation labels
- act operations denied by default
- Pydantic input validation
- output type validation
- trajectory emission for completed/denied calls
- persistent policy decision records for the narrow `/mentor/route` path
- principal-scoped trajectory and policy-decision reads

## Current Tool Gateway Found

Registered tools:

- `problem.detect_pattern`: read, low risk, callers `adk_narrow_coordinator`, `mentor_service`
- `problem.related_problems`: draft, low risk, callers `adk_narrow_coordinator`, `mentor_service`

No live Gemini/ADK tool invocation is enabled. The narrow ADK coordinator builds an ADK agent object when available but uses deterministic fallback by default and has no tools attached.

## Current Persistence Found

`agent_trajectories` stores trajectory events and identity fields. `policy_decisions` stores structural/final policy fields plus metadata. Current records preserve request, trace, session, trajectory, tool, caller, operation, risk, decision, policy ID, success, error, latency, and metadata.

## What Is Structurally Enforced

- unknown tools fail closed
- disallowed callers fail closed
- act tools fail closed
- invalid input schema fails closed
- invalid output type fails closed
- cross-user trajectory/policy-decision reads return `404`

## What Is Semantically Enforced Today

Semantic mentoring behavior exists inside Skills, not the gateway:

- progressive hinting has deterministic intent detection and reveal handling
- progressive hinting limits full solution behavior unless `reveal_solution` or full-solution wording is present
- problem intelligence uses deterministic classification evidence/provenance
- pattern transfer uses deterministic relationship and learner-evidence constraints

The gateway itself does not currently enforce semantic intent-tool alignment, capability-tool alignment, mentoring mode, prompt-injection suspicion, or tool-specific semantic preconditions.

## Semantic Gaps Found

- `problem.related_problems` can be structurally called by an allowlisted caller even when current intent is only one hint.
- `problem.detect_pattern` can be called without a trusted selected capability or mentoring mode.
- A structurally allowed future ADK caller could request a tool unrelated to the selected capability.
- Prompt-injection-like user/problem text is treated as data by Python code today, but no gateway signal records suspicious override pressure.
- Solution-leakage policy is enforced in the hint Skill output, not before tool execution.
- Policy decision persistence records structural outcomes but not semantic reason codes, policy version, selected capability, mentoring mode, reveal authorization, or injection suspicion.
- Direct legacy endpoints still call raw deterministic tools outside the gateway.

## Where Intent Is Currently Derived

- `AdkCoordinatorRuntime._deterministic_decision` infers `problem_analysis` vs `next_hint` from requested capability, message, and hint level.
- `progressive_hinting.detect_intent` infers hint intent and explicit reveal from user attempt and `reveal_solution`.
- No shared typed gateway intent context exists before this phase.

## Where Intent May Drift

- Future live ADK routing could select one capability while requesting an unrelated tool.
- Allowlisted callers can currently call `problem.related_problems` without an explicit recommendation/transfer capability.
- User content may include instruction-like text inside problem descriptions; current code does not obey it as instructions, but it also does not record the risk.

## Solution-Leakage Boundary Found

The progressive hint workflow is the source of truth for explicit reveal and leakage controls. `detect_intent` only returns `FULL_SOLUTION` when `reveal_solution` is true or the user explicitly asks for a full solution. The gateway must reuse those signals rather than inventing contradictory reveal behavior.

## Prompt-Injection-Like Content Reachability

User message, problem title, and problem description can reach gateway payloads and deterministic tool inputs. Current deterministic handlers do not execute instructions from that text, but suspicious phrases can reach policy context unless explicitly marked as untrusted data.

## Tool Result Influence

`problem.detect_pattern` output influences `TopicAnalysis` and hint context. `problem.related_problems` output can influence recommendations. Both are deterministic internal tool outputs and should be treated as conditionally trusted, not policy instructions.

## Policy Provenance Sufficiency

Before this phase, persisted policy outcomes have identity and structural decision data. They do not have enough semantic provenance for future live model tool invocation readiness.

## Direct Legacy Path Findings

- `/problems/analyze` calls `detect_problem_pattern` directly. This is a low-risk compatibility path but outside governed tool policy.
- `/hints/next` calls `detect_problem_pattern` directly through `next_hint`. This is deterministic compatibility behavior and currently unreachable from a denied `/mentor/route` gateway fallback only if the route already passed classification; it remains a future migration candidate.
- `/recommendations` calls `recommend_related_problems` directly. This is a policy bypass risk for future model-driven recommendation flows but is not part of the current governed ADK runtime slice.
- `/pattern-transfer` uses the pattern transfer Skill directly. This is intentionally retained and not migrated in Phase 19.
- Code review and study-plan paths use deterministic workflows/tools directly and are out of scope for this phase.

## Implementation Implication

Semantic policy should be a deterministic policy engine composed inside `ToolGateway`, not an agent. The gateway remains the execution boundary and records both structural and semantic outcomes. Structural deny must precede and dominate semantic policy.
