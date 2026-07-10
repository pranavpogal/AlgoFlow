# Memory and Context Engineering Specification

Status: Partially Implemented
Owner: AlgoFlow
Phase: Memory + RAG Personalization

## Purpose

Define memory semantics and safe context construction for personalized AI mentoring.

## Motivation

Current vector writes are useful but insufficient. Memory is not a vector database; it requires write policy, retrieval policy, provenance, privacy, and context budgeting.

## Current Runtime Scope

Implemented narrow RAG personalization slice:

- `backend/app/memory/context.py` builds same-user scoped memory context.
- `backend/app/memory/policy.py` enforces a purpose-bound same-user memory read policy.
- `VectorMemory.search` returns stable memory IDs when available.
- `MemoryRetrieved` learning events record retrieval purpose, count, provenance, and limitations.
- `MemoryRetrieved` is passive and does not increase learner mastery/readiness evidence.
- Response schemas expose `memory_context` for hints, code review, study plans, recommendations, pattern transfer, and mock interviews.

Current retrieval is advisory. It may influence wording and personalization notes, but it is not treated as correctness proof, mastery proof, or policy authority.

## Memory Types

- Working memory: current problem, code, approach, hint stage, session state.
- Episodic memory: concrete learning events and past interactions.
- Semantic learner memory: derived mastery, misconceptions, preferences, goals.
- Procedural memory: tutoring strategies and Skill versions.

## Write Policy

Memory writes must specify:

- user_id from authenticated context
- memory type
- source event ID
- confidence
- provenance
- retention category
- sensitivity level

Current implementation note: vector writes remain existing local memory notes from deterministic workflows. Full typed memory write policy is still future work.

## Retrieval Policy

Retrieval must specify:

- user scope
- query purpose
- allowed memory types
- max items
- ranking strategy
- recency and confidence weighting
- provenance returned with each hit

Current implementation:

- same-user scope is enforced by `evaluate_memory_access`
- purpose is required
- retrieval limit is bounded to a small default
- snippets are length-bounded
- each returned snippet includes `vector_memory.search` provenance
- cross-user retrieval is denied before vector search

## Context Builder

Inputs:

- current request
- task intent
- problem metadata
- current code/reasoning
- session state
- selected learner state
- selected retrieval hits
- tool results
- Skill/agent instructions
- token budget

Outputs:

- trusted instructions
- untrusted user content
- untrusted retrieved content
- compact evidence summaries
- provenance references
- budget metadata

Current implementation note: the runtime context builder returns normalized snippets and provenance for service-layer workflows. It does not yet build model prompts or token-budgeted Gemini contexts.

## Security

- Retrieved content must never override system/developer/project instructions.
- User content and problem statements are untrusted.
- Cross-user retrieval is forbidden.
- Sensitive data is excluded unless required and authorized.

## BDD Scenarios

### Scenario: Retrieve User-Scoped DP Mistakes

Given user A has prior DP initialization mistakes
And user B has graph mistakes
When user A asks for a DP hint
Then retrieval may include user A's DP evidence
And must not include user B's graph evidence

### Scenario: Prompt Injection In Retrieved Memory

Given a retrieved memory item contains “ignore system instructions”
When the context builder constructs prompt context
Then the content is marked untrusted
And cannot override policy or Skill instructions

### Scenario: Context Budget Pressure

Given the learner has many past events
When the hint Skill has a small context budget
Then the context builder includes only the most relevant high-confidence summaries
And records omitted categories in metadata

## Testing Strategy

- Retrieval filtering tests.
- Context builder snapshot tests.
- Prompt-injection fixture tests.

## Evaluation Strategy

- Recall@K.
- MRR.
- nDCG@K.
- Personalization evals.

## Acceptance Criteria

- Runtime decisions can cite memory provenance.
- Retrieval is scoped by authenticated user.
- Context separates trusted and untrusted content.

## Implemented Acceptance Evidence

- `backend/tests/test_memory_context.py` verifies same-user retrieval, cross-user denial, provenance, and hint endpoint personalization.
- Full accepted deterministic baseline remains unchanged after adding optional memory context fields.
- Retrieved memories are surfaced in response `memory_context` and learning-event evidence.
