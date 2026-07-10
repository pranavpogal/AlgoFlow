# Phase 18 Policy Decision Persistence Completion Report

PHASE:
Persistent Policy-Decision Records Before Live ADK Tool Use

STATUS:
Complete

ARCHITECTURE CHANGE:
Policy decisions from gateway-mediated tool calls are now persisted as standalone audit records linked to request, trace, session, and trajectory identity.

FILES MODIFIED:

- `backend/app/db/base.py`
- `backend/app/memory/repository.py`
- `backend/app/services/mentor_service.py`
- `backend/app/api/routes.py`
- `backend/app/schemas/mentor.py`
- `backend/tests/test_adk_runtime_trajectory.py`
- `backend/tests/test_tool_gateway.py`
- `docs/API.md`
- `specs/security/policy-gateway.md`
- `docs/evaluation/tool-gateway-evaluation.md`

FILES CREATED:

- `docs/audits/policy-decision-persistence-audit.md`
- `docs/reports/phase-18-policy-decision-persistence-completion-report.md`

PERSISTENCE MODEL:
`PolicyDecisionRecord` stores tool policy outcomes in `policy_decisions` with user, request, trace, session, trajectory, tool, caller, operation, risk, decision, policy ID, reason, success, error, latency, and metadata fields.

RUNTIME PATH UPDATED:
`/api/v1/mentor/route` persists policy decisions for the gateway-mediated `problem.detect_pattern` call after storing the agent trajectory.

READ PATH ADDED:
`GET /api/v1/agent-trajectories/{trajectory_id}/policy-decisions` returns principal-scoped policy records for a trajectory.

TRAJECTORY SCHEMA:
No trajectory schema change. Policy decisions remain embedded in tool events and are additionally persisted as standalone records.

FALLBACKS:
Deterministic ADK-disabled fallback behavior is unchanged. Existing workflows continue to run without live ADK/Gemini tool execution.

BASELINE RELATIONSHIP:
The accepted deterministic baseline remains the gate. This phase adds persistence and tests around the narrow runtime slice without changing evaluation outputs.

TESTS AND EVALUATION:

- Focused gateway/runtime tests: `9 passed, 4 warnings`
- Full backend tests: `67 passed, 5 warnings`
- Ruff: `All checks passed`
- Accepted baseline comparison: `0 pass 0 0 0 eval_20260706T084218Z_7ddc33ed`
- ADK routing eval: `3/3 passed`, gates `PASS`
- Frontend build: Next.js production build compiled successfully, 12 static pages generated

FRONTEND BUILD NOTE:
The shell did not expose `npm`, so the build was run through the bundled Node binary:
`/Users/pranavpogal/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/next/dist/bin/next build`.

KNOWN LIMITATIONS:

- No live ADK/Gemini tool use.
- No broad raw-tool migration.
- No external tools or code execution.
- No semantic policy classifier.
- No migration framework.
- No admin policy-log search/export UI.
