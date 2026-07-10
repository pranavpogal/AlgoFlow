from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class HintIntent(StrEnum):
    IDEA_VALIDATION = "IDEA_VALIDATION"
    ONE_HINT = "ONE_HINT"
    ANOTHER_HINT = "ANOTHER_HINT"
    WHY_STATE_WRONG = "WHY_STATE_WRONG"
    NO_SOLUTION = "NO_SOLUTION"
    FULL_SOLUTION = "FULL_SOLUTION"
    CODE_REQUEST = "CODE_REQUEST"
    APPROACH_REVIEW = "APPROACH_REVIEW"
    ALREADY_KNOWS_RECURRENCE = "ALREADY_KNOWS_RECURRENCE"


class InterventionType(StrEnum):
    IDEA_VALIDATION = "IDEA_VALIDATION"
    REFLECTIVE_QUESTION = "REFLECTIVE_QUESTION"
    CONCEPTUAL_NUDGE = "CONCEPTUAL_NUDGE"
    MISCONCEPTION_CORRECTION = "MISCONCEPTION_CORRECTION"
    STATE_DEFINITION_PROMPT = "STATE_DEFINITION_PROMPT"
    INVARIANT_PROMPT = "INVARIANT_PROMPT"
    EDGE_CASE_PROMPT = "EDGE_CASE_PROMPT"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    COMPLEXITY_CHALLENGE = "COMPLEXITY_CHALLENGE"
    PARTIAL_PSEUDOCODE = "PARTIAL_PSEUDOCODE"
    EXPLICIT_SOLUTION = "EXPLICIT_SOLUTION"


@dataclass(frozen=True)
class HintContext:
    title: str
    description: str
    pattern: str
    difficulty: str
    current_hint_level: int
    user_attempt: str | None
    reveal_solution: bool
    learner_state: dict[str, Any]
    previous_hint_events: list[Any]


@dataclass(frozen=True)
class ProgressiveHintResult:
    intervention_type: InterventionType
    hint_level: int
    learner_state_confidence: str
    detected_misconception: str | None
    uses_previous_hint_context: bool
    solution_leakage_risk: str
    hint: str
    mentor_note: str
    reveals_solution: bool
    next_escalation_condition: str
    intent: HintIntent
    repeated_hint: bool = False


def generate_progressive_hint(context: HintContext) -> ProgressiveHintResult:
    intent = detect_intent(context.user_attempt, context.reveal_solution)
    previous_interventions = _previous_interventions(context.previous_hint_events)
    misconception = detect_misconception(context.user_attempt, context.pattern)
    intervention = select_intervention(context, intent, previous_interventions, misconception)
    repeated = intervention.value in previous_interventions
    if repeated and intervention is not InterventionType.EXPLICIT_SOLUTION:
        intervention = _next_non_repeating_intervention(intervention, previous_interventions)

    reveals_solution = intervention is InterventionType.EXPLICIT_SOLUTION and intent is HintIntent.FULL_SOLUTION
    hint = render_hint(context, intervention, intent, misconception, reveals_solution)
    leakage_risk = "high" if reveals_solution else "low"
    return ProgressiveHintResult(
        intervention_type=intervention,
        hint_level=5 if reveals_solution else min(context.current_hint_level + 1, 4),
        learner_state_confidence=context.learner_state.get("confidence", "unknown"),
        detected_misconception=misconception,
        uses_previous_hint_context=bool(previous_interventions),
        solution_leakage_risk=leakage_risk,
        hint=hint,
        mentor_note=mentor_note(context, intervention),
        reveals_solution=reveals_solution,
        next_escalation_condition=next_escalation_condition(intervention, reveals_solution),
        intent=intent,
        repeated_hint=repeated,
    )


