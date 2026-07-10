# Code Intelligence Specification

Status: Draft
Owner: AlgoFlow
Phase: 1

Implementation note:

Phase 4B implemented a deterministic Code Review Skill/workflow with review-intent detection, typed findings, Python AST parsing, limited text adapters for selected non-Python languages, learning-event integration, and a deterministic evaluation dataset. Secure execution, counterexample generation, and Gemini/ADK semantic interpretation remain deferred.

## Purpose

Define a layered code review and analysis pipeline that uses deterministic evidence before LLM interpretation.

## Motivation

Current code review is string heuristics. A serious interview mentor should parse code, identify structural issues, reason about tests/edge cases, and eventually find counterexamples safely.

## Scope

- Language adapter architecture.
- Parser/AST/static analysis.
- Structured diagnostics.
- Secure execution interface.
- LLM semantic review as complement, not source of truth.

## Non-Goals

- Supporting every language immediately.
- Executing user code inside FastAPI.
- Claiming correctness without tests or evidence.

## Pipeline

```text
Code Submission
  -> Language Adapter
  -> Parser / AST
  -> Static Analysis
  -> Structured Diagnostics
  -> Optional Execution Service Request
  -> Counterexample Search
  -> LLM Semantic Review
  -> Structured Verdict
```

## Initial Language Strategy

Start with Python because the current demo examples are Python and Python AST tooling is available in the standard library. Other languages require adapters and tests before being advertised as strongly supported.

Current Phase 4B support:

- Python: AST parse plus selected structural diagnostics.
- Java, C++, JavaScript, TypeScript, Go: limited text-pattern diagnostics only.
- Other languages: unsupported-language response.

## Diagnostic Schema

```json
{
  "diagnostic_id": "diag_...",
  "category": "boundary_error",
  "severity": "medium",
  "evidence": "uses dp[i-1] when i can be 0",
  "line": 3,
  "confidence": 0.83,
  "suggested_next_step": "Define base cases before the loop."
}
```

## Security

- No arbitrary code execution in API process.
- Execution service is disabled until sandbox exists.
- Submitted code is sensitive and should not be logged by default.

## BDD Scenarios

### Scenario: Python DP Negative Index Risk

Given a Python House Robber submission uses `dp[i-1]` inside a loop starting at `i = 0`
When code intelligence analyzes it
Then it emits a boundary/base-case diagnostic
And cites the relevant line

### Scenario: Unsupported Language

Given a user submits Rust before Rust adapter exists
When code review runs
Then the system returns an unsupported-language or limited-review response
And does not pretend to provide full structural analysis

### Scenario: Execution Requested Before Sandbox

Given the user requests running tests
When no sandbox is configured
Then the system returns a safe disabled-execution response
And does not execute code

## Testing Strategy

- Parser unit tests.
- Diagnostic fixture tests.
- Unsupported-language tests.
- Security tests for no local execution.

## Evaluation Strategy

- Bug detection precision and recall.
- Diagnostic usefulness.
- Counterexample quality once execution exists.

## Acceptance Criteria

- Code review output distinguishes deterministic diagnostics from LLM commentary. Implemented by returning deterministic findings and no LLM commentary in Phase 4B.
- First language adapter has fixture coverage. Implemented for Python AST-backed checks.
- Production execution remains disabled until sandbox is implemented. Still enforced; no execution layer exists.
- Review intent influences rewrite behavior. Implemented for one-hint, do-not-rewrite, and corrected-code requests.
- Evaluation coverage exists for review quality and unsupported-claim control. Initial deterministic eval added in Phase 4B.
