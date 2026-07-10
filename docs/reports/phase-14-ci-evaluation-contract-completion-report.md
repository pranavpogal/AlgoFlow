# Phase 14 CI Evaluation Contract Completion Report

PHASE:
CI Evaluation Contract + Accepted Baseline Snapshot Policy

STATUS:
Complete

CURRENT CI ARCHITECTURE FOUND:
No CI workflow existed before this phase. The repo had Dockerfiles, `docker-compose.yml`, `scripts/dev.sh`, backend pytest/ruff configuration, frontend build scripts, and the unified evaluation CLI.

CURRENT EVAL CONTRACT FOUND:
The unified evaluation platform existed with typed protocols, adapters, metric registry, gate policy, split filtering, human-readable reports, JSON artifacts, typed failure categories, and exit-code semantics.

CI FRAGMENTATION FOUND:
There were local commands and docs, but no CI provider, no workflow triggers, no artifact retention, no accepted baseline snapshot, no baseline comparison, and no explicit baseline promotion policy.

ARCHITECTURE DECISION:
Use a minimal GitHub Actions workflow plus a checked-in accepted baseline snapshot. Add explicit baseline comparison and candidate generation to the existing evaluation CLI. Do not add cloud deployment, live Gemini, ADK runtime, or model judges.

FILES CREATED:
- `.github/workflows/ci.yml`
- `backend/app/evaluation/core/baseline.py`
- `backend/tests/test_ci_evaluation_contract.py`
- `docs/audits/ci-evaluation-contract-runtime-audit.md`
- `docs/evaluation/accepted-baseline-policy.md`
- `docs/evaluation/regression-case-policy.md`
- `docs/evaluation/local-ci-contract.md`
- `docs/reports/phase-14-ci-evaluation-contract-completion-report.md`
- `evals/baselines/accepted/current.json`
- `specs/evaluation/ci-evaluation-contract.md`

FILES MODIFIED:
- `backend/app/evaluation/cli.py`
- `docs/evaluation/ci-integration.md`
- `evals/README.md`

CI PROVIDER:
GitHub Actions.

CI WORKFLOWS ADDED / MODIFIED:
Added `.github/workflows/ci.yml` with backend tests/lint/eval comparison and frontend build jobs.

PR GATE CONTRACT:
- Backend: `pytest -q`
- Backend lint: `ruff check app tests`
- Deterministic eval comparison: `python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --json`
- Frontend: `npm ci` and `npm run build`

SCHEDULED / MANUAL CONTRACT:
Manual `workflow_dispatch` is enabled. No scheduled workflow was added in this phase because broader ADK/Gemini/model-judge suites do not exist yet.

ACCEPTED BASELINE MODEL:
Implemented as `accepted-baseline-v1` JSON with baseline ID, contract version, creation timestamp, source revision, suite results, case IDs, split counts, metrics, metric definition versions/fingerprints, taxonomy versions, and notes.

BASELINE STORAGE:
Checked-in repository snapshot at `evals/baselines/accepted/current.json`.

BASELINE ID:
`accepted-2026-07-06-deterministic-v1`

BASELINE PROMOTION POLICY:
Normal eval/compare runs never mutate the accepted baseline. Candidate generation is explicit via `python -m app.evaluation.cli baseline candidate --output ... --notes ...`. Promotion requires a reviewed repository change to `evals/baselines/accepted/current.json`.

BASELINE MUTATION PROTECTION:
CI uses read-only repository permissions and does not run any baseline promotion command. Candidate generation requires an explicit output path.

METRIC VERSION SAFETY:
Implemented metric definition versions and metric definition fingerprints. Incompatible metric versions/fingerprints produce `not_comparable` instead of silent comparison.

CASESET DRIFT DETECTION:
Implemented case-count, case-ID, and split-count comparison per suite.

ABSOLUTE GATES:
Existing absolute gates remain in `backend/app/evaluation/core/thresholds.py`.

RELATIVE REGRESSION GATES:
Implemented in `RELATIVE_REGRESSION_POLICIES` in `backend/app/evaluation/core/baseline.py`.

BLOCKING METRICS:
Blocking relative policies include suite pass rates, hint intervention correctness, solution leakage, unsupported-claim rates, rewrite-policy compliance, pattern-transfer same-topic shortcut rate, and pattern-transfer provenance completeness.

WARNING METRICS:
Warning policies include code-review workflow precision, problem-intelligence topic/pattern quality, pattern-transfer recommendation relevance, and transfer type accuracy.

INFORMATIONAL METRICS:
Metrics not included in blocking/warning policies remain measured and available in artifacts, including small-data and secondary-label signals.

REGRESSION SPLIT STATUS:
No dedicated regression split exists yet. A real regression-case policy was documented; no fake regression corpus was created.

FAILURE-TO-REGRESSION WORKFLOW:
Documented in `docs/evaluation/regression-case-policy.md`: behavioral failure, root cause, fix, regression case, provenance tag, future CI gate.