def detect_intent(user_attempt: str | None, reveal_solution: bool) -> HintIntent:
    text = (user_attempt or "").lower()
    if reveal_solution or "full solution" in text or "give me the solution" in text:
        return HintIntent.FULL_SOLUTION
    if "don't give" in text or "do not give" in text or "no solution" in text:
        return HintIntent.NO_SOLUTION
    if "code" in text:
        return HintIntent.CODE_REQUEST
    if "am i" in text or "thinking correctly" in text or "is this correct" in text:
        return HintIntent.IDEA_VALIDATION
    if "why" in text and ("state" in text or "wrong" in text):
        return HintIntent.WHY_STATE_WRONG
    if "review my approach" in text or "approach" in text:
        return HintIntent.APPROACH_REVIEW
    if "already know" in text and "recurrence" in text:
        return HintIntent.ALREADY_KNOWS_RECURRENCE
    if "another" in text or "next hint" in text:
        return HintIntent.ANOTHER_HINT
    return HintIntent.ONE_HINT


def detect_misconception(user_attempt: str | None, pattern: str) -> str | None:
    text = (user_attempt or "").lower()
    if pattern == "Dynamic Programming" and "whether" in text and "robbed" in text:
        return "State stores action instead of optimal value"
    if pattern == "Dynamic Programming" and "dp" in text and "base" in text and "not" in text:
        return "Unclear DP base case"
    if "binary" in pattern.lower() and ("<= " in text or "boundary" in text):
        return "Binary search boundary uncertainty"
    if "visited" in text and "after" in text and "graph" in text:
        return "Graph visitation timing"
    return None


def select_intervention(
    context: HintContext,
    intent: HintIntent,
    previous_interventions: set[str],
    misconception: str | None,
) -> InterventionType:
    if intent is HintIntent.FULL_SOLUTION:
        return InterventionType.EXPLICIT_SOLUTION
    if misconception:
        return InterventionType.MISCONCEPTION_CORRECTION
    if intent is HintIntent.IDEA_VALIDATION:
        return InterventionType.IDEA_VALIDATION
    if intent is HintIntent.ALREADY_KNOWS_RECURRENCE:
        return InterventionType.EDGE_CASE_PROMPT
    if intent is HintIntent.CODE_REQUEST:
        return InterventionType.PARTIAL_PSEUDOCODE
    if context.pattern == "Dynamic Programming":
        if "STATE_DEFINITION_PROMPT" not in previous_interventions and context.current_hint_level <= 1:
            return InterventionType.STATE_DEFINITION_PROMPT
        if context.current_hint_level >= 3:
            return InterventionType.EDGE_CASE_PROMPT
        return InterventionType.CONCEPTUAL_NUDGE
    if context.pattern == "Graphs":
        if context.current_hint_level >= 2:
            return InterventionType.INVARIANT_PROMPT
        return InterventionType.REFLECTIVE_QUESTION
    if context.pattern == "Binary Search":
        return InterventionType.INVARIANT_PROMPT
    if context.current_hint_level >= 3:
        return InterventionType.COMPLEXITY_CHALLENGE
    return InterventionType.REFLECTIVE_QUESTION


