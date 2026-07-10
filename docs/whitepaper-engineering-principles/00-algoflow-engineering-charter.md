# AlgoFlow Engineering Charter

## Project Status

AlgoFlow is a serious production-oriented agentic AI engineering project.

It is NOT:

- a toy chatbot
- a hackathon-only prototype
- a superficial multi-agent demo
- an agent wrapper around a single prompt
- a project whose quality is measured by number of agents
- a project where generated code volume substitutes for engineering quality

The goal is to evolve AlgoFlow into a state-of-the-art agentic coding interview mentorship platform with strong architecture, pedagogy, security, observability, evaluation, and production deployment discipline.

---

# 1. Product Vision

AlgoFlow should help learners improve at:

- data structures and algorithms
- coding interviews
- problem-solving
- debugging
- complexity analysis
- pattern recognition
- mock interviews
- long-term preparation

The system must adapt to the learner's current reasoning rather than merely generate solutions.

---

# 2. Core Pedagogical Principle

Preserve learner ownership of reasoning.

The system should distinguish between:

- asking whether an idea is correct
- requesting one hint
- requesting another hint
- requesting conceptual explanation
- requesting code review
- requesting debugging help
- requesting full solution
- participating in mock interview mode

Do not dump a complete solution when the learner requested guidance.

Do not restart from beginner-level explanation when the learner has already demonstrated advanced reasoning.

---

# 3. Architectural Principle

Use the correct primitive for each responsibility.

## Deterministic Logic

Use for predictable rules and transformations.

## Tool

Use for bounded external capability.

## Skill

Use for reusable procedural expertise.

## Workflow

Use for predictable multi-stage orchestration.

## Agent

Use for autonomous responsibility ownership.

## Multi-Agent Collaboration

Use only when genuine autonomous collaboration is justified.

---

# 4. Candidate Target Architecture

The architecture may evolve toward:

User
    ->
Next.js Frontend
    ->
FastAPI API
    ->
Authentication and Session Boundary
    ->
Intent and Task Context
    ->
Coordinator
    ->
Skills / Agents / DAG Workflows
    ->
Context Resolver
    ->
Hybrid Policy Layer
    ->
Tool Gateway
    ->
PostgreSQL / Vector Retrieval / MCP / External Services
    ->
Sandboxed Execution
    ->
Observability and Trace Layer
    ->
Security / Evaluation / Governance

This is a target direction, not permission to implement every component immediately.

Avoid overengineering.

---

# 5. Current Architectural Decision Rule

For every proposed component, document:

- problem being solved
- why current architecture is insufficient
- alternatives considered
- operational complexity
- security impact
- evaluation impact
- expected user value

Do not add architecture merely because it appears advanced.

---

# 6. State and Knowledge Boundaries

Prefer:

- PostgreSQL for durable structured state
- vector retrieval for semantic knowledge
- session service for runtime conversational state
- Skills for procedural expertise
- tools for bounded capabilities
- agents for autonomous responsibilities

The context window is not a database.

The context window is not a workflow log.

The context window is not a message bus.

---

# 7. Security Requirements

The system must move toward:

- least privilege
- zero ambient authority
- centralized policy enforcement
- sandboxed code execution
- scoped data access
- tenant isolation
- controlled tool exposure
- context hygiene
- auditability
- circuit breakers
- rollback for high-impact changes

No student code should execute directly in the main API runtime.

---

# 8. Evaluation Requirements

Agentic features require evaluation beyond unit tests.

Evaluate:

- intent satisfaction
- functional correctness
- pedagogical quality
- solution leakage
- trajectory quality
- routing correctness
- Skill activation
- cost and latency
- self-repair
- session convergence
- safety

Use real failure cases and user corrections to improve evaluation datasets.

---

# 9. Observability Requirements

Important executions should be traceable.

Capture where appropriate:

- trace ID
- session ID
- task
- routing decision
- workflow
- Skill version
- agent version
- model call
- tool call
- retrieval
- policy decision
- latency
- token usage
- failure
- evaluation result

Never log secrets unnecessarily.

---

# 10. Spec-Driven Development

Major changes begin with specifications.

Use:

specs/
  architecture/
  features/
  api/
  data/
  security/
  evaluation/
  deployment/

Do not implement large features from vague prompts.

---

# 11. Development Discipline

For new architecture:

design before code.

For features:

follow approved specification.

For bugs:

reproduce before fixing.

For persistent changes:

checkpoint where appropriate.

For agent behavior:

evaluate, do not merely unit test.

For security-sensitive operations:

enforce policy outside the model prompt.

---

# 12. Implementation Priority

Do not attempt to build the entire target architecture in one uncontrolled rewrite.

Prefer phased evolution.

## Phase A

- audit current repository
- document current architecture
- identify technical debt
- establish specs
- establish typed contracts
- establish tests
- establish baseline observability

## Phase B

- rationalize agents vs Skills vs workflows
- implement progressive hinting properly
- improve structured state
- strengthen retrieval boundaries
- add evaluation datasets

## Phase C

- add policy gateway
- add sandboxed execution
- improve tracing
- add security tests
- add trajectory evaluation

## Phase D

- production deployment
- CI/CD
- cloud observability
- scaling
- reliability
- cost controls

## Phase E

Only if justified:

- A2A interoperability
- advanced MCP ecosystem
- generative UI
- graph-native code intelligence
- self-improving Skill proposals

---

# 13. Non-Negotiable Rule for Coding Agents

Before making major changes:

1. inspect the repository
2. understand existing behavior
3. read relevant specifications
4. identify gaps
5. propose a plan
6. explain trade-offs
7. implement in small reviewable increments
8. add tests
9. run tests
10. run relevant evaluations
11. update documentation
12. report remaining risks

Do not perform a blind rewrite.

Do not delete working functionality without justification.

Do not fabricate successful test results.

Do not claim production readiness without evidence.

---

# 14. Final Engineering Standard

AlgoFlow should be judged by whether it is:

- useful
- technically correct
- pedagogically intelligent
- secure
- observable
- evaluable
- maintainable
- deployable
- recoverable
- cost-aware

Not by how many agents it contains.