ARTIFACT POLICY:
`--json` writes `summary.json`, `cases.json`, `failures.json`, and `baseline_comparison.json` under `evals/artifacts/<run_id>/`. CI uploads `evals/artifacts/` for 14 days.

HUMAN-READABLE SUMMARY:
Implemented via `human_comparison_summary`, showing baseline ID, current run ID, status, exit, improved/regressed/unchanged/not-comparable counts, caseset drift, blocking regressions, and warnings.

MACHINE-READABLE COMPARISON:
Implemented as `BaselineComparison.to_dict()` with baseline ID, run ID, status, metric deltas, caseset drift, blocking regressions, warnings, not-comparable entries, infrastructure flag, and exit code.

EXIT CODE CONTRACT:
- `0`: success, no blocking regression.
- `1`: behavioral failure or blocking baseline regression.
- `2`: infrastructure failure, invalid baseline, invalid suite, or case-loading failure.

LOCAL COMMANDS:
```bash
cd backend
.venv/bin/pytest -q
.venv/bin/ruff check app tests
.venv/bin/python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json
.venv/bin/python -m app.evaluation.cli baseline candidate --output ../evals/baselines/candidates/<candidate>.json --notes "Reason"
cd ../frontend
npm run build
```

CI COMMANDS:
```bash
cd backend
pytest -q
ruff check app tests
python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --json
cd ../frontend
npm ci
npm run build
```

CURRENT BASELINE METRICS:
- Hinting: 5 cases, pass rate 1.0, intervention type accuracy 1.0, solution leakage rate 0.0.
- Code review: 16 cases, pass rate 1.0, workflow precision 0.692, legacy precision 0.625, unsupported claim rate 0.0.
- Problem intelligence: 30 cases, pass rate 1.0, primary topic accuracy 1.0, pattern precision 1.0, pattern recall 1.0.
- Pattern transfer: 15 cases, pass rate 1.0, recommendation relevance 1.0, same-topic shortcut rate 0.0, provenance completeness 1.0.

BASELINE COMPARISON RESULT:
Machine-readable comparison returned `0 pass 0 0 0`: exit code 0, status pass, 0 blocking regressions, 0 warnings, 0 not-comparable entries.

INTENTIONAL REGRESSION TEST RESULT:
Controlled fake current metric set `hinting.pass_rate=0.8`; comparison returned exit code 1 with blocking regression `hinting.pass_rate`.

INFRASTRUCTURE FAILURE TEST RESULT:
Invalid baseline `{}` returned exit code 2 and reported missing required baseline fields.

PARITY RESULTS:
Unified eval comparison preserved current semantics: 4 suites, 66 cases, 66 passed, no blocking gates failed, no caseset drift.

TESTS RUN:
- `cd backend && .venv/bin/pytest -q tests/test_ci_evaluation_contract.py`
- `cd backend && .venv/bin/pytest -q`
- `cd backend && .venv/bin/ruff check app tests`
- `cd backend && .venv/bin/python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --json`
- `cd backend && .venv/bin/python -m app.evaluation.cli run --suite pattern_transfer --split adversarial`
- `cd frontend && npm run build`
- `ruby -e "require 'yaml'; YAML.load_file('.github/workflows/ci.yml'); puts 'workflow_yaml_parse_ok'"`

EXACT TEST RESULTS:
- New CI-contract tests: 12 passed.
- Full backend tests: 57 passed, 1 warning.
- Workflow YAML parse: `workflow_yaml_parse_ok`.

BACKEND LINT:
`ruff check app tests`: all checks passed.

FRONTEND BUILD:
`npm run build`: compiled successfully, lint/type checks passed, 12 static pages generated.

UNIFIED EVAL RESULT:
Accepted-baseline comparison run: 4 suites, 66 cases, 66 passed, status pass, exit code 0.

KNOWN LIMITATIONS:
No historical trend store, no dedicated regression split, no live Gemini eval, no real ADK trajectory eval, no model-assisted judge, no cloud deployment, and no committed Git revision available for baseline provenance yet.

SECURITY FINDINGS:
CI uses read-only contents permission and no secrets. Baseline promotion cannot happen from normal CI. Artifact retention is limited to 14 days. This does not claim perfect supply-chain security because third-party GitHub Actions are still used by version tag.

EVAL LEAKAGE RISKS:
Current suites remain small and curated. Heldout/adversarial fixtures have been repeatedly used locally, so they should not be treated as statistically clean holdouts.

UNRESOLVED DECISIONS:
- When to add a real regression split.
- Whether future baseline promotion should use a manual workflow or reviewed commits only.
- How future ADK/Gemini comparison artifacts should be retained.
- When to add scheduled broader evals.

NEXT RECOMMENDED PHASE:
ADK routing/orchestration evaluation readiness, or real regression corpus creation from future discovered failures.