def render_hint(
    context: HintContext,
    intervention: InterventionType,
    intent: HintIntent,
    misconception: str | None,
    reveals_solution: bool,
) -> str:
    if intervention is InterventionType.EXPLICIT_SOLUTION:
        return _solution_level_hint(context.pattern)
    if intervention is InterventionType.IDEA_VALIDATION:
        return "Yes, that is a useful direction. Now make it precise: what single state or invariant would let you compare choices without remembering the whole path?"
    if intervention is InterventionType.MISCONCEPTION_CORRECTION:
        return f"Careful: {misconception}. Try defining the state as the best result up to a position, not only what action happened at that position."
    if intervention is InterventionType.STATE_DEFINITION_PROMPT:
        return "Before writing a recurrence, define the state in one sentence. What should dp[i] mean so that the answer to a larger prefix can reuse smaller prefixes?"
    if intervention is InterventionType.CONCEPTUAL_NUDGE:
        return "You are looking for a relationship between the current position and earlier solved positions. What two choices are competing at this step?"
    if intervention is InterventionType.INVARIANT_PROMPT:
        return "Name the invariant you maintain after each step. What must be true after processing this node/index/search range?"
    if intervention is InterventionType.EDGE_CASE_PROMPT:
        return "Test your idea on the smallest inputs first. What should happen for size 0, size 1, and the first moment where the constraint actually matters?"
    if intervention is InterventionType.COUNTEREXAMPLE:
        return "Try constructing a tiny input where your current rule makes a greedy-looking choice. Does that choice block a better later option?"
    if intervention is InterventionType.COMPLEXITY_CHALLENGE:
        return "Look at the constraints and your nested work. Which part dominates runtime, and can any repeated work be cached or avoided?"
    if intervention is InterventionType.PARTIAL_PSEUDOCODE:
        if intent is HintIntent.CODE_REQUEST:
            return "I will keep this at pseudocode level for hint mode: initialize base state, iterate through positions, update from prior valid states, then return the final best state."
        return "Sketch only the loop shape, not full code: initialize state, iterate in dependency order, update from previous compatible states."
    return "What is the smallest subproblem whose answer would help you make the next decision?"


def mentor_note(context: HintContext, intervention: InterventionType) -> str:
    confidence = context.learner_state.get("confidence", "unknown")
    weak_topics = set(context.learner_state.get("weak_topics", []))
    if confidence in {"medium", "high"} and context.pattern in weak_topics:
        return f"I am focusing on {context.pattern} because your recent evidence points there as a growth area."
    if confidence == "unknown":
        return "I do not have enough learner evidence yet, so I am keeping the hint general and problem-focused."
    return f"This is a {intervention.value.lower().replace('_', ' ')} because it is the smallest useful next step I can give without taking ownership away from you."


def next_escalation_condition(intervention: InterventionType, reveals_solution: bool) -> str:
    if reveals_solution:
        return "Ask for implementation review or complexity discussion after studying the solution."
    if intervention is InterventionType.STATE_DEFINITION_PROMPT:
        return "Once you can state dp/state/invariant clearly, ask for the transition hint."
    if intervention is InterventionType.MISCONCEPTION_CORRECTION:
        return "Revise the state or invariant, then ask me to validate it."
    return "Try applying this hint to one small example before asking for another hint."


def _solution_level_hint(pattern: str) -> str:
    if pattern == "Dynamic Programming":
        return "Solution-level direction: define a state for the best answer up to each position, initialize the smallest cases, transition by comparing the competing choices, and return the final state."
    if pattern == "Graphs":
        return "Solution-level direction: model neighbors, track visited state, traverse systematically with DFS/BFS, and update the answer when each node or component is processed."
    if pattern == "Binary Search":
        return "Solution-level direction: identify a monotonic condition, search the answer/range boundaries, and update the range while preserving the invariant."
    return "Solution-level direction: define the reusable subproblem or invariant, process inputs in an order that preserves it, and verify edge cases."


def _previous_interventions(previous_hint_events: list[Any]) -> set[str]:
    interventions: set[str] = set()
    for event in previous_hint_events:
        evidence = getattr(event, "evidence", {}) or {}
        intervention = evidence.get("intervention_type")
        if intervention:
            interventions.add(str(intervention))
    return interventions


def _next_non_repeating_intervention(
    intervention: InterventionType, previous_interventions: set[str]
) -> InterventionType:
    order = [
        InterventionType.STATE_DEFINITION_PROMPT,
        InterventionType.CONCEPTUAL_NUDGE,
        InterventionType.EDGE_CASE_PROMPT,
        InterventionType.INVARIANT_PROMPT,
        InterventionType.COMPLEXITY_CHALLENGE,
        InterventionType.PARTIAL_PSEUDOCODE,
    ]
    try:
        start = order.index(intervention) + 1
    except ValueError:
        start = 0
    for candidate in order[start:] + order[:start]:
        if candidate.value not in previous_interventions:
            return candidate
    return InterventionType.REFLECTIVE_QUESTION
