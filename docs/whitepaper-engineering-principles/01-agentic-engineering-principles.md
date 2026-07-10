# AlgoFlow Agentic Engineering Principles

## Purpose

This document defines engineering constraints for the AlgoFlow agentic system.

AlgoFlow is a serious production-oriented agentic coding interview mentorship platform. It is not a toy multi-agent demo. Architectural decisions must be justified by correctness, reliability, observability, security, evaluation quality, maintainability, and user value.

The implementation agent MUST treat this document as a source of engineering requirements.

---

# 1. Core Agentic Engineering Principle

Do not build agentic behavior merely because an LLM can perform a task.

For every capability, first determine whether it should be implemented as:

- deterministic application logic
- a tool
- a reusable Agent Skill
- a deterministic workflow
- an LLM-powered component
- an autonomous agent
- a multi-agent collaboration

Prefer the least autonomous mechanism that correctly satisfies the requirement.

Do not create unnecessary agents.

---

# 2. Coordinator Responsibility

The coordinator is responsible for high-level orchestration.

It SHOULD:

- interpret user intent
- identify the current task
- determine whether clarification is needed
- choose an appropriate workflow
- delegate bounded responsibilities
- aggregate structured outputs
- enforce workflow limits
- handle failures and escalation
- preserve user intent across the execution

It SHOULD NOT:

- perform every specialist task itself
- receive every available tool
- directly access unrestricted databases
- contain all domain instructions in one giant prompt
- become an all-powerful monolithic agent
- silently mutate persistent user state

---

# 3. Specialist Design

A specialist must have:

- a narrow responsibility
- explicit capability boundaries
- bounded context
- explicit input contracts
- explicit output contracts
- explicit tool permissions
- explicit data permissions
- timeout behavior
- retry behavior
- escalation behavior
- observability metadata

Do not create a specialist whose responsibility substantially overlaps another specialist without documented justification.

---

# 4. Agent Selection Rule

Create an autonomous agent only when the capability genuinely benefits from one or more of:

- independent state ownership
- long-running task ownership
- multi-turn collaboration
- pause and resume behavior
- independent deployment
- separate security boundaries
- different model requirements
- meaningful parallel execution
- autonomous replanning
- lifecycle ownership

Otherwise prefer:

- a Skill
- a tool
- deterministic logic
- a workflow node

---

# 5. Candidate AlgoFlow Responsibilities

The following are architectural hypotheses, not mandatory implementation decisions.

## Coordinator

Likely a genuine agent because it owns orchestration and task routing.

## Mock Interviewer

Likely a genuine agent because it may own:

- long-lived interview state
- adaptive questioning
- multi-turn progression
- interruption and resumption
- dynamic follow-up decisions

## Study Planner

May be a genuine agent only if it owns:

- longitudinal learner goals
- persistent planning state
- replanning
- progress-aware decisions
- multi-step plan evolution

Otherwise implement it as a bounded workflow.

## Problem Classification

Prefer deterministic logic, structured LLM classification, or a Skill before creating an agent.

## Progressive Hinting

Prefer a Skill or bounded workflow unless independent autonomous state is demonstrably required.

## Code Review

Prefer a Skill plus tools and deterministic analysis unless long-running autonomous review responsibility is required.

## Analytics

Prefer tools plus deterministic analytics plus an interpretation Skill.

---

# 6. Structured Delegation

Agents and workflow stages SHOULD exchange bounded structured state.

Prefer:

- typed schemas
- task IDs
- artifact IDs
- trace IDs
- database references
- explicit status fields
- structured evidence

Avoid:

- unlimited raw conversation dumps
- unbounded free-form handoff text
- accumulated hidden reasoning
- passing the entire session to every specialist

---

# 7. Workflow Control

Every autonomous loop MUST have explicit bounds.

Define where relevant:

- maximum iterations
- maximum retries
- timeout
- token budget
- tool-call budget
- escalation condition
- terminal success condition
- terminal failure condition

No unbounded agent loop is permitted.

---

# 8. Failure Handling

Failures must be explicit.

Possible states SHOULD include:

- pending
- running
- succeeded
- failed
- timed_out
- denied_by_policy
- awaiting_human_approval
- cancelled
- partially_completed

Do not silently convert failures into apparently successful responses.

---

# 9. Human Control

High-impact operations require explicit governance.

The system must distinguish:

- read
- draft
- act

Read operations are generally low risk.

Draft operations may generate proposals without persistence.

Act operations mutate state or affect external systems and require policy evaluation.

High-risk act operations may require human approval.

---

# 10. Production Requirement

The architecture must optimize for:

- correctness
- pedagogical quality
- security
- observability
- evaluation
- recoverability
- maintainability
- cost awareness
- latency awareness
- user intent preservation

Do not optimize for the number of agents.

Do not describe the system as advanced merely because it is multi-agent.