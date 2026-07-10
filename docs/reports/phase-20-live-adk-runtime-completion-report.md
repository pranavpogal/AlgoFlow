# Phase 20 Live ADK Runtime Completion Report

PHASE:
Narrow Live ADK/Gemini Runtime

STATUS:
Complete

OBJECTIVE:
Enable one bounded live ADK coordinator invocation path behind existing policy/evaluation constraints while preserving deterministic fallback and avoiding broad agent/tool expansion.

ARCHITECTURE CHANGE:
`AdkCoordinatorRuntime` now installs a default `LiveAdkDecisionInvoker` when `ENABLE_LIVE_ADK=true` and `GOOGLE_API_KEY` is configured. The invoker uses ADK `Runner` and validates output through `CoordinatorDecision`.

LIVE RUNTIME PATH:

```text
/mentor/route
  -> AdkCoordinatorRuntime
  -> LiveAdkDecisionInvoker when enabled/configured
  -> CoordinatorDecision validation
  -> ToolGateway + semantic policy
  -> deterministic Skill workflow
  -> trajectory and policy persistence
```

FILES CREATED:

- `backend/app/evaluation/adk_live_runtime_eval.py`
- `backend/app/evaluation/adapters/adk_live_runtime.py`
- `evals/adk_live_runtime/cases.jsonl`
- `docs/audits/live-adk-runtime-runtime-audit.md`
- `docs/evaluation/adk-live-runtime-evaluation.md`
- `docs/reports/phase-20-live-adk-runtime-completion-report.md`

FILES MODIFIED:

- `backend/app/runtime/adk_runtime.py`
- `backend/app/runtime/trajectory.py`
- `backend/app/core/config.py`
- `backend/app/evaluation/core/registry.py`
- `backend/app/evaluation/core/thresholds.py`
- `backend/app/evaluation/core/metrics.py`
- `backend/tests/test_adk_runtime_trajectory.py`
- `.github/workflows/ci.yml`
- `README.md`
- `specs/architecture/adk-runtime.md`
- `docs/evaluation/ci-integration.md`

LIVE ADK/GEMINI BEHAVIOR:
Live ADK routing is opt-in. Real Gemini-backed invocation only runs when `ENABLE_LIVE_ADK=true` and `GOOGLE_API_KEY` is configured. CI does not call Gemini.

POLICY BOUNDARY:
The ADK agent still receives no tools. Tool execution remains post-routing through `ToolGateway`, structural policy, semantic policy, and persistent policy-decision records.

FALLBACKS:
Fallback remains deterministic for disabled config, missing key, dependency failure, timeout, invalid schema, and invocation exceptions.

TRAJECTORY EVENTS:
Added `ADK_LIVE_EVENT_RECEIVED`. Existing invocation/fallback/route/tool/policy events remain compatible with `trajectory-v1`.

EVALUATION:
Added explicit `adk_live_runtime` suite with 4 cases and blocking gates. It is CI-blocking but not part of the accepted baseline comparison.

TESTS AND EVALUATION:

- Full backend tests: `81 passed, 5 warnings`
- Backend lint: `All checks passed!`
- Accepted deterministic eval: `66/66 passed`, gates `PASS`
- Accepted baseline comparison: `0 pass 0 0 0 eval_20260710T035011Z_c36aab63`
- ADK routing eval: `3/3 passed`, gates `PASS`
- ADK live runtime boundary eval: `4/4 passed`, gates `PASS`
- Semantic tool policy eval: `18/18 passed`, gates `PASS`
- Frontend build: Next.js production build compiled successfully, 12 static pages generated

KNOWN LIMITATIONS:

- No live ADK tool invocation.
- No broad agent/sub-agent connection.
- No CI Gemini calls.
- No token/cost metrics yet.
- No production persistent ADK session service yet.
