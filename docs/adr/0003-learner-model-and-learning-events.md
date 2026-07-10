# ADR 0003: Learner Model and Learning Events

Status: Proposed

## Context

New users currently receive hardcoded strong/weak topics and mastery scores through `DEFAULT_PROFILE`. This creates fictional evidence and misleading analytics.

## Decision

Introduce immutable learning events and derive learner state from evidence. Start with a pragmatic event model and confidence-weighted mastery updates; defer full Bayesian Knowledge Tracing until enough data/evals exist.

## Alternatives

- Keep static profile defaults: rejected as misleading.
- Implement full event sourcing and BKT immediately: rejected as overengineering.
- Use only vector memory: rejected because memory is not just retrieval.

## Consequences

- Add `learning_events`, `mastery_states`, and misconception evidence in a later migration.
- Analytics must show confidence/unknown states for new users.

## Security Impact

Events must be user-scoped and privacy-aware.

## Operational Impact

More database writes and aggregation logic.

## Evaluation Impact

Requires tests proving state updates are explainable from evidence.
