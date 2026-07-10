# Phase 19 Semantic Tool Policy Completion Report

PHASE:
Semantic Tool Policy + Intent Boundary Enforcement

STATUS:
Complete

CURRENT POLICY ARCHITECTURE FOUND:
Structural tool policy existed in `ToolGateway`; semantic mentoring policy existed inside Skills but not before tool execution.

CURRENT TOOL GATEWAY FOUND:
`ToolGateway` registers `problem.detect_pattern` and `problem.related_problems`, validates inputs/outputs, enforces caller allowlists, denies act tools by default, emits trajectory events, and now evaluates deterministic semantic policy before execution.

CURRENT PERSISTENCE FOUND:
`policy_decisions` persisted structural/final tool records. Phase 19 now stores structural and semantic decision payloads in `decision_metadata` without changing the table schema.

SEMANTIC GAPS FOUND:
Intent-tool alignment, capability-tool alignment, mentoring-mode enforcement, prompt-injection suspicion, explicit reveal authorization, and argument semantic matching were not enforced at the gateway.

ARCHITECTURE DECISION:
Semantic policy is a deterministic service composed into `ToolGateway`, not an agent or LLM judge. Structural deny always precedes and dominates semantic policy.

FILES CREATED:

- `backend/app/core/semantic_policy.py`
- `backend/app/evaluation/semantic_tool_policy_eval.py`
- `backend/app/evaluation/adapters/semantic_tool_policy.py`
- `backend/tests/test_semantic_tool_policy.py`
- `evals/semantic_tool_policy/cases.jsonl`
- `docs/audits/semantic-tool-policy-runtime-audit.md`
- `specs/policy/semantic-tool-policy.md`
- `docs/security/tool-policy-matrix.md`
- `docs/security/prompt-injection-boundary.md`
- `docs/evaluation/semantic-tool-policy-evaluation.md`
- `docs/reports/phase-19-semantic-tool-policy-completion-report.md`

FILES MODIFIED:

- `backend/app/core/tool_gateway.py`
- `backend/app/runtime/trajectory.py`
- `backend/app/services/mentor_service.py`
- `backend/app/memory/repository.py`
- `backend/app/evaluation/adk_routing_eval.py`
- `backend/app/evaluation/core/registry.py`
- `backend/app/evaluation/core/thresholds.py`
- `backend/app/evaluation/core/metrics.py`
- `backend/tests/test_tool_gateway.py`
- `.github/workflows/ci.yml`
- `docs/API.md`
- `docs/evaluation/ci-integration.md`
- `specs/security/policy-gateway.md`

SEMANTIC POLICY CONTEXT:
`SemanticPolicyContext` carries principal, request, trace, session, trajectory, caller, selected capability, user intent, mentoring mode, tool ID, operation type, tool arguments, task context, prior hint context, trusted context, untrusted-content marker, and reveal authorization.

TRUST BOUNDARIES:
Trusted runtime metadata is separated from untrusted user/problem text. Untrusted content cannot redefine caller identity, principal identity, tool permissions, operation type, mentoring mode, or reveal authorization.

DECISION MODEL:
`allow` and `deny`. `ALLOW_WITH_CONSTRAINTS` is deferred because no reliable constraint executor exists yet.

REASON TAXONOMY:
Includes intent mismatch, capability mismatch, mentoring-mode violation, solution-leakage risk, explicit reveal not authorized, prompt-injection suspected, instruction override, argument mismatch, unsupported task, capability drift, untrusted override, insufficient context, invalid context, and allow reasons such as bounded analysis allowed and explicit reveal authorized.

INTENT ALIGNMENT:
Intent-to-tool mappings now allow pattern detection for problem analysis/hints/validation and related-problem calls only for recommendation/transfer intent.

CAPABILITY ALIGNMENT:
Capability-to-tool mappings now restrict `problem.detect_pattern` to `problem_analysis` and `next_hint`, and `problem.related_problems` to recommendation/transfer capabilities.

