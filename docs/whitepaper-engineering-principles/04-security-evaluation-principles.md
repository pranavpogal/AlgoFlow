# AlgoFlow Security and Evaluation Principles

## Purpose

This document defines security, observability, and evaluation requirements for AlgoFlow.

Security and evaluation are separate dimensions.

Security asks:

Did the system remain within authorized boundaries?

Evaluation asks:

Did the system perform the task well enough to ship?

Both are required.

---

# 1. Security Domains

AlgoFlow MUST explicitly consider:

- infrastructure and networking
- data
- models and prompts
- application runtime
- identity and access management
- observability and incident response
- governance

---

# 2. Student Code Execution

Student-generated or user-submitted code MUST NOT execute directly inside:

- the FastAPI process
- the coordinator runtime
- the host machine
- a privileged production container

Preferred architecture:

API
    ->
Execution Service
    ->
Ephemeral Sandbox
    ->
Compile
    ->
Run
    ->
Capture Bounded Result
    ->
Destroy Environment

The sandbox SHOULD enforce:

- CPU limit
- memory limit
- wall-clock timeout
- process-count limit
- filesystem isolation
- network disabled by default
- no host filesystem access
- no inherited secrets
- no cloud credentials
- ephemeral state

---

# 3. Dependency Safety

Never autonomously execute model-generated dependency installation without verification.

Examples requiring control:

- pip install
- npm install
- Maven dependency retrieval
- system package installation

Preferred flow:

dependency proposal
    ->
registry verification
    ->
policy check
    ->
version validation
    ->
security scan
    ->
sandbox installation

---

# 4. Context as Security Perimeter

Security depends not only on authentication but also on:

- loaded Skills
- retrieved documents
- visible tools
- selected agent
- injected memory
- accessible files
- accessible database rows
- current user intent
- environment

Progressive disclosure is therefore also a security mechanism.

---

# 5. Zero Ambient Authority

No agent should receive broad standing authority merely for convenience.

Forbidden pattern:

Coordinator
    ->
full database admin
    ->
all vector data
    ->
all cloud credentials
    ->
all external APIs

Prefer narrowly scoped, temporary capabilities.

---

# 6. Policy Gateway

Sensitive operations SHOULD pass through centralized policy enforcement.

The policy layer SHOULD evaluate:

- user identity
- agent identity
- task identity
- current intent
- requested capability
- resource scope
- environment
- risk

---

# 7. Intent Drift

Track whether execution remains aligned with the original task.

Example:

Original intent:
"Give me one hint."

Aligned actions:

- inspect problem
- inspect current attempt
- inspect previous hints
- generate one bounded hint

Drift:

- generate full solution
- rewrite code
- mutate study plan
- store unrelated memory
- invoke unrelated external service

Unexpected actions should reduce trust and may trigger denial or escalation.

---

# 8. Circuit Breakers

Define conditions that can stop execution.

Examples:

- repeated tool failure
- unexpected tool sequence
- policy violations
- excessive retries
- abnormal token growth
- unauthorized resource request
- repeated intent drift

Circuit-breaker behavior may include:

- stop execution
- revoke temporary capability
- quarantine task
- preserve trace
- request human review
- rollback state

---

# 9. Checkpoint and Rollback

Before high-impact persistent mutations:

current state
    ->
checkpoint
    ->
proposed action
    ->
verification
    ->
commit or rollback

---

# 10. Observability

A final response is not sufficient evidence.

Trace where appropriate:

- trace ID
- session ID
- user intent
- coordinator decision
- selected workflow
- activated Skill and version
- model calls
- tool calls
- retrievals
- policy decisions
- latency
- token usage
- retries
- failures
- evaluation results

Do not log secrets or unnecessary sensitive data.

---

# 11. Evaluation Dimensions

Evaluate at least:

1. Intent satisfaction
2. Functional correctness
3. Visual and behavioral correctness
4. Cost and efficiency
5. Quality and conventions
6. Trajectory quality
7. Self-repair behavior

Safety is transversal across all dimensions.

---

# 12. Intent Satisfaction

Technical correctness alone is insufficient.

Example:

User:
"I think each rod has left/right/skip. Am I thinking correctly? Don't give the solution."

A mathematically correct full solution is still a failure because it violates intent.

---

# 13. Trajectory Evaluation

Evaluate:

- correct routing
- correct Skill activation
- appropriate context retrieval
- appropriate tool selection
- unnecessary tool calls
- coherent execution order
- failure recovery
- policy compliance

A correct final answer produced through a fragile trajectory is not sufficient.

---

# 14. Evaluation Methods

Use complementary methods:

- unit tests
- integration tests
- security tests
- LLM-as-judge
- browser tests
- trajectory inspection
- human review
- production evaluation

No single method is sufficient.

---

# 15. Session-Level Evaluation

Evaluate whether a multi-turn session converges.

Metrics may include:

- successful convergence
- turns to convergence
- user corrections
- abandonment
- token cost
- repeated misunderstanding
- successful recovery

---

# 16. User Corrections as Failure Data

Treat corrections such as:

- "Don't give the solution."
- "I already know recursion."
- "I asked for a hint."
- "Explain why my state is wrong."
- "Don't rewrite my code."
- "Use Java."
- "You're repeating yourself."

as valuable labeled failure signals.

Cluster recurring failures and use them to improve:

- Skills
- routing
- prompts
- evaluation cases
- workflow design

Do not automatically modify production behavior without evaluation gates.