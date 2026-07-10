# ADK Live Runtime Evaluation

Status: Current
Owner: AlgoFlow

## Suite

`adk_live_runtime`

Cases live in:

```text
evals/adk_live_runtime/cases.jsonl
```

## Dataset Size

4 cases:

- mock live valid route
- mock live invalid output fallback
- live enabled without key fallback
- deterministic disabled parity

## Metrics

- `live_boundary_accuracy`
- `live_fallback_accuracy`
- `trajectory_event_coverage`
- `deterministic_parity_accuracy`

## CI Relationship

This suite is explicit and CI-blocking. It does not call Gemini. It validates the live runtime boundary with bounded mock invokers and fallback cases. It is not part of the accepted deterministic baseline comparison.

## Latest Verified Result

```text
adk_live_runtime: 4/4 passed, gates PASS
live_boundary_accuracy=1.0
live_fallback_accuracy=1.0
trajectory_event_coverage=1.0
deterministic_parity_accuracy=1.0
```

## Limitations

This suite verifies the runtime boundary and fallback contract, not model quality, token/cost behavior, or real network reliability.