MENTORING MODE ENFORCEMENT:
Gateway policy recognizes implemented runtime modes: `HINT_ONLY`, `VALIDATE_APPROACH`, `EXPLAIN_CONCEPT`, `RECOMMEND_TRANSFER`, `EXPLICIT_SOLUTION`, and `CODE_REVIEW` as a reserved taxonomy value.

SOLUTION LEAKAGE POLICY:
Hint-only mode cannot silently drift into recommendation tooling. Full-solution intent is denied unless explicit reveal authorization is present.

EXPLICIT REVEAL POLICY:
Reveal authorization is derived from existing progressive hint intent logic plus the `reveal_solution` flag. It is not inferred from model/tool arguments.

PROMPT INJECTION SUSPICION:
Bounded deterministic checks detect obvious policy/tool override pressure such as bypass policy, pretend admin, call every tool, override system policy, or change caller identity. This is suspicion only, not complete injection detection.

TOOL ARGUMENT SEMANTICS:
`problem.detect_pattern` requires problem context and matching task/tool title. `problem.related_problems` requires a pattern and recommendation-compatible context.

POLICY COMPOSITION ORDER:
Tool existence, structural policy, input schema validation, semantic context validation, injection suspicion, capability alignment, intent alignment, mentoring mode, reveal/leakage boundary, argument semantics, execution, output validation, trajectory/persistence.

POLICY PRECEDENCE:
Structural deny > semantic allow. Act deny default > model request. Trusted runtime metadata > untrusted text. Semantic deny > raw fallback in governed runtime.

POLICY VERSION:
`semantic-tool-policy-v1`

PERSISTED POLICY FIELDS:
Existing columns remain. `decision_metadata` now stores `structural_decision`, `semantic_decision`, `final_decision`, semantic policy version, reason code, selected capability, user intent, mentoring mode, reveal authorization, and injection suspicion.

TRAJECTORY EVENTS:
Added `STRUCTURAL_POLICY_EVALUATED` and `SEMANTIC_POLICY_EVALUATED`. Existing `TOOL_CALL_COMPLETED` and `TOOL_CALL_DENIED` remain compatible with `trajectory-v1`.

REGISTERED TOOL POLICY MATRIX:
Documented in `docs/security/tool-policy-matrix.md` for `problem.detect_pattern` and `problem.related_problems`.

DIRECT LEGACY PATH FINDINGS:
`/problems/analyze`, `/hints/next`, `/recommendations`, and `/pattern-transfer` retain direct deterministic paths. They are documented as compatibility paths/future migration candidates. The governed `/mentor/route` path does not bypass semantic deny by calling raw tools.

FALLBACK NON-BYPASS BEHAVIOR:
If `/mentor/route` semantic policy denies `problem.detect_pattern`, the service returns a safe non-tool fallback instead of calling `detect_problem_pattern` directly.

SEMANTIC POLICY EVAL DATASET SIZE:
18 cases total: 8 development, 4 held-out, 6 adversarial.

DEVELOPMENT RESULTS:
8/8 passed, gates PASS.

HELD-OUT RESULTS:
4/4 passed, gates PASS.

ADVERSARIAL RESULTS:
6/6 passed, gates PASS.

SAFE ALLOW ACCURACY:
1.0

UNSAFE DENY ACCURACY:
1.0

FALSE POSITIVE DENY RATE:
0.0

INTENT ALIGNMENT ACCURACY:
1.0

CAPABILITY ALIGNMENT ACCURACY:
1.0

MENTORING MODE ENFORCEMENT ACCURACY:
1.0

SOLUTION LEAKAGE POLICY ACCURACY:
1.0

INJECTION SUSPICION RESULTS:
`injection_suspicion_recall=1.0` on labeled adversarial fixtures.

STRUCTURAL PRECEDENCE ACCURACY:
1.0

PERSISTENCE COMPLETENESS:
1.0

TRAJECTORY POLICY EVENT COVERAGE:
1.0

FALLBACK NON-BYPASS ACCURACY:
1.0

BASELINE COMPARISON:
Accepted baseline comparison returned `0 pass 0 0 0 eval_20260706T102449Z_be11392e`.

