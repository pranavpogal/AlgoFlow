# Current System Audit

Date: 2026-07-05
Repository: `/Users/pranavpogal/Documents/New project 2`

## A. Executive Summary

AlgoFlow is currently a runnable prototype scaffold for a coding-interview mentor. It has a FastAPI backend, a Next.js frontend, SQLAlchemy models, ChromaDB-backed vector writes, Pydantic schemas, deterministic tools, and Google ADK agent definitions. The API can return structured responses for problem analysis, hints, code review, study plans, recommendations, pattern transfer, analytics, and mock interview turns.

What genuinely works:

- FastAPI route registration and in-process ASGI calls for `/`, `/api/v1/health`, `/api/v1/problems/analyze`, and `/api/v1/hints/next` returned HTTP 200 during audit.
- Deterministic pattern classification works for curated cases such as `Largest Divisible Subset`.
- SQLite tables are created on startup through `backend/app/main.py::lifespan` -> `backend/app/db/init_db.py::init_db`.
- Pydantic schemas provide typed request/response contracts in `backend/app/schemas/mentor.py`.
- Backend tool unit tests pass when run with `PYTHONPATH=.`.

What is partially implemented:

- ChromaDB vector writes exist in `backend/app/memory/vector_store.py::VectorMemory.add`, but retrieval is not integrated into most decision paths.
- Structured relational memory exists for users, problem attempts, mistakes, and interview sessions, but learner state updates are shallow and mostly count-based.
- Frontend pages exist and call APIs, but many use `demo-user` and hardcoded dashboard/profile data.

What is simulated or disconnected:

- Google ADK agents are defined in `backend/app/agents/adk_agents.py`, but FastAPI routes call `backend/app/services/mentor_service.py` directly and do not invoke an ADK Runner/session/event runtime.
- The coordinator agent is not in the actual request path.
- Code review is heuristic string matching in `backend/app/tools/code_review.py::review_code_heuristics`.
- Mock interview behavior is keyword-driven in `backend/app/services/mentor_service.py::interview_turn`, not state-machine or evidence-backed.
- Analytics include synthetic values in `backend/app/services/mentor_service.py::analytics`, especially static weekly velocity.

Highest-risk gaps:

- Documentation and UI currently claim stronger ADK/multi-agent runtime behavior than implementation proves.
- User identity is client-supplied and defaults to `demo-user`, creating IDOR/cross-user memory risks in any deployed environment.
- No authentication, authorization, policy gateway, trace propagation, or production observability exists.
- No safe code execution boundary exists; current review avoids execution, but future execution would be high-risk without sandboxing.
- No evaluation harness exists for routing, hint leakage, code review quality, memory retrieval, or interview quality.

## B. Repository Map

- `backend/app/main.py`: FastAPI application, CORS, lifespan DB initialization, root route.
- `backend/app/api/routes.py`: API route handlers; thin route layer delegates to `mentor_service`.
- `backend/app/services/mentor_service.py`: Current application orchestration. This is the true runtime path for mentor features.
- `backend/app/agents/adk_agents.py`: ADK agent definitions and sub-agent topology. Imported nowhere in the live route path.
- `backend/app/agents/instructions.py`: Prompt/instruction strings for named agents.
- `backend/app/tools/problem_intelligence.py`: Curated/heuristic DSA classification and related-problem lookup.
- `backend/app/tools/code_review.py`: String-based code review heuristics.
- `backend/app/tools/learning_tools.py`: Readiness score and study-plan construction.
- `backend/app/memory/repository.py`: SQLAlchemy persistence helpers and snapshot aggregation.
- `backend/app/memory/vector_store.py`: ChromaDB/JSONL vector memory adapter.
- `backend/app/db/base.py`: SQLAlchemy models for users, attempts, mistakes, interviews.
- `backend/app/schemas/mentor.py`: Pydantic API schemas.
- `frontend/src/app/*`: Next.js pages for the product surface.
- `docs/whitepaper-engineering-principles/*`: Mandatory engineering guidance.
- `backend/tests/*`: Four deterministic tests for code review and pattern classification.

## C. Runtime Path

Actual path for problem analysis:

```text
frontend/src/app/problem-analysis/page.tsx
  -> apiPost('/problems/analyze') in frontend/src/lib/api.ts
  -> backend/app/api/routes.py::analyze_problem
  -> backend/app/services/mentor_service.py::MentorService.analyze_problem
  -> backend/app/tools/problem_intelligence.py::detect_problem_pattern
  -> backend/app/memory/repository.py::remember_attempt
  -> backend/app/memory/vector_store.py::vector_memory.add
  -> TopicAnalysis response
```

