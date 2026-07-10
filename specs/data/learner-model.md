# Learner Model Specification

Status: Draft
Owner: AlgoFlow
Phase: 1

Implementation note:

Phase 5 added an initial append-only `learning_events` table and emits events from existing workflows. Mastery and misconception state derivation is not implemented yet.

Phase 6 added a minimal evidence-derived learner-state engine. It reports confidence, evidence counts, derived topic mastery, and mistake summaries. It is not full Bayesian Knowledge Tracing.

## Purpose

Define evidence-based learner state so AlgoFlow can personalize without fabricating strengths, weaknesses, or readiness.

## Motivation

Current new users receive static `DEFAULT_PROFILE` values. This creates misleading analytics and weakens trust. Production AlgoFlow must derive learner state from observable learning evidence.

## Scope

- Learning evidence categories.
- Mastery state dimensions.
- Misconception tracking.
- Confidence and recency.
- Update rules.
- Explainability requirements.

## Non-Goals

- Full Bayesian Knowledge Tracing implementation in Phase 1.
- Real-time psychometric modeling.
- Claiming readiness from insufficient data.

## Data Concepts

### Learning Events

Potential events:

- `ProblemClassified`
- `HintRequested`
- `HintDelivered`
- `ApproachSubmitted`
- `CodeSubmitted`
- `ReviewDelivered`
- `MisconceptionDetected`
- `InterviewAnswerSubmitted`
- `MasteryUpdated`
- `RecommendationShown`

### Mastery State

Fields:

- concept
- score
- confidence
- evidence_count
- last_evidence_at
- positive_evidence_count
- negative_evidence_count
- decay_factor
- explanation

### Misconception State

Fields:

- misconception_id
- concept
- probability
- evidence_count
- latest_evidence
- corrective_strategy

## Update Principles

- New users start with unknown/low-confidence state, not invented strengths/weaknesses.
- Every important update must cite evidence.
- Recent evidence should matter more than stale evidence.
- Hints and reviews should distinguish low mastery from low evidence.

## BDD Scenarios

### Scenario: New User Has No Evidence

Given a new authenticated user has no learning events
When analytics are requested
Then the system reports insufficient evidence or unknown mastery
And does not claim strong or weak topics

### Scenario: Repeated DP Base Case Mistakes

Given the learner has three reviewed submissions with DP initialization mistakes
When learner state is updated
Then the DP base-case misconception probability increases
And the update cites the relevant review events

### Scenario: Strong Recent Evidence

Given the learner solves several graph traversal problems without hints
When mastery is recalculated
Then graph traversal mastery and confidence increase
And stale unrelated mistakes do not dominate the score

## Security

- Learner state is user-scoped.
- Evidence references must not expose another user's data.
- Sensitive code snippets should not be stored in summary fields unless explicitly needed.

## Observability

- Record update reason, input evidence IDs, previous state, new state, and algorithm version.

## Testing Strategy

- Unit tests for update rules.
- DB tests for event-to-state derivation.
- Regression tests for new-user unknown state.

## Evaluation Strategy

- Personalization quality evals.
- Misconception detection accuracy.
- Calibration checks against labeled learner histories.

## Acceptance Criteria

- No fabricated default strengths/weaknesses outside explicit demo mode. Implemented for analytics.
- Analytics include confidence/evidence counts. Implemented.
- State updates can be explained from events. Partially implemented through derived evidence summaries; persisted mastery state is not implemented yet.

## Phase 5 Implemented Event Types

- `ProblemClassified`
- `HintDelivered`
- `CodeSubmitted`
- `ReviewDelivered`
- `MisconceptionDetected`
- `StudyPlanGenerated`
- `AnalyticsViewed`
- `InterviewAnswerSubmitted`
