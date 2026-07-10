# Phase 16 Trajectory Storage Completion Report

PHASE:
Persistent Trajectory Storage + Expanded Trajectory Evaluation

STATUS:
Complete

CURRENT TRAJECTORY ARCHITECTURE FOUND:
Phase 15 returned `trajectory-v1` from `/mentor/route`, but trajectories were not durably stored. The database had learning events and attempts, but no dedicated agent/runtime trajectory table.

ARCHITECTURE DECISION:
Add append-only trajectory persistence for the narrow ADK routing slice. Keep the accepted deterministic baseline unchanged. Do not add live Gemini, broad ADK routing, OpenTelemetry, tool gateway, cloud tracing, or retention policy in this phase.

RUNTIME PATH UPDATED:
```text
POST /api/v1/mentor/route
  -> AdkCoordinatorRuntime
  -> deterministic fallback/workflow
  -> trajectory.finish()
  -> record_agent_trajectory(...)
  -> response includes same trajectory_id
```

READ PATH ADDED:
```text
GET /api/v1/agent-trajectories/{trajectory_id}
  -> resolved principal
  -> trajectory_for_user(...)
  -> stored trajectory response or 404
```

DATABASE CHANGES:
Added `AgentTrajectory` ORM model and `agent_trajectories` table fields:

- `id`
- `user_id`
- `request_id`
- `trace_id`
- `session_id`
- `task`
- `runtime_mode`
- `selected_capability`
- `selected_skill`
- `fallback_used`
- `duration_ms`
- `schema_version`
- `event_count`
- `events`
- `trajectory_metadata`
- `created_at`

REPOSITORY CHANGES:
Added helpers:

- `record_agent_trajectory`
- `trajectory_for_user`
- `recent_trajectories_for_user`

TRAJECTORY SCHEMA CHANGE:
Added stable `trajectory_id` to `trajectory-v1` payloads.

API CHANGES:
Added `AgentTrajectoryResponse` schema and `GET /agent-trajectories/{trajectory_id}`.

EVALUATION CHANGES:
Expanded explicit `adk_routing` eval with `trajectory_identity_completeness`.

ADK ROUTING EVAL RESULT:
`adk_routing`: 3 cases, 3 passed.

Metrics:

- `routing_accuracy=1.0`
- `trajectory_event_coverage=1.0`
- `trajectory_identity_completeness=1.0`
- `fallback_policy_accuracy=1.0`

BASELINE COMPARISON:
Accepted deterministic baseline remains unchanged:

`0 pass 0 0 0`

REGRESSIONS:
None detected. `--suite all` still preserves the accepted 66-case deterministic contract.

FILES CREATED:

- `docs/audits/trajectory-storage-runtime-audit.md`
- `docs/evaluation/trajectory-storage-evaluation.md`
- `docs/reports/phase-16-trajectory-storage-completion-report.md`

FILES MODIFIED:

- `backend/app/db/base.py`
- `backend/app/memory/repository.py`
- `backend/app/runtime/trajectory.py`
- `backend/app/services/mentor_service.py`
- `backend/app/api/routes.py`
- `backend/app/schemas/mentor.py`
- `backend/app/evaluation/adk_routing_eval.py`
- `backend/app/evaluation/adapters/adk_routing.py`
- `backend/app/evaluation/core/metrics.py`
- `backend/app/evaluation/core/thresholds.py`
- `backend/tests/test_adk_runtime_trajectory.py`
- `backend/tests/test_evaluation_platform.py`
- `docs/API.md`
- `docs/evaluation/adk-routing-evaluation.md`
- `specs/architecture/adk-runtime.md`

TESTS RUN:

- `cd backend && .venv/bin/pytest -q tests/test_adk_runtime_trajectory.py`
- `cd backend && .venv/bin/pytest -q tests/test_evaluation_platform.py tests/test_adk_runtime_trajectory.py`
- `cd backend && .venv/bin/pytest -q`
- `cd backend && .venv/bin/ruff check app tests`
- `cd backend && .venv/bin/python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --machine`
- `cd backend && .venv/bin/python -m app.evaluation.cli run --suite adk_routing`
- `cd frontend && npm run build`

EXACT RESULTS:

- Focused trajectory tests: 4 passed, 4 ADK deprecation warnings.
- Focused eval/runtime tests: 11 passed, 4 ADK deprecation warnings.
- Full backend tests: 62 passed, 5 warnings.
- Ruff: all checks passed.
- Accepted baseline comparison: `0 pass 0 0 0`.
- ADK routing eval: 3/3 passed, all gates passing.
- Frontend build: compiled successfully, 12 static pages generated.

KNOWN LIMITATIONS:

- No migration framework; table creation still uses SQLAlchemy `create_all`.
- No trajectory retention/deletion policy yet.
- No trajectory list/search endpoint yet.
- No OpenTelemetry export.
- No live model/token/cost capture.
- Existing direct endpoints still do not emit persisted trajectories.

NEXT RECOMMENDED PHASE:
Tool gateway and policy integration before any live ADK tool use, or trajectory query/list UX if observability needs to become user/developer visible.
