# Trajectory Storage Runtime Audit

Status: Complete
Owner: AlgoFlow
Phase: Persistent Trajectory Storage + Expanded Trajectory Evaluation

## Current State Before This Phase

Phase 15 returned `trajectory-v1` payloads from `POST /api/v1/mentor/route`, but trajectories were not stored durably. The database had `learning_events`, `problem_attempts`, `mistakes`, and `interview_sessions`, but no dedicated trajectory table.

## Existing Persistence Pattern

SQLite tables are defined in `backend/app/db/base.py` and created on startup through `Base.metadata.create_all` in `backend/app/db/init_db.py`. Repository helpers in `backend/app/memory/repository.py` mediate most app persistence.

## Gap Found

- No `agent_trajectories` table.
- No trajectory repository helpers.
- No route to retrieve a stored trajectory.
- ADK routing eval checked event presence but not trajectory identity completeness.

## Architecture Decision

Add an append-only trajectory table scoped by `user_id`, persist the trajectory after mentor route execution, and expose a principal-scoped read endpoint. Do not add a broad observability stack, cloud tracing, OpenTelemetry, or live ADK model calls in this phase.

## Runtime Path After This Phase

```text
POST /api/v1/mentor/route
  -> ADK coordinator boundary
  -> deterministic fallback/workflow
  -> trajectory.finish()
  -> record_agent_trajectory(...)
  -> response includes same trajectory_id
```

Read path:

```text
GET /api/v1/agent-trajectories/{trajectory_id}
  -> resolved principal
  -> trajectory_for_user(...)
  -> stored trajectory response or 404
```

## Security Boundary

Trajectory reads are scoped to the resolved principal. The endpoint does not accept arbitrary `user_id` query parameters.

## Known Limitations

- No migration framework yet; new tables are created via `create_all`.
- No retention/deletion policy yet.
- No trajectory search/list API yet.
- No OpenTelemetry export.
- No live model token/cost capture yet.
