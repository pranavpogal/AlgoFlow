# Phase 17 Tool Gateway Completion Report

PHASE:
Tool Gateway + Policy Integration Before Live ADK Tool Use

STATUS:
Complete

CURRENT TOOL ARCHITECTURE FOUND:
Tools were plain Python functions called directly by services and listed on old decorative ADK agents. No centralized gateway existed.

ARCHITECTURE DECISION:
Add a local structural tool gateway for low-risk read/draft tools only. Do not expose code execution, memory mutation, external tools, broad agent tools, or live Gemini tool use.

GATEWAY IMPLEMENTED:
`backend/app/core/tool_gateway.py`

REGISTERED TOOLS:

- `problem.detect_pattern`: read, low risk
- `problem.related_problems`: draft, low risk

POLICY MODEL:

- caller allowlist required
- read/draft allowed for registered callers
- act tools denied by default
- invalid input rejected through Pydantic validation
- output type checked

TRAJECTORY INTEGRATION:
Added trajectory events:

- `TOOL_CALL_COMPLETED`
- `TOOL_CALL_DENIED`

RUNTIME PATH UPDATED:
`/mentor/route` now calls `problem.detect_pattern` through `ToolGateway` and records the tool event before returning/storing trajectory.

FILES CREATED:

- `backend/app/core/tool_gateway.py`
- `backend/tests/test_tool_gateway.py`
- `docs/audits/tool-gateway-runtime-audit.md`
- `docs/evaluation/tool-gateway-evaluation.md`
- `docs/reports/phase-17-tool-gateway-completion-report.md`

FILES MODIFIED:

- `backend/app/runtime/trajectory.py`
- `backend/app/services/mentor_service.py`
- `backend/app/evaluation/adk_routing_eval.py`
- `backend/tests/test_adk_runtime_trajectory.py`
- `evals/adk_routing/cases.jsonl`

EVALUATION RESULT:
`adk_routing`: 3 cases, 3 passed, all gates passed.

BASELINE COMPARISON:
Accepted deterministic baseline preserved. No `--suite all` caseset change.

TESTS RUN:

- `pytest -q tests/test_tool_gateway.py tests/test_adk_runtime_trajectory.py`
- `pytest -q tests/test_evaluation_platform.py tests/test_tool_gateway.py tests/test_adk_runtime_trajectory.py`
- `pytest -q`
- `ruff check app tests`
- `python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --machine`
- `python -m app.evaluation.cli run --suite adk_routing`
- `npm run build`

EXACT RESULTS:

- Focused gateway/runtime tests: 8 passed, 4 ADK deprecation warnings.
- Focused gateway/runtime/eval tests: 15 passed, 4 ADK deprecation warnings.
- Full backend tests: 66 passed, 5 warnings.
- Ruff: all checks passed.
- Accepted baseline comparison: `0 pass 0 0 0`.
- ADK routing eval: 3/3 passed, all gates passing.
- Frontend build: compiled successfully, 12 static pages generated.

KNOWN LIMITATIONS:

- Direct legacy service paths still call raw tools to preserve baseline behavior.
- Gateway is synchronous and in-process.
- No policy-decision DB table yet.
- No tool timeout/cancellation enforcement yet.
- No live ADK tool invocation yet.

NEXT RECOMMENDED PHASE:
Migrate additional low-risk direct tool calls through the gateway or add policy-decision persistence before live ADK tool use.
