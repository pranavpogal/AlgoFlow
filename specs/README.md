# AlgoFlow Specifications

This directory is the source of truth for future major behavior changes. Do not implement major AI, security, data, API, or deployment features without a linked specification.

Recommended structure:

- `architecture/`: runtime, agent/Skill/workflow, context, and policy specs.
- `features/`: adaptive hinting, code review, mock interview, learner analytics specs.
- `api/`: endpoint contracts, error envelopes, request IDs, pagination, auth boundaries.
- `data/`: learning events, mastery state, memory taxonomy, migrations.
- `security/`: threat controls, sandbox, policy gateway.
- `evaluation/`: eval datasets, metrics, acceptance thresholds.
- `deployment/`: Cloud Run, Cloud SQL, secrets, CI/CD, rollback.

A feature spec should include purpose, scope, non-goals, user stories, architecture, dependencies, data model, API contracts, state transitions, security, observability, failure modes, BDD scenarios, tests, evals, rollout, and rollback.