Actual path for hints:

```text
frontend/src/app/hints/page.tsx
  -> apiPost('/hints/next')
  -> backend/app/api/routes.py::next_hint
  -> backend/app/services/mentor_service.py::MentorService.next_hint
  -> backend/app/memory/repository.py::user_memory_snapshot
  -> backend/app/tools/problem_intelligence.py::detect_problem_pattern
  -> static hint ladder response
```

Actual path for code review:

```text
frontend/src/app/code-review/page.tsx
  -> apiPost('/code-review')
  -> backend/app/api/routes.py::code_review
  -> backend/app/services/mentor_service.py::MentorService.review_code
  -> backend/app/tools/code_review.py::review_code_heuristics
  -> remember_attempt / remember_mistakes / vector_memory.add
  -> CodeReviewResponse
```

Actual path for mock interview:

```text
frontend/src/app/mock-interview/page.tsx
  -> apiPost('/mock-interview/turn')
  -> backend/app/api/routes.py::interview_turn
  -> backend/app/services/mentor_service.py::MentorService.interview_turn
  -> keyword matching on payload.message
  -> generated session_id only if missing; no DB transcript persistence
```

ADK status:

- `google-adk 2.2.0` is installed.
- `backend/app/agents/adk_agents.py` defines `root_agent` and sub-agents.
- No route imports `root_agent`.
- No ADK Runner/session/event invocation was found.
- Therefore ADK is available and decorative at runtime, not yet production-path orchestration.

## D. Agent Architecture Audit

| Agent | Defined | Invoked | Stateful | Tools | Real Runtime Path | Justified as Agent? | Better Primitive Now |
|---|---:|---:|---:|---|---:|---|---|
| coordinator_agent | yes | no | no | none | no | yes later for orchestration | agent after ADK runtime integration |
| topic_agent | yes | no | no | `detect_problem_pattern` | no | no | classifier Skill/tool/workflow node |
| hint_agent | yes | no | no | none | no | no | progressive-hinting Skill/workflow |
| review_agent | yes | no | no | `review_code_heuristics` | no | no | code-review Skill + tools |
| memory_agent | yes | no | no | none | no | no | memory service + policy-gated tools |
| planner_agent | yes | no | no | `build_weekly_plan` | no | maybe later if longitudinal | deterministic workflow now |
| recommendation_agent | yes | no | no | `recommend_related_problems` | no | no | recommendation service/tool |
| mistake_tracker_agent | yes | no | no | none | no | no | event/misconception classifier Skill |
| interviewer_agent | yes | no | no | none | no | yes later | stateful interview agent/workflow |
| analytics_agent | yes | no | no | `readiness_score` | no | no | analytics engine + interpretation Skill |
| pattern_transfer_agent | yes | no | no | none | no | no | pattern-transfer Skill |

## E. Data and Memory Audit

Database usage:

- SQLite default URL: `sqlite+aiosqlite:///./algoflow.db` in `backend/app/core/config.py`.
- Tables: `users`, `problem_attempts`, `mistakes`, `interview_sessions` in `backend/app/db/base.py`.
- No Alembic or schema migration system.
- No auth-derived user identity; `user_id` is accepted from client request bodies or path params.

ChromaDB usage:

- `VectorMemory.add` writes documents to ChromaDB or JSONL fallback.
- `VectorMemory.search` exists but is not called by `mentor_service`.
- Vector memory therefore records events but does not materially personalize most responses.

Session state:

- Mock interview returns a `session_id`, but no durable transcript update occurs in `MentorService.interview_turn`.
- Frontend stores interview turns in component state only.

User isolation:

- User isolation depends entirely on client-supplied `user_id`; no authentication or authorization boundary exists.

## F. Adaptive Learning Audit

Learner model:

- `DEFAULT_PROFILE` in `backend/app/memory/repository.py` gives every new user fixed strong/weak topics and mastery scores.
- This violates evidence-based learner modeling because new users are assigned fictional weaknesses.

Mastery:

- `readiness_score` computes a score from static `pattern_mastery`, mistake category count, and attempt count.
- No Bayesian/Elo/BKT/temporal update mechanism exists.

Hint adaptation:

- Hints use a static five-item ladder.
- Personalization is limited to a mentor note if detected pattern appears in `weak_topics`.
- `user_attempt`, previous hint text, time spent, misconception evidence, and current code are not analyzed.

