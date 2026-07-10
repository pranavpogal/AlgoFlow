# Frontend Product Polish Runtime Audit

Phase: 30 - Frontend Product Polish
Status: Pre-implementation audit

## Current Frontend Runtime

The Next.js frontend currently talks directly to FastAPI endpoints through `frontend/src/lib/api.ts`:

- `/analytics/demo-user`
- `/problems/analyze`
- `/hints/next`
- `/code-review`
- `/mock-interview/turn`
- `/study-plan`

The backend remains the source of truth for learner state, policy, trajectory, and deterministic workflows.

## Current UX Gaps

- API errors are shown inconsistently and usually as raw exception text.
- Several pages show raw JSON only, which is useful for debugging but weak for recruiter demos.
- The dashboard and analytics pages now use evidence-backed data, but still need stronger visual hierarchy.
- The mock interview page exposes rubric scores but not enough conversation polish or loading state.
- The profile page still shows static sample tags instead of real learner-model evidence.
- There is no frontend surface that demonstrates the governed route trajectory/policy story.
- The homepage still overstates the current runtime as ten live specialist agents rather than bounded governed workflows and justified ADK slices.

## Phase 30 Scope

This phase should:

- Add reusable frontend UI primitives for API state, evidence cards, score bars, and JSON disclosure.
- Improve loading/error states across core pages.
- Make dashboard, analytics, mock interview, and profile feel coherent and demo-ready.
- Add a bounded trajectory/policy visibility surface using `/mentor/route`, returned trajectory data, and policy-decision lookup when available.
- Keep frontend copy honest about current deterministic workflows and governed ADK routing.

## Explicit Non-Goals

- No backend runtime expansion.
- No live Gemini behavior changes.
- No new auth provider.
- No deployment/Docker work.
- No new analytics model calibration.
- No broad design-system rewrite beyond practical product polish.
