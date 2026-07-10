from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

InterviewPersona = Literal["Google", "Meta", "Amazon", "Generic"]


class InterviewStage(StrEnum):
    OPENING = "opening"
    APPROACH = "approach"
    COMPLEXITY = "complexity"
    TESTING = "testing"
    OPTIMIZATION = "optimization"
    WRAP_UP = "wrap_up"


RUBRIC_CATEGORIES = ["communication", "correctness", "complexity", "testing", "adaptability"]


@dataclass(frozen=True)
class InterviewContext:
    session_id: str
    persona: InterviewPersona
    problem_title: str | None
    message: str
    transcript: list[dict[str, Any]] = field(default_factory=list)
    scorecard: dict[str, Any] = field(default_factory=dict)
    memory_snippets: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class InterviewResult:
    session_id: str
    interviewer_message: str
    follow_up_focus: str
    score_delta: int
    feedback: list[str]
    stage: str
    turn_index: int
    rubric_scores: dict[str, int]
    scorecard: dict[str, Any]
    transcript_entries: list[dict[str, Any]]
    evaluation_summary: str
    persona_style: str


def conduct_interview_turn(context: InterviewContext) -> InterviewResult:
    message = context.message.strip()
    lower = message.lower()
    previous_turns = len([entry for entry in context.transcript if entry.get("role") == "user"])
    stage = _select_stage(lower, previous_turns)
    rubric_delta, evidence = _score_message(lower, stage)
    prior_scores = _prior_scores(context.scorecard)
    rubric_scores = {
        category: max(0, min(5, prior_scores[category] + rubric_delta.get(category, 0)))
        for category in RUBRIC_CATEGORIES
    }
    focus = _follow_up_focus(stage, rubric_delta, lower)
    interviewer_message = _render_interviewer_message(context.persona, stage, focus, context.memory_snippets)
    score_delta = sum(rubric_scores.values()) - sum(prior_scores.values())
    turn_index = previous_turns + 1
    transcript_entries = [
        {
            "turn_index": turn_index,
            "role": "user",
            "message": message,
            "stage": stage.value,
            "rubric_evidence": evidence,
        },
        {
            "turn_index": turn_index,
            "role": "interviewer",
            "message": interviewer_message,
            "stage": stage.value,
            "follow_up_focus": focus,
        },
    ]
    scorecard = {
        "rubric_scores": rubric_scores,
        "total_score": sum(rubric_scores.values()),
        "max_score": len(RUBRIC_CATEGORIES) * 5,
        "turn_count": turn_index,
        "last_stage": stage.value,
        "persona": context.persona,
        "evidence": [*list(context.scorecard.get("evidence", []))[-8:], evidence],
    }
    return InterviewResult(
        session_id=context.session_id,
        interviewer_message=interviewer_message,
        follow_up_focus=focus,
        score_delta=score_delta,
        feedback=_feedback(stage, rubric_delta, context.persona),
        stage=stage.value,
        turn_index=turn_index,
        rubric_scores=rubric_scores,
        scorecard=scorecard,
        transcript_entries=transcript_entries,
        evaluation_summary=_evaluation_summary(rubric_scores, stage),
        persona_style=_persona_style(context.persona),
    )


def _select_stage(message: str, previous_turns: int) -> InterviewStage:
    if previous_turns == 0:
        if _mentions_complexity(message):
            return InterviewStage.COMPLEXITY
        if _mentions_tests(message):
            return InterviewStage.TESTING
        return InterviewStage.APPROACH
    if _mentions_complexity(message):
        return InterviewStage.COMPLEXITY
    if _mentions_tests(message):
        return InterviewStage.TESTING
    if "optimiz" in message or "improve" in message or "space" in message:
        return InterviewStage.OPTIMIZATION
    if previous_turns >= 4:
        return InterviewStage.WRAP_UP
    return InterviewStage.APPROACH


