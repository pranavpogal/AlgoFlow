# CI Integration Guide

Status: Current
Owner: AlgoFlow

AlgoFlow now has a minimal GitHub Actions workflow for deterministic validation. It does not deploy, use secrets, call Gemini, or invoke live ADK runtime.

## Provider

GitHub Actions.

Workflow:

```text
.github/workflows/ci.yml
```

## Jobs

- Backend tests, lint, and deterministic eval contract.
- Frontend production build.

## PR Contract

```bash
cd backend
pytest -q
ruff check app tests
python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --json
python -m app.evaluation.cli run --suite adk_routing
python -m app.evaluation.cli run --suite adk_live_runtime
python -m app.evaluation.cli run --suite adk_tool_orchestration
python -m app.evaluation.cli run --suite semantic_tool_policy

cd ../frontend
npm ci
npm run build
```

## Artifacts

The backend job uploads `evals/artifacts/` as `algoflow-evaluation-artifacts` with 14-day retention.

## Permissions

The workflow uses:

```yaml
permissions:
  contents: read
```

No baseline promotion occurs in CI. No secrets are required.

The ADK live runtime suite is explicit and blocking in CI, but uses bounded mock invokers
and no-key fallback cases; it does not call Gemini. The ADK tool orchestration suite is also
explicit and blocking; it checks allowed ADK-requested tool execution, denied misaligned tool
requests, tool-request trajectory coverage, and fallback non-bypass behavior. The semantic tool
policy suite guards structural precedence, solution-leakage boundaries, fallback non-bypass
behavior, and safe allow/deny balance. None of these explicit ADK/policy suites are part of the
accepted deterministic baseline comparison, so the four-suite baseline caseset does not change.

## Caching

- Python dependencies use `actions/setup-python` pip cache.
- Node dependencies use `actions/setup-node` npm cache.
- Eval results are not cached.

## Concurrency

The workflow cancels in-progress runs for the same workflow/ref. This avoids stale duplicate validation while not attempting distributed locking.

## Scheduled Evaluation

No scheduled workflow is added in this phase. Future scheduled runs may evaluate broader ADK/Gemini or model-judge suites once real traces, cost policy, and reproducibility rules exist.
