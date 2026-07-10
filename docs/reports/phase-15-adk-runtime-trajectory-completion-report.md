# Phase 15 ADK Runtime Trajectory Completion Report

PHASE:
Real Google ADK Runtime Integration With Trajectory Capture

STATUS:
Complete

CURRENT ADK ARCHITECTURE FOUND:
`backend/app/agents/adk_agents.py` defined a decorative root coordinator with all specialist sub-agents, but the production request path bypassed it. Existing direct routes called `MentorService`, which called deterministic Skills/workflows/tools.

CURRENT RUNTIME PATH FOUND:
```text
FastAPI route -> MentorService -> deterministic Skill/workflow/tool -> response
```

ARCHITECTURE DECISION:
Introduce one narrow ADK runtime slice for routing and trajectory capture only. Do not connect all existing agents. Do not use the old all-subagent root. Preserve deterministic workflows and direct endpoints.

RUNTIME PATH ADDED:
```text
POST /api/v1/mentor/route
  -> request/trace middleware
  -> MentorService.route_mentor_request
  -> AdkCoordinatorRuntime.route
  -> real google.adk Agent object built with CoordinatorDecision schema
  -> live invocation skipped unless explicitly enabled/configured
  -> deterministic fallback routing
  -> existing deterministic workflow
  -> response + trajectory-v1
```

NARROW SLICE:
Only two capabilities are routed in this phase:

- `problem_analysis` -> `problem_intelligence_workflow`
- `next_hint` -> `progressive_hinting_workflow`

GOOGLE ADK INTEGRATION:
Verified local `google.adk` import and `google.adk.agents.Agent`. `AdkCoordinatorRuntime` builds a real `LlmAgent` named `algoflow_narrow_coordinator` with no tools, no sub-agents, timeout `3.0`, and structured output schema `CoordinatorDecision`.

LIVE MODEL STATUS:
Live ADK/Gemini invocation remains disabled by default. CI and tests do not call Gemini. Mock invoker tests prove the ADK invocation boundary and fallback behavior.

TRAJECTORY SCHEMA:
Schema version: `trajectory-v1`.

Fields:

- `request_id`
- `trace_id`
- `session_id`
- `task`
- `runtime_mode`
- `selected_capability`
- `fallback_used`
- `started_at`
- `finished_at`
- `duration_ms`
- `events`

TRAJECTORY EVENTS:

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

REQUEST / TRACE / SESSION IDENTITY:
The new route uses existing request/trace middleware. Tests verify the response trajectory `request_id` matches `x-request-id` and `trace_id` matches the response `x-trace-id`. Session ID is generated when not supplied.

FILES CREATED:

- `backend/app/runtime/__init__.py`
- `backend/app/runtime/trajectory.py`
- `backend/app/runtime/adk_runtime.py`
- `backend/app/evaluation/adk_routing_eval.py`
- `backend/app/evaluation/adapters/adk_routing.py`
- `backend/tests/test_adk_runtime_trajectory.py`
- `docs/audits/adk-runtime-integration-audit.md`
- `docs/evaluation/adk-routing-evaluation.md`
- `docs/reports/phase-15-adk-runtime-trajectory-completion-report.md`
- `evals/adk_routing/cases.jsonl`

FILES MODIFIED:

- `.github/workflows/ci.yml`
- `backend/app/api/routes.py`
- `backend/app/evaluation/core/metrics.py`
- `backend/app/evaluation/core/registry.py`
- `backend/app/evaluation/core/thresholds.py`
- `backend/app/schemas/mentor.py`
- `backend/app/services/mentor_service.py`
- `backend/tests/test_evaluation_platform.py`
- `docs/API.md`
- `docs/evaluation/ci-integration.md`
- `specs/architecture/adk-runtime.md`

EVALUATION PLATFORM CHANGES:
Added explicit `adk_routing` suite. `--suite all` remains the accepted-baseline four-suite contract and still returns 66 cases.

ADK ROUTING EVAL RESULT:
`python -m app.evaluation.cli run --suite adk_routing`:

- 3 cases
- 3 passed
- `routing_accuracy=1.0`
- `trajectory_event_coverage=1.0`
- `fallback_policy_accuracy=1.0`
- gates passed

ACCEPTED BASELINE COMPARISON:
`python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --machine`:

- exit code `0`
- status `pass`
- blocking regressions `0`
- warnings `0`
- not comparable `0`

BASELINE PRESERVATION:
The accepted baseline was not mutated. The new ADK routing suite is not included in `--suite all` yet, avoiding silent caseset drift.

CI CHANGES:
CI now runs:

- backend tests
- backend lint
- accepted-baseline eval comparison
- explicit ADK routing trajectory eval
- frontend production build

FALLBACKS:
When `ENABLE_LIVE_ADK=false`, runtime records `adk_disabled`, `ADK_INVOCATION_SKIPPED`, and uses deterministic routing fallback. If a live/mock invoker returns invalid output, runtime records `ADK_INVOCATION_FAILED` and falls back safely.

REGRESSIONS:
No accepted-baseline regression detected. No direct endpoint behavior was changed.

TESTS RUN:

- `cd backend && .venv/bin/pytest -q tests/test_adk_runtime_trajectory.py tests/test_evaluation_platform.py`
- `cd backend && .venv/bin/pytest -q`
- `cd backend && .venv/bin/ruff check app tests`
- `cd backend && .venv/bin/python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --machine`
- `cd backend && .venv/bin/python -m app.evaluation.cli run --suite adk_routing`
- `cd frontend && npm run build`
- `ruby -e "require 'yaml'; YAML.load_file('.github/workflows/ci.yml'); puts 'workflow_yaml_parse_ok'"`

EXACT TEST RESULTS:

- Focused ADK/eval tests: 11 passed, 4 ADK deprecation warnings.
- Full backend tests: 62 passed, 5 warnings.
- Backend lint: all checks passed.
- ADK routing eval: 3/3 passed.
- Accepted-baseline comparison: `0 pass 0 0 0`.
- Frontend build: compiled successfully, lint/type checks passed, 12 static pages generated.
- Workflow YAML parse: `workflow_yaml_parse_ok`.

KNOWN LIMITATIONS:

- No live Gemini model call is executed in this phase.
- No broad sub-agent delegation is connected.
- No tool gateway integration yet.
- No persistent trajectory database table yet.
- Only `problem_analysis` and `next_hint` route through the new endpoint.
- Existing direct endpoints remain deterministic and do not return trajectories.
- ADK package emits `BaseAgentConfig` deprecation warnings during tests.

SECURITY / POLICY NOTES:

- No new tools are exposed to ADK.
- No code execution is added.
- No secrets are required.
- The runtime fails closed to deterministic fallback for disabled or invalid ADK invocation.

NEXT RECOMMENDED PHASE:
Persistent trajectory storage and trajectory-evaluation expansion, or tool-gateway policy integration before any live ADK tool use.