CASESET DRIFT:
No accepted-baseline caseset drift. `--suite all` remains the four-suite, 66-case deterministic baseline. `semantic_tool_policy` is explicit and CI-blocking but not part of accepted baseline comparison.

TESTS RUN:

- `cd backend && .venv/bin/pytest -q tests/test_semantic_tool_policy.py tests/test_tool_gateway.py tests/test_adk_runtime_trajectory.py`
- `cd backend && .venv/bin/pytest -q tests/test_evaluation_platform.py tests/test_semantic_tool_policy.py tests/test_tool_gateway.py tests/test_adk_runtime_trajectory.py`
- `cd backend && .venv/bin/pytest -q`
- `cd backend && .venv/bin/ruff check app tests`
- `cd backend && .venv/bin/python -m app.evaluation.cli run --suite semantic_tool_policy`
- `cd backend && .venv/bin/python -m app.evaluation.cli run --suite semantic_tool_policy --split development`
- `cd backend && .venv/bin/python -m app.evaluation.cli run --suite semantic_tool_policy --split held_out`
- `cd backend && .venv/bin/python -m app.evaluation.cli run --suite semantic_tool_policy --split adversarial`
- `cd backend && .venv/bin/python -m app.evaluation.cli run --suite all`
- `cd backend && .venv/bin/python -m app.evaluation.cli run --suite adk_routing`
- `cd backend && .venv/bin/python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --machine`
- `cd frontend && /Users/pranavpogal/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/next/dist/bin/next build`

EXACT TEST RESULTS:

- Focused semantic/gateway/runtime tests: `21 passed, 4 warnings`
- Focused evaluation/runtime regression tests: `28 passed, 4 warnings`
- Full backend tests: `79 passed, 5 warnings`
- Semantic policy eval: `18/18 passed`, gates `PASS`
- Development split: `8/8 passed`, gates `PASS`
- Held-out split: `4/4 passed`, gates `PASS`
- Adversarial split: `6/6 passed`, gates `PASS`
- `--suite all`: `66/66 passed`, gates `PASS`
- ADK routing eval: `3/3 passed`, gates `PASS`

BACKEND LINT:
`All checks passed!`

FRONTEND BUILD:
Next.js production build compiled successfully and generated 12 static pages.

SECURITY FINDINGS:
Structural policy was strong for caller/operation checks but did not know whether a tool call was justified. Semantic policy now covers the governed route, but direct legacy paths remain future migration candidates.

MITIGATED RISKS:

- capability drift in governed gateway calls
- intent/tool mismatch in governed gateway calls
- unauthorized reveal escalation in governed gateway calls
- obvious policy/tool override prompt pressure
- structural deny being overridden by semantic allow
- semantic deny bypass through `/mentor/route` raw fallback
- cross-user policy-decision reads

PARTIALLY MITIGATED RISKS:

- indirect prompt injection in problem statements
- future model-generated tool argument drift
- tool confusion for currently registered tools only
- semantic persistence via metadata rather than dedicated columns

DEFERRED RISKS:

- broad direct legacy path migration
- semantic policy for memory/code execution/external tools
- admin policy review/search UI
- migration framework for database schema evolution
- async timeout/cancellation enforcement

KNOWN LIMITATIONS:

- No live Gemini or live ADK tool use enabled.
- No LLM-based policy judge.
- Prompt-injection suspicion is pattern-based and incomplete.
- `ALLOW_WITH_CONSTRAINTS` is deferred.
- Current policy maps only two registered tools.
- CI workflow syntax was inspected, not validated with a remote GitHub runner.

EVAL LEAKAGE RISKS:
The held-out split is fixture-held-out, not a repeatedly untouched external dataset. Adversarial cases are deterministic examples and should not be treated as comprehensive red-team coverage.

UNRESOLVED DECISIONS:
Whether to migrate `/hints/next`, `/problems/analyze`, and `/recommendations` direct paths through the gateway next, or first add live ADK invocation behind this policy boundary.

NEXT RECOMMENDED PHASE:
Narrow live ADK runtime invocation behind the policy gateway for one routing/tool slice, with deterministic fallback, timeout policy, and trajectory/policy comparison against the accepted deterministic baseline.
