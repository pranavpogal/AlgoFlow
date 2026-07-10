# Mock Interview Runtime Audit

Status: Current-state audit before Phase 28 implementation
Owner: AlgoFlow
Date: 2026-07-10

## Current Runtime Path

```text
POST /api/v1/mock-interview/turn
  -> backend/app/api/routes.py::interview_turn
  -> MentorService.interview_turn
  -> keyword branch on message text
  -> InterviewTurnResponse
  -> InterviewAnswerSubmitted learning event
```

## Current Capabilities

- Accepts persona: Google, Meta, Amazon, Generic.
- Returns a `session_id` if one is not supplied.
- Returns a follow-up question, focus label, score delta, and feedback.
- Retrieves memory context for advisory personalization.
- Records `InterviewAnswerSubmitted` learning events.

## Current Gaps

- No durable transcript update despite `InterviewSession` table existing.
- No explicit interview state machine.
- Persona differences are shallow.
- Score is a single turn delta, not a rubric-backed scorecard.
- Follow-up selection is keyword-driven only.
- No session summary, turn index, rubric evidence, or conversation stage is exposed.
- No interview-specific eval suite exists.

## Proposed Narrow Slice

Add a deterministic mock-interview workflow that:

- creates or loads an `InterviewSession`
- appends user and interviewer turns to transcript
- tracks phase/stage across turns
- applies persona-specific interviewer style
- scores communication, correctness, complexity, testing, and adaptability
- returns rubric evidence and aggregate scorecard
- records score/transcript evidence in learning events

## Non-Goals

- No live Gemini interviewer.
- No broad ADK sub-agent expansion.
- No speech/audio or code execution.
- No frontend redesign in this phase.
- No claims that scoring is equivalent to a real onsite interview.

## Expected Tests

- first turn creates durable interview session
- second turn reuses session and appends transcript
- persona changes interviewer style/focus
- scorecard includes rubric categories and evidence
- cross-user session access is not allowed

## Known Limitations

- Rubric scoring is deterministic and heuristic.
- Session memory is stored in JSON columns; production migration files remain future work.
- The frontend currently displays only the interviewer message.
