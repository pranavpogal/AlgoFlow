# Progressive Hinting Skill

Generates staged, non-spoiling hints for coding interview problems based on current problem context, learner intent, current reasoning, previous hints, derived learner state, and known misconceptions.

## Use When

- The learner asks for one hint.
- The learner asks for another hint.
- The learner asks whether an idea is correct.
- The learner asks why their state/approach is wrong.
- The learner asks for conceptual guidance without code.

## Do Not Use When

- The learner asks for final code review.
- The learner asks for a full code solution without hint mode.
- The learner is in a mock interview scoring turn.
- The task is study planning or analytics.

## Procedure

1. Identify user intent.
2. Classify the problem pattern.
3. Build bounded context from learner state and previous hint events.
4. Select one intervention type from the taxonomy.
5. Enforce leakage policy.
6. Avoid repeating previous hints.
7. Return structured internal result.
8. Record meaningful learning events.

## Leakage Policy

Do not reveal full recurrence, full algorithm, final code, or decisive missing trick unless explicit solution intent is present.

Repeated hint requests should escalate gradually, not automatically reveal the solution.
