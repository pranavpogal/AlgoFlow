# ADR 0006: Code Intelligence and Secure Execution

Status: Proposed

## Context

Current code review uses string heuristics and does not execute submitted code. Future correctness/counterexample features require execution but submitted code is hostile.

## Decision

Implement code intelligence in layers:

1. Language adapter and parser/AST/static checks.
2. Deterministic diagnostics and complexity evidence.
3. Execution service interface returning safe stub in production until sandbox exists.
4. Isolated worker/sandbox with CPU/memory/time/network/filesystem limits.
5. Counterexample engine and LLM semantic review.

## Alternatives

- Execute code with `subprocess.run` in FastAPI: rejected categorically.
- Use LLM-only review: rejected because deterministic evidence is needed.

## Consequences

- Initial support should focus on one language, likely Python, rather than pretending broad support.
- Multi-language support comes through adapters.

## Security Impact

Critical RCE boundary.

## Operational Impact

Real sandbox introduces worker infrastructure and resource limits.

## Evaluation Impact

Bug detection precision/recall and counterexample quality become measurable.
