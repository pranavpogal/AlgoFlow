# AlgoFlow

**AlgoFlow is an adaptive coding interview mentorship platform under active production transformation.**

The product goal is to help learners improve at coding interviews by teaching problem-solving patterns, tracking mistakes, personalizing guidance, reviewing code, running mock interviews, and measuring progress over time.

## Current Reality

AlgoFlow currently runs as a local prototype with:

- FastAPI backend.
- Next.js frontend.
- Pydantic request/response schemas.
- SQLite persistence for users, attempts, mistakes, and interviews.
- ChromaDB-backed vector memory writes with local fallback behavior.
- Deterministic tools for problem classification, code-review heuristics, study plans, recommendations, and analytics.
- Google ADK agent definitions in the repository.

Important limitation:

- The live FastAPI request path currently calls `MentorService` and deterministic tools directly.
- Google ADK agents are defined but are not yet invoked in the production request path.
- Several frontend dashboard/profile values are demo placeholders.
- Personalization is early and not yet evidence-based.

## Target Direction

The target architecture is a serious, evaluation-driven, secure, observable, cloud-deployable AI mentorship platform using:

- Google ADK and Gemini where agentic reasoning is justified.
- Skills and workflows for reusable procedural tutoring behavior.
- Tool gateway and policy enforcement.
- Long-term learner modeling from immutable learning evidence.
- RAG with explicit memory semantics and retrieval provenance.
- Secure code intelligence and sandboxed execution architecture.
- Evaluation suites for routing, hint leakage, code review, memory retrieval, personalization, and interview quality.
- Google Cloud deployment with Cloud Run, Cloud SQL PostgreSQL, Secret Manager, Artifact Registry, and Cloud observability.

See:

- [Current system audit](docs/audits/current-system-audit.md)
- [Target architecture](docs/architecture/system-overview.md)
- [Migration plan](docs/migration-plan.md)
- [Whitepaper traceability](docs/whitepaper-traceability.md)

## Repository Structure

```text
backend/        FastAPI app, schemas, services, tools, database models, ADK definitions
frontend/       Next.js app and UI pages
docs/           architecture, audits, ADRs, security, deployment notes
specs/          source-of-truth specifications for future major changes
evals/          planned evaluation suite structure
scripts/        local helper scripts
```

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp ../.env.example .env
uvicorn app.main:app --reload --reload-dir app
```

API root:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

## Environment Variables

```bash
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
ENABLE_LIVE_ADK=false
LIVE_ADK_TIMEOUT_SECONDS=3
LIVE_ADK_MAX_EVENTS=20
DATABASE_URL=sqlite+aiosqlite:///./algoflow.db
AUTO_CREATE_DB_SCHEMA=true
CHROMA_PATH=./.chroma
AUTH_MODE=hmac
AUTH_TOKEN_SECRET=
TRUSTED_HEADER_AUTH_ENABLED=false
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```

`ENABLE_LIVE_ADK=false` is the safe default. To opt into the narrow live ADK/Gemini coordinator route, set `ENABLE_LIVE_ADK=true` and provide `GOOGLE_API_KEY`. The ADK agent still receives no direct tools; post-routing tool execution remains policy-gated through the Tool Gateway.

Local mode can run without auth headers and resolves to `demo-user`. Production-like mode requires `DATABASE_URL=postgresql+asyncpg://...`, `AUTO_CREATE_DB_SCHEMA=false`, and either HMAC bearer auth with `AUTH_TOKEN_SECRET` or explicitly enabled trusted-header auth behind an authenticated gateway.

## Current API Highlights

- `GET /api/v1/health`
- `POST /api/v1/problems/analyze`
- `POST /api/v1/hints/next`
- `POST /api/v1/code-review`
- `POST /api/v1/study-plan`
- `POST /api/v1/recommendations`
- `POST /api/v1/pattern-transfer`
- `POST /api/v1/mock-interview/turn`
- `GET /api/v1/analytics/{user_id}`

See [docs/API.md](docs/API.md).

## Baseline Verification Notes

Current Phase 2 verification:

- `backend/.venv/bin/ruff check app tests`: passed.
- `backend/.venv/bin/pytest -q`: passed.
- `npm run build`: passed.

The API now emits `x-request-id` and `x-trace-id` headers and returns structured validation error envelopes.

## Development Discipline

Before major implementation:

1. Create or update a spec under `specs/`.
2. Define BDD scenarios.
3. Add deterministic tests and relevant eval cases.
4. Implement a bounded change.
5. Run tests/evals.
6. Update docs to match actual behavior.

Do not claim production readiness until behavior is implemented, tested, evaluated, observable, and deployable.