def _score_message(message: str, stage: InterviewStage) -> tuple[dict[str, int], dict[str, Any]]:
    delta = {category: 0 for category in RUBRIC_CATEGORIES}
    signals: list[str] = []
    if len(message.split()) >= 12:
        delta["communication"] += 1
        signals.append("clear_explanation_length")
    if any(term in message for term in ["invariant", "state", "dp", "visited", "pointer", "window"]):
        delta["correctness"] += 1
        signals.append("algorithmic_invariant_or_state")
    if _mentions_complexity(message):
        delta["complexity"] += 1
        signals.append("complexity_discussed")
    if _mentions_tests(message):
        delta["testing"] += 1
        signals.append("tests_or_edges_discussed")
    if any(term in message for term in ["tradeoff", "optimize", "alternative", "if not", "constraint"]):
        delta["adaptability"] += 1
        signals.append("tradeoff_or_adaptation")
    if stage is InterviewStage.COMPLEXITY and not _mentions_complexity(message):
        signals.append("complexity_prompt_not_answered")
    if not signals:
        signals.append("needs_more_structure")
    return delta, {"stage": stage.value, "signals": signals, "message_length": len(message)}


def _follow_up_focus(stage: InterviewStage, rubric_delta: dict[str, int], message: str) -> str:
    if stage is InterviewStage.APPROACH and rubric_delta["correctness"] == 0:
        return "state the invariant or data structure choice"
    if stage is InterviewStage.COMPLEXITY and rubric_delta["complexity"] == 0:
        return "justify time and space complexity"
    if stage is InterviewStage.TESTING and rubric_delta["testing"] == 0:
        return "name edge cases and failure modes"
    if "optimiz" in message or stage is InterviewStage.OPTIMIZATION:
        return "tradeoffs and optimization"
    return "communication clarity under follow-up pressure"


def _render_interviewer_message(
    persona: InterviewPersona, stage: InterviewStage, focus: str, memory_snippets: list[str]
) -> str:
    style = _persona_style(persona)
    memory_clause = ""
    if memory_snippets:
        memory_clause = " I will also watch for a pattern from your recent practice: keep that in mind as you answer."
    if stage is InterviewStage.APPROACH:
        prompt = f"{style} Walk me through your approach, but make the invariant explicit. What exactly stays true after each step?"
    elif stage is InterviewStage.COMPLEXITY:
        prompt = f"{style} Now justify complexity. What is the tight time and space bound, and what input shape makes it worst-case?"
    elif stage is InterviewStage.TESTING:
        prompt = f"{style} Give me three tests: smallest input, a typical case, and one adversarial edge case. Why do those cover the risk?"
    elif stage is InterviewStage.OPTIMIZATION:
        prompt = f"{style} Can you improve either memory or runtime? If not, explain the limiting constraint clearly."
    else:
        prompt = f"{style} Summarize the final algorithm, complexity, and the highest-risk edge case in under one minute."
    return prompt + memory_clause


def _feedback(stage: InterviewStage, rubric_delta: dict[str, int], persona: InterviewPersona) -> list[str]:
    feedback = [f"Current stage: {stage.value}; persona style: {_persona_style(persona)}"]
    if rubric_delta["communication"] == 0:
        feedback.append("Structure your answer in approach, invariant, complexity, and tests.")
    if rubric_delta["correctness"] == 0:
        feedback.append("Name the core state, invariant, or data structure before implementation details.")
    if rubric_delta["complexity"] == 0:
        feedback.append("Add explicit Big-O reasoning when the interviewer asks for optimality.")
    if rubric_delta["testing"] == 0:
        feedback.append("Include edge cases proactively instead of waiting for a prompt.")
    return feedback


def _evaluation_summary(rubric_scores: dict[str, int], stage: InterviewStage) -> str:
    total = sum(rubric_scores.values())
    return f"Rubric total {total}/{len(RUBRIC_CATEGORIES) * 5}; latest stage was {stage.value}."


def _prior_scores(scorecard: dict[str, Any]) -> dict[str, int]:
    raw = scorecard.get("rubric_scores") if isinstance(scorecard, dict) else None
    return {category: int((raw or {}).get(category, 0)) for category in RUBRIC_CATEGORIES}


def _mentions_complexity(message: str) -> bool:
    return "o(" in message or "complex" in message or "time" in message or "space" in message


def _mentions_tests(message: str) -> bool:
    return "edge" in message or "test" in message or "empty" in message or "single" in message


def _persona_style(persona: InterviewPersona) -> str:
    if persona == "Google":
        return "Google-style: reason from invariants and clarify tradeoffs."
    if persona == "Meta":
        return "Meta-style: move crisply, communicate implementation-ready steps."
    if persona == "Amazon":
        return "Amazon-style: be pragmatic, test edge cases, and explain operational tradeoffs."
    return "Generic DSA style: be precise, structured, and honest about uncertainty."
