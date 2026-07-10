# ADR 0004: Memory Architecture

Status: Proposed

## Context

The current system writes some text to ChromaDB but does not retrieve it into most decisions. Relational memory exists but is shallow.

## Decision

Define memory semantics before migrating storage:

- Working memory: current session/problem/code/hint state.
- Episodic memory: concrete learning events.
- Semantic learner memory: derived mastery/misconceptions/preferences with confidence.
- Procedural memory: versioned tutoring strategies/Skills.

Keep ChromaDB for local development initially. Prefer PostgreSQL + pgvector for first production consolidation unless scale or latency justifies Vertex AI Vector Search.

## Alternatives

- Treat Chroma as memory: rejected.
- Move immediately to Vertex AI Vector Search: deferred as premature.
- Store all context in prompts: rejected.

## Consequences

- Need write/retrieval/merge/expiration/provenance policies.
- Retrieval must be scoped by authenticated user and treated as untrusted context.

## Security Impact

High: memory is a cross-user leakage vector without auth and policy.

## Operational Impact

Postgres + pgvector simplifies Cloud Run/Cloud SQL architecture initially.

## Evaluation Impact

Requires retrieval Recall@K/MRR/nDCG and provenance tests.
