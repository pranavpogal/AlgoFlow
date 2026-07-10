# Memory and Context Engineering Specification

Status: Draft
Owner: AlgoFlow
Phase: 1

## Purpose

Define memory semantics and safe context construction for personalized AI mentoring.

## Motivation

Current vector writes are useful but insufficient. Memory is not a vector database; it requires write policy, retrieval policy, provenance, privacy, and context budgeting.

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

## Retrieval Policy

Retrieval must specify:

- user scope
- query purpose
- allowed memory types
- max items
- ranking strategy
- recency and confidence weighting
- provenance returned with each hit

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
