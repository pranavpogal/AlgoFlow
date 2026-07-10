# Regression Case Policy

Status: Current
Owner: AlgoFlow

## Purpose

Regression cases protect fixed behavioral failures from returning. They are not a way to inflate suite count or claim artificial maturity.

## Valid Sources

A regression case should originate from at least one of:

- A real discovered bug.
- A failed evaluation case.
- A previously fixed behavioral failure.
- A known policy violation.
- A future sanitized production failure.

## Required Metadata Where Available

- Originating suite.
- Failure category.
- Date discovered.
- Expected behavior.
- Fix reference if available.
- Issue or PR reference if available.
- Whether the case contains sanitized user data.

Unavailable metadata should be recorded honestly as `null` or omitted. Do not fabricate issue IDs or production incidents.

## Workflow

```text
Behavioral Failure Found
        ↓
Root Cause Confirmed
        ↓
Fix Implemented
        ↓
Regression Case Added
        ↓
Case Tagged With Provenance
        ↓
Future CI Gate Protects It
```

## Current Status

No dedicated regression split exists yet. This is honest: current eval fixtures include development, heldout, and adversarial patterns, but there is not yet a curated regression corpus derived from historical failures.

## Future Split Name

Use `regression` for future cases. Do not duplicate existing cases into a regression folder merely to claim support.
