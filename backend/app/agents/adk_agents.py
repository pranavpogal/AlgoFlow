from __future__ import annotations

from app.agents.instructions import (
    ANALYTICS_INSTRUCTION,
    COORDINATOR_INSTRUCTION,
    HINT_INSTRUCTION,
    INTERVIEWER_INSTRUCTION,
    MEMORY_INSTRUCTION,
    MISTAKE_TRACKER_INSTRUCTION,
    PATTERN_TRANSFER_INSTRUCTION,
    PLANNER_INSTRUCTION,
    RECOMMENDATION_INSTRUCTION,
    REVIEW_INSTRUCTION,
    TOPIC_INSTRUCTION,
)
from app.core.config import get_settings
from app.tools.code_review import review_code_heuristics
from app.tools.learning_tools import build_weekly_plan, readiness_score
from app.tools.problem_intelligence import detect_problem_pattern, recommend_related_problems

settings = get_settings()

try:
    from google.adk.agents import Agent
except Exception:  # pragma: no cover - keeps local tests independent from ADK install
    Agent = None  # type: ignore[assignment]


def _agent(name: str, description: str, instruction: str, tools: list | None = None, sub_agents=None):
    if Agent is None:
        return {"name": name, "description": description, "instruction": instruction}
    return Agent(
        name=name,
        model=settings.gemini_model,
        description=description,
        instruction=instruction,
        tools=tools or [],
        sub_agents=sub_agents or [],
    )


topic_agent = _agent(
    "topic_agent",
    "Detects DSA concepts, prerequisites, and pattern labels from coding problems.",
    TOPIC_INSTRUCTION,
    tools=[detect_problem_pattern],
)

hint_agent = _agent(
    "hint_agent",
    "Provides adaptive, progressive hints without answer dumping.",
    HINT_INSTRUCTION,
)

review_agent = _agent(
    "review_agent",
    "Reviews submitted code for correctness, complexity, and engineering quality.",
    REVIEW_INSTRUCTION,
    tools=[review_code_heuristics],
)

memory_agent = _agent(
    "memory_agent",
    "Maintains structured long-term learner memory and personalization context.",
    MEMORY_INSTRUCTION,
)

planner_agent = _agent(
    "planner_agent",
    "Builds personalized study plans from goals, time budget, and weak topics.",
    PLANNER_INSTRUCTION,
    tools=[build_weekly_plan],
)

recommendation_agent = _agent(
    "recommendation_agent",
    "Recommends pattern-linked problems and difficulty progressions.",
    RECOMMENDATION_INSTRUCTION,
    tools=[recommend_related_problems],
)

mistake_tracker_agent = _agent(
    "mistake_tracker_agent",
    "Tracks repeated mistake categories and creates corrective insights.",
    MISTAKE_TRACKER_INSTRUCTION,
)

interviewer_agent = _agent(
    "interviewer_agent",
    "Runs realistic mock coding interviews with adaptive follow-up questions.",
    INTERVIEWER_INSTRUCTION,
)

analytics_agent = _agent(
    "analytics_agent",
    "Turns learning history into readiness analytics and visual dashboard data.",
    ANALYTICS_INSTRUCTION,
    tools=[readiness_score],
)

pattern_transfer_agent = _agent(
    "pattern_transfer_agent",
    "Teaches how a pattern transfers across related problems.",
    PATTERN_TRANSFER_INSTRUCTION,
)

root_agent = _agent(
    "coordinator_agent",
    "Root coordinator for AlgoFlow's multi-agent mentoring system.",
    COORDINATOR_INSTRUCTION,
    sub_agents=[
        topic_agent,
        hint_agent,
        review_agent,
        planner_agent,
        memory_agent,
        recommendation_agent,
        mistake_tracker_agent,
        interviewer_agent,
        analytics_agent,
        pattern_transfer_agent,
    ],
)
