# Memory + RAG Personalization Runtime Audit

Status: Current-state audit before Phase 26 implementation
Owner: AlgoFlow
Date: 2026-07-10

## Current Memory Writes

AlgoFlow already records memory-like evidence through two channels:

- relational memory in `problem_attempts`, `mistakes`, `learning_events`, trajectories, and policy decisions
- vector memory writes through `backend/app/memory/vector_store.py::VectorMemory.add`

Current examples include analyzed problems, hint milestones, code reviews, recommendations, and pattern-transfer notes.

## Current Retrieval Behavior

`VectorMemory.search(user_id, query, limit)` exists and supports ChromaDB with a JSONL fallback, but most mentor workflows do not retrieve vector memories before responding. The service primarily uses `user_memory_snapshot` and `derive_learner_state`, which are useful but not RAG.

## Current Personalization Behavior

Personalization is partially active through relational memory:

- hints read `user_memory_snapshot` and derived learner state
- study plans read memory snapshot and derived learner state
- analytics read memory snapshot and derived learner state
- pattern transfer reads memory snapshot and learner state

However, retrieved vector memories do not yet provide cited context in responses, so the project should not claim deep RAG personalization yet.

## Gap

Phase 26 should make retrieval explicit, scoped, and provenance-bearing without turning memory into an unbounded prompt bag. Retrieval must be treated as advisory context, not authoritative truth.

## Proposed Narrow Slice

Add a memory context builder that:

- searches vector memory for the current user only
- uses bounded query text and result limits
- returns normalized memory snippets with provenance
- marks whether retrieved context was applied
- records retrieval as a learning event for auditability

Apply it first to deterministic workflows where response schemas can safely expose provenance:

- hints: mentor note acknowledges relevant prior memory
- code review: readability feedback and unsupported-claims/provenance mention retrieved context
- study plan: personalization notes cite retrieved context
- recommendations and pattern transfer: explanation/evidence fields include retrieved context

## Boundary Rules

- Do not add broad Gemini/RAG prompt generation.
- Do not treat retrieved memories as ground truth.
- Do not retrieve across users.
- Do not add PostgreSQL/auth changes in this phase.
- Do not change accepted deterministic baseline fixtures unless explicitly justified.
- Keep fallback behavior deterministic when retrieval returns nothing.

## Expected Tests

- user-scoped retrieval only returns the active user's memories
- context builder returns bounded snippets and provenance
- selected workflows expose memory provenance when relevant memories exist
- workflows remain stable when retrieval is empty

## Known Limitations

- ChromaDB ranking quality is not evaluated deeply in this phase.
- Retrieved snippets are short advisory context, not a full learner model.
- No memory deletion/retention policy is added here.
