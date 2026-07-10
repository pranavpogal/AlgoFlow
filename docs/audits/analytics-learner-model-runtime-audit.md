# Analytics + Learner Model Runtime Audit

Phase: 29 - Analytics + Learner Model Upgrade
Status: Pre-implementation audit

## Current Runtime Path

`GET /api/v1/analytics/{user_id}` currently follows this path:

1. API route enforces same-user identity policy.
2. `MentorService.analytics` loads `user_memory_snapshot`.
3. `derive_learner_state` computes readiness, confidence, topic mastery, mistakes, and recommendations.
4. The service injects a small placeholder `learning_velocity` list.
5. `AnalyticsViewed` is recorded as a passive learning event.

## Existing Evidence Sources

The learner model can already read:

- `problem_attempts`: titles, patterns, difficulty, status, review payloads.
- `mistakes`: category, pattern, severity, evidence.
- `learning_events`: event type, problem title, concept, evidence payload, metadata, created timestamp.
- `interview_sessions`: transcript and scorecard exist, but are not included in the analytics snapshot yet.

## Gaps

- Learning velocity is partly synthetic and does not reflect event chronology.
- Readiness score is a single blended number without visible components.
- Topic mastery treats pattern exposure and mistake signals conservatively, but does not expose risk labels or trend direction.
- Repeated mistakes are listed, but not converted into visual trend/risk artifacts.
- Mock interview scorecards are persisted but not yet included in readiness analytics.
- Frontend dashboard still displays hard-coded readiness/velocity/mistake values.

## Phase 29 Scope

This phase should:

- Keep analytics deterministic and evidence-backed.
- Include compact event history in the memory snapshot.
- Derive learning velocity from real recent learning events and attempts.
- Add readiness components, mistake trends, topic risk labels, next best actions, and evidence limitations.
- Include interview scorecard summaries without claiming live interviewer judgment.
- Update analytics UI and dashboard to use real API data instead of static metrics.
- Preserve same-user access controls and passive-event handling.

## Explicit Non-Goals

- No live Gemini analytics interpretation.
- No new decorative analytics agent.
- No new database table unless required.
- No broad frontend redesign.
- No cloud observability or deployment work.
- No change to accepted deterministic baseline thresholds unless justified by eval updates.