Recommendations:

- Related problems are static by pattern, not personalized by learner history.

## G. Code Intelligence Audit

Current capability:

- `review_code_heuristics` detects substrings such as `range(len`, `i+1`, `<=`, `dp`, `while left`.
- No parser, AST, language adapters, static analysis framework, compilation, execution, tests, counterexamples, or complexity proof exists.

Security-positive fact:

- The current system does not execute submitted code, avoiding immediate arbitrary-code-execution exposure.

Gap:

- The frontend claims multi-language review, but backend support is language-agnostic string inspection.

## H. Security Audit

Risks found:

- No authentication or authorization.
- Client-supplied `user_id` enables IDOR if deployed.
- No tenant boundary for relational or vector memory beyond `user_id` filter.
- No input size limits on problem descriptions or code submissions.
- No policy gateway for act operations such as memory writes.
- No prompt-injection defense for future live LLM/ADK path.
- No centralized structured error envelope; raw 500s can surface during backend failures.
- No secure code execution service; future execution must not happen in FastAPI.
- `.env` is ignored, but secret-management integration is absent.

## I. Observability Audit

Current state:

- Uvicorn/FastAPI default logs only.
- No request IDs, trace IDs, session IDs, selected agent/Skill metadata, tool latency, model latency, token usage, policy decisions, or retrieval metrics.
- No OpenTelemetry instrumentation.
- No persisted agent/tool run tables.

## J. Testing and Evaluation Audit

Baseline commands run:

- `backend/.venv/bin/ruff check app tests`: passed.
- `backend/.venv/bin/pytest -q`: failed with `ModuleNotFoundError: No module named 'app'` because documented command lacks package path/install path behavior.
- `PYTHONPATH=. backend/.venv/bin/pytest -q`: passed, 4 tests.
- `npm run build` in `frontend`: failed type-checking in `src/components/Nav.tsx` because typed routes reject plain `string` href values.
- Socket-based uvicorn smoke start failed in sandbox with `operation not permitted` on bind; in-process ASGI requests succeeded.

No evals exist for:

- routing accuracy
- Skill triggering
- hint leakage
- hint helpfulness
- code review precision/recall
- memory retrieval quality
- personalization quality
- interview quality
- trajectory correctness

## K. Cloud Readiness Audit

Current readiness:

- Dockerfiles exist.
- Docker Compose exists.
- Backend can use environment variables.

Gaps:

- SQLite local file and Chroma local path are default durable stores.
- No migrations.
- No production auth/session boundary.
- No stateless durable session service for interviews.
- Frontend Dockerfile runs `npm run dev`, not production `next start`.
- No health/readiness endpoints beyond simple health.
- No IaC, CI/CD, Secret Manager, Cloud SQL, Artifact Registry, or Cloud Run configuration.
- Local `.chroma`, `.venv`, `.next`, and database artifacts exist in workspace and should remain ignored.

## L. Documentation Accuracy

Potentially misleading claims:

- README: “Google ADK multi-agent architecture with a root coordinator and specialized sub-agents.” Accurate as definitions, misleading as runtime behavior.
- README: “long-term user modeling” overstates current static default profile and count-based snapshots.
- README: “RAG-ready vector memory” is accurate if interpreted as readiness, not actual RAG personalization.
- `docs/ARCHITECTURE.md` diagram shows `API -> Coordinator -> Agents`; actual path is `API -> MentorService -> deterministic tools`.
- Frontend copy says “specialized Google ADK agents”; current UI/API path does not invoke them.

## Conflicts and Tensions From Principles

- Agent ambition vs least-autonomous primitive: current named agents are useful product vocabulary, but most should become Skills/tools/workflows until independent autonomy is justified.
- Rapid demo value vs documentation truthfulness: current prototype demos well, but docs must avoid claiming production runtime behavior.
- Memory writes vs privacy/security: writing every event supports personalization, but without auth/policy/provenance it creates tenant leakage risk.
- Cloud readiness vs local simplicity: SQLite/Chroma local are useful for development, but must be abstracted before production deployment.

## Premature or Deferred Principles

- A2A interoperability, advanced MCP ecosystem, generative UI, GKE, and full Vertex AI Vector Search are premature.
- Secure code execution should first be an interface and disabled safe stub, not a fake sandbox.
- ADK runtime integration should follow specs/contracts/observability, not be bolted on merely to satisfy architecture diagrams.
