# AlgoFlow Spec-Driven Production Development

## Purpose

AlgoFlow must be developed using production-oriented Spec-Driven Development.

This is a serious engineering project.

Do not treat high-level prompts as sufficient specifications.

Do not immediately generate large amounts of code from vague intent.

---

# 1. Spec-Driven Development

Before major implementation, create or update a specification.

The specification is the source of truth for:

- requirements
- architecture
- behavior
- interfaces
- schemas
- constraints
- failure modes
- security
- observability
- tests
- evaluations

Store specifications in version control.

Suggested structure:

specs/
  architecture/
  features/
  api/
  data/
  security/
  evaluation/
  deployment/

---

# 2. Specification Requirements

A production-grade feature specification SHOULD include:

- purpose
- motivation
- scope
- non-goals
- user stories
- architecture
- dependencies
- data model
- API contracts
- state transitions
- security considerations
- observability
- failure modes
- edge cases
- acceptance scenarios
- testing strategy
- evaluation strategy
- rollout plan
- rollback plan

---

# 3. Behavior-Driven Acceptance Scenarios

Use structured behavioral scenarios where appropriate.

Format:

Scenario
Given
When
Then

Example:

Scenario: Learner has a promising partial DP insight

Given:
- the learner is solving a DSA problem
- the learner proposes a meaningful partial state idea
- the learner has not requested a full solution

When:
- progressive hinting responds

Then:
- acknowledge the useful reasoning
- identify the smallest missing conceptual step
- avoid revealing the complete recurrence
- avoid final code
- preserve learner ownership

Include:

- success cases
- failure cases
- edge cases
- adversarial cases

---

# 4. Instruction Layering

Do not place all instructions in one giant prompt.

Use distinct layers.

## Session Instructions

Short-lived user intent.

Example:
"Give me one hint. Do not reveal the solution."

## Specifications

Task-specific source of truth.

Example:
specs/features/progressive-hinting.md

## Skills

Reusable procedural expertise.

Example:
skills/progressive-hinting/SKILL.md

## Project Instructions

Stable engineering DNA and repository-wide constraints.

These layers must not be confused.

---

# 5. Execution Modes

Different development tasks require different behavior.

## Architect Mode

Use for:

- new subsystem
- major redesign
- major infrastructure change

Before coding, produce:

- assumptions
- architecture
- alternatives
- trade-offs
- folder structure
- dependency plan
- risks
- testing plan
- evaluation plan
- migration plan

Do not immediately code.

## Builder Mode

Use for:

- implementing a defined feature

Requirements:

- follow approved spec
- match existing style
- preserve naming conventions
- preserve error-handling patterns
- add tests
- add logging where appropriate
- keep changes bounded

## Forensic Mode

Use for:

- debugging

Required sequence:

1. reproduce failure
2. collect evidence
3. identify root cause
4. create failing test or reproduction command
5. apply minimal fix
6. run regression tests
7. document root cause

Do not perform unrelated cleanup.

## Author Mode

Use for:

- specs
- architecture docs
- API docs
- README
- runbooks

## Librarian Mode

Use for:

- database operations
- migrations
- data pipelines
- retrieval systems
- analytics

Make transformations and queries explicit.

---

# 6. Evidence-Driven Debugging

No speculative large-scale patching.

Prefer:

failure
    ->
reproduction
    ->
evidence
    ->
root cause
    ->
minimal patch
    ->
regression test

When practical, create a failing test before the fix.

Keep the regression test after the fix.

---

# 7. Documentation Synchronization

When code changes, determine whether to update:

- architecture specification
- feature specification
- API contract
- data schema
- BDD scenario
- README
- operational runbook
- changelog

Documentation drift is an engineering defect.

---

# 8. Dependency Discipline

For dependencies:

- specify versions
- verify current compatibility
- do not silently downgrade
- do not trust model memory for current versions
- consult authoritative documentation where needed
- document significant dependency choices

---

# 9. Pull Request Requirements

Significant PRs SHOULD include:

- summary
- motivation
- linked specification
- files or subsystems changed
- potential breakage points
- risk assessment
- security impact
- data impact
- agent-behavior impact
- tests added
- evaluation results
- deployment considerations
- rollback strategy

---

# 10. Small Reviewable Changes

Avoid enormous unreviewable agent-generated modifications.

Prefer:

plan
    ->
small change
    ->
test
    ->
evaluate
    ->
review
    ->
next change

Do not combine unrelated refactors with bug fixes.

---

# 11. Sandboxing

Agent-generated or learner-submitted code must execute in restricted environments.

Use:

- ephemeral execution
- low privilege
- resource limits
- network isolation by default
- filesystem isolation
- no inherited secrets

---

# 12. Human-in-the-Loop

Use risk-based approval.

Examples of operations that may require explicit approval:

- production deployment
- database schema migration
- destructive data operation
- external communication
- high-impact persistent mutation

Do not interrupt users with approval prompts for every low-risk operation.

Avoid approval fatigue.

---

# 13. AI-Generated Test Coverage

AI-generated implementation should be accompanied by strong test generation.

Generate where appropriate:

- unit tests
- integration tests
- edge cases
- adversarial cases
- regression tests

For bug fixes, prefer a failing test before repair.

---

# 14. Tests vs Evaluations

Tests verify deterministic behavior.

Evaluations measure probabilistic agent behavior.

Example:

Test:
POST /hint returns a valid response schema.

Evaluation:
The hint advances the learner without leaking the solution.

Both are mandatory for agentic features.

---

# 15. Hybrid Policy Enforcement

Use two complementary policy layers.

## Structural Gating

Deterministic checks such as:

- is this tool allowed?
- is this role allowed?
- is this environment allowed?
- is this resource scope allowed?

## Semantic Gating

Contextual checks such as:

- does this action match current user intent?
- does it expose sensitive information?
- is the proposed use of an allowed tool inappropriate?
- is the content semantically unsafe?

Execution occurs only after required policy checks pass.

---

# 16. Context Hygiene

Do not hardcode sensitive runtime values into prompts.

Prefer controlled placeholders and runtime resolution.

Examples:

[[USER_ID]]
[[SESSION_ID]]
[[TENANT_ID]]
[[TRACE_ID]]
[[EXECUTION_ID]]

Resolve values only from authorized runtime state.

If required authorization context is missing:

- fail safely
- request clarification where appropriate

Do not guess from stale context.

---

# 17. Production Principle

Rapid code generation is not production readiness.

Production readiness requires:

- specification
- controlled implementation
- tests
- evaluations
- security
- observability
- review
- deployment discipline
- rollback capability

AlgoFlow must never equate generated code volume with engineering progress.