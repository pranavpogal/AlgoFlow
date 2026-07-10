# AlgoFlow Phased Migration Plan

Date: 2026-07-05

This plan is dependency-aware and intentionally avoids a blind rewrite. Each phase should end with a phase completion report.

## Phase 0 — Audit and Baseline

Objective: Establish truth about current behavior.

Current problem: Docs and architecture claims exceed runtime implementation.

Principles applied: CH-05, SPEC-01, AG-01, SEC-04.

Files/components affected: `docs/audits/*`, `docs/whitepaper-traceability.md`, `docs/architecture/system-overview.md`, `docs/adr/*`.

Implementation tasks:

- Inspect repository and mandatory guidance files.
- Record runtime paths.
- Run baseline tests/builds.
- Create audit, traceability, gap, ADR, architecture, threat model, migration artifacts.

Migration risks: Documentation may reveal uncomfortable gaps; that is desired.

Rollback plan: Revert docs-only changes.

Tests: Existing tests/build commands recorded.

Evals: None yet; eval directories created as future structure.

Acceptance criteria: Gate artifacts exist and cite evidence.

Prerequisites: None.

## Phase 1 — Spec and Contract Foundations

Objective: Make behavior explicit before implementation.

Current problem: No feature specs, no error contracts, no request IDs, and docs drift.

Principles applied: SPEC-01, SPEC-02, CH-05.

Files/components affected: `specs/`, `backend/app/schemas`, `docs`, README.

Implementation tasks:

- Create specs for adaptive hinting, learner model, code review, ADK runtime, memory, security, evaluation.
- Add API error envelope spec.
- Add request ID/trace ID contract.
- Correct README and architecture docs to separate current vs target.

Risks: Too much documentation without behavior; keep specs actionable.

Rollback: Specs are additive; revert incorrect docs.

Tests: Schema import tests; docs link checks if available.

Evals: Define first hint leakage and routing fixtures.

Acceptance criteria: Major future features have specs with BDD scenarios and acceptance criteria.

Prerequisites: Phase 0.

## Phase 2 — Runtime and Boundary Cleanup

Objective: Establish service boundaries, trace context, and failure contracts.

Current problem: Routes call services directly with no request IDs, structured errors, or policy context.

Principles applied: CH-04, AG-03, SPEC-04.

Affected components: FastAPI middleware, schemas, services, logging.

Tasks:

- Add request/trace ID middleware.
- Add consistent error envelopes.
- Add typed `TaskContext` and `RequestContext`.
- Ensure documented test command works.
- Fix frontend build type error.

Risks: API response changes affect frontend.

Rollback: Feature flag new error envelopes if needed.

Tests: API contract tests, frontend build, backend pytest.

Evals: None required beyond trajectory fixtures definition.

Acceptance criteria: Requests are traceable; baseline tests/build pass.

Prerequisites: Phase 1.

## Phase 3 — Real ADK Runtime Integration

Objective: Put ADK in the live path where justified.

Current problem: Agents are decorative definitions.

Principles applied: AG-02, AG-04, TOOL-02.

Affected components: `backend/app/agents`, runtime wrapper, context builder, tool gateway.

Tasks:

- Investigate installed ADK 2.2.0 APIs.
- Implement bounded runner/session wrapper.
- Validate structured outputs.
- Add deterministic fallback for local tests.
- Trace routing decisions and model/tool latency.

Risks: API latency/cost, malformed model outputs.

Rollback: Switch route to deterministic service fallback.

Tests: mocked ADK integration tests, timeout tests.

Evals: routing and trajectory evals.

Acceptance criteria: At least one route shows real ADK run/session/events in trace.

Prerequisites: Phases 1-2.

## Phase 4 — Agent / Skill / Workflow Rationalization

Objective: Replace decorative agents with justified primitives.

Current problem: Most named agents are better as Skills or workflows.

Principles applied: AG-01, SKILL-01.

Tasks:

- Add Skill contracts for hinting, code review, classification, pattern transfer.
- Define workflow state for code review and study planning.
- Retain only justified agents in runtime.

Risks: Naming churn; preserve user-facing product language separately.

Rollback: Keep old service methods behind fallback.

Tests: Skill activation tests.

Evals: Skill trigger/collision evals.

Acceptance criteria: Each capability has documented primitive and test coverage.

Prerequisites: Phase 1.

## Phase 5 — Learning Event Foundation

Objective: Preserve immutable learning evidence.

Current problem: Attempts/mistakes are shallow and profile defaults are fictional.

Principles applied: ADR 0003, SPEC-01.

Tasks:

- Specify and add learning event model.
- Persist hint, classification, submission, interview, misconception events.
- Add idempotency keys where needed.

Risks: Migration complexity.

Rollback: Keep existing tables; disable event consumers.

Tests: DB integration and event append tests.

Evals: event coverage checks.

Acceptance criteria: Important state updates can cite event evidence.

Prerequisites: Phase 2.

## Phase 6 — Learner Intelligence

Objective: Build evidence-based learner state.

Current problem: Static `DEFAULT_PROFILE` misleads users.

Tasks:

- Replace fictional defaults with unknown/low-confidence state.
- Add mastery/misconception update algorithm.
- Include confidence and evidence references.

Risks: Sparse data may produce less flashy dashboards.

Rollback: Preserve old analytics behind demo mode only.

Tests: deterministic mastery update tests.

Evals: personalization evals.

Acceptance criteria: New user profile contains no fabricated strengths/weaknesses.

Prerequisites: Phase 5.

## Phase 7 — Adaptive Hinting

Objective: Replace static ladder with learner-aware non-leaking guidance.

Current problem: `user_attempt` and previous hints are mostly ignored.

Tasks:

- Implement progressive hinting Skill.
- Use current reasoning/code/prior hints/misconceptions.
- Enforce solution leakage controls.

Risks: LLM may over-reveal.

Rollback: Deterministic safe hint fallback.

Tests: API and state tests.

Evals: hint leakage/helpfulness suite.

Acceptance criteria: BDD scenarios pass and leakage rate is below threshold.

Prerequisites: Phases 1, 5, 6.

## Phase 8 — Code Intelligence

Objective: Add structural code evidence.

Current problem: String heuristics only.

Tasks:

- Choose first language adapter, likely Python.
- Add parser/AST diagnostics.
- Produce structured findings with evidence spans.

Risks: False positives.

Rollback: Keep heuristic fallback.

Tests: parser/diagnostic fixtures.

Evals: bug detection precision/recall.

Acceptance criteria: Review includes deterministic structural evidence.

Prerequisites: Phase 1.

## Phase 9 — Secure Execution Boundary

Objective: Prevent unsafe execution while defining future execution path.

Current problem: No execution architecture exists.

Tasks:

- Define execution request/result schema.
- Implement production-disabled safe stub.
- Document sandbox requirements.

Risks: Users expect execution; communicate disabled state.

Rollback: Remove endpoint or keep disabled.

Tests: execution denied in API process.

Evals: none initially.

Acceptance criteria: No user code can execute in FastAPI.

Prerequisites: Phase 8 spec.

## Phase 10 — Counterexample Engine

Objective: Find failing cases once sandbox exists.

Current problem: No test execution.

Tasks: differential/property testing, minimization, pedagogical explanations.

Prerequisites: Phase 9 real sandbox.

## Phase 11 — Memory and Context Engineering

Objective: Make memory explicit, scoped, and useful.

Current problem: Vector writes do not equal memory.

Tasks: memory taxonomy, retrieval policy, context builder, provenance, reranking, budgets.

Prerequisites: Phases 2, 5, 14 basics.

## Phase 12 — Stateful Mock Interviews

Objective: Replace keyword simulator.

Tasks: state machine, transcript persistence, rubric, score evidence, adaptive follow-ups.

Prerequisites: Phases 5-6.

## Phase 13 — Evaluation Platform

Objective: Make AI quality measurable.

Tasks: eval runner, datasets, metrics, CI smoke evals.

Prerequisites: Phase 1 specs; can begin early.

## Phase 14 — Policy and Security Hardening

Objective: Enforce auth, authorization, and tool/state mutation policy.

Tasks: auth boundary, IDOR tests, structural gateway, semantic intent checks, circuit breakers.

Prerequisites: Phase 2.

## Phase 15 — Observability and Reliability

Objective: Trace and recover from failures.

Tasks: OpenTelemetry-compatible spans, metrics, retries/timeouts, failure categories.

Prerequisites: Phase 2 trace context.

## Phase 16 — Google Cloud Readiness

Objective: Prepare stateless deployable services.

Tasks: production config, Cloud SQL, Secret Manager plan, container hardening, health checks.

Prerequisites: Phases 2, 14, 15.

## Phase 17 — CI/CD and Infrastructure as Code

Objective: Automate quality gates and reproducible infrastructure.

Tasks: GitHub Actions/Cloud Build, selected evals, container build, Terraform dev env.

Prerequisites: stable tests/evals.

## Phase 18 — Final Hardening

Objective: Performance, cost, security, documentation, evaluation regression, deployment verification.

Tasks: security review, cost analysis, docs audit, load/perf smoke, rollback rehearsal.

Prerequisites: previous phases.
