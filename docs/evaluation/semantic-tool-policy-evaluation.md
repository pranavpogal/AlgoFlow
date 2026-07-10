# Semantic Tool Policy Evaluation

Status: Current
Owner: AlgoFlow

## Suite

`semantic_tool_policy`

Cases live in:

```text
evals/semantic_tool_policy/cases.jsonl
```

## Dataset Size

18 cases:

- development: 8
- held_out: 4
- adversarial: 6

## Coverage

The suite covers:

- safe aligned pattern detection
- safe related-problem recommendation
- intent drift
- capability drift
- mentoring-mode enforcement
- explicit reveal authorization
- solution-leakage pressure
- obvious prompt-injection suspicion
- tool argument semantic mismatch
- structural precedence
- persistence metadata shape
- trajectory policy event coverage

## Metrics

- `semantic_policy_accuracy`
- `safe_allow_accuracy`
- `unsafe_deny_accuracy`
- `intent_alignment_accuracy`
- `capability_alignment_accuracy`
- `mentoring_mode_enforcement_accuracy`
- `solution_leakage_policy_accuracy`
- `injection_suspicion_recall`
- `false_positive_deny_rate`
- `structural_precedence_accuracy`
- `persistence_completeness`
- `trajectory_policy_event_coverage`
- `fallback_non_bypass_accuracy`
- `structured_output_validity`

## CI Relationship

The suite is explicit and blocking in CI because it guards live-tool-readiness invariants. It is not part of `--suite all` and does not alter the accepted four-suite deterministic baseline.

## Latest Verified Result

Full suite:

```text
18/18 passed, gates PASS
semantic_policy_accuracy=1.0
safe_allow_accuracy=1.0
unsafe_deny_accuracy=1.0
false_positive_deny_rate=0.0
```

Splits:

- development: 8/8 passed
- held_out: 4/4 passed
- adversarial: 6/6 passed

## Limitations

This is deterministic fixture coverage. It does not prove complete semantic understanding, complete prompt-injection coverage, or production robustness for arbitrary future tools.
