# AlgoFlow Agent Skills Principles

## Purpose

This document defines how reusable procedural expertise should be represented and evaluated.

---

# 1. Specialization Does Not Automatically Mean Another Agent

Before creating a specialist agent, ask:

1. Does it require independent state?
2. Does it require separate permissions?
3. Does it require genuine parallel execution?
4. Does it require a different model?
5. Does it require multi-turn autonomous collaboration?
6. Does it require independent deployment?
7. Does it require lifecycle ownership?

If the answer is no, prefer an Agent Skill, deterministic component, or workflow.

---

# 2. Primitive Selection

Use this mental model.

## Tool

Question:

What can the system access or execute?

Examples:

- query learner history
- retrieve documents
- execute code
- query analytics
- fetch submissions

## Skill

Question:

How should the agent perform a reusable procedure?

Examples:

- generate progressive hints
- review code without solution leakage
- analyze complexity
- diagnose recursion mistakes
- conduct interview feedback
- classify common DSA patterns

## Agent

Question:

Who owns an autonomous responsibility?

Examples:

- coordinator
- long-running mock interviewer
- longitudinal planner

## Workflow

Question:

What predictable sequence of stages must execute?

Examples:

- submission analysis
- post-interview report generation
- study-plan refresh
- code review pipeline

---

# 3. Progressive Disclosure

Skills SHOULD use progressive disclosure.

Keep always-visible metadata minimal.

Load detailed instructions only when the Skill activates.

Load supporting references only when needed.

Execute deterministic scripts without copying their full contents into model context.

Suggested structure:

skills/
  progressive-hinting/
    SKILL.md
    scripts/
    references/
    assets/

  code-reviewing/
    SKILL.md
    scripts/
    references/
    assets/

  interview-feedback/
    SKILL.md
    references/
    assets/

---

# 4. Skill Description Is a Routing Contract

Every Skill description MUST define:

- what the Skill does
- positive activation conditions
- negative boundaries
- closely related tasks it must not handle

Bad:

"Helps with coding problems."

Good:

"Generates staged, non-spoiling hints for DSA and coding interview problems based on the learner's current reasoning, code, and previous hints. Use when the learner asks for a hint, says they are stuck, requests guidance without a full solution, or needs the next conceptual step. Do not use for full-solution generation, final code review, mock-interview scoring, or study-plan creation."

---

# 5. Evaluation-Driven Skill Development

Before implementing or substantially modifying a Skill, define evaluation cases.

Each case SHOULD contain:

- case_id
- input
- expected Skill
- expected behavior
- forbidden behavior
- expected tools
- acceptable trajectory constraints
- expected output structure
- scoring rubric

Do not evaluate only final prose.

Evaluate:

- trigger correctness
- execution correctness
- tool trajectory
- regression
- token behavior under realistic co-loading

---

# 6. Progressive Hinting Requirements

The progressive hinting capability MUST:

- inspect the learner's current reasoning
- avoid restarting from zero unnecessarily
- adapt to demonstrated expertise
- avoid revealing the full solution unless explicitly appropriate
- account for previous hints
- identify misconceptions
- provide the smallest useful next step
- preserve learner ownership of reasoning

It MUST distinguish:

- learner asks whether an idea is correct
- learner asks for one hint
- learner asks for another hint
- learner asks for full solution
- learner asks for code
- learner asks for explanation after solving

---

# 7. Skill Collision Testing

Skills must not be tested only in isolation.

Test realistic combinations such as:

- progressive-hinting
- Java-code-reviewing
- complexity-analysis
- DP-pattern-recognition
- interview-mode
- solution-leakage-prevention

Measure:

- incorrect activation
- missed activation
- conflicting instructions
- context growth
- output degradation

---

# 8. Read / Draft / Act Governance

Classify capabilities.

## Read

Examples:

- inspect code
- retrieve progress
- analyze weaknesses
- identify patterns

## Draft

Examples:

- propose study plan
- draft feedback
- recommend problems
- suggest profile changes

## Act

Examples:

- persist study plan
- schedule interview
- mutate learner profile
- send notification
- modify records

Act operations require policy evaluation.

High-risk actions may require human approval.

---

# 9. Context Engineering

The context window MUST NOT be treated as:

- a database
- a session store
- a workflow log
- an analytics warehouse
- a dump of learner history
- a dump of every Skill

Use:

- PostgreSQL for durable structured state
- vector retrieval for semantic knowledge
- session services for runtime state
- Skills for procedural knowledge
- tools for capabilities
- agents for autonomous responsibilities

---

# 10. Structured Workflow State

Workflow stages SHOULD exchange:

- typed state
- artifact references
- IDs
- bounded summaries
- evidence
- explicit status

Do not use the context window as a message bus.

---

# 11. Skill Improvement

Production traces may be used to propose Skill improvements.

Preferred flow:

interaction
    ->
trace
    ->
failure or repeated success pattern
    ->
proposed Skill change
    ->
evaluation suite
    ->
regression suite
    ->
human review
    ->
controlled promotion

An agent-written Skill MUST NOT automatically promote itself to production.