from collections import Counter, defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import (
    AgentTrajectory,
    LearningEvent,
    Mistake,
    PolicyDecisionRecord,
    ProblemAttempt,
    User,
)


DEFAULT_PROFILE = {
    "strong_topics": ["Hash Maps", "Sliding Window"],
    "weak_topics": ["Dynamic Programming", "Graphs"],
    "pattern_mastery": {
        "Hash Maps": 78,
        "Sliding Window": 74,
        "Trees": 55,
        "Dynamic Programming": 42,
        "Graphs": 38,
    },
}


async def get_or_create_user(session: AsyncSession, user_id: str) -> User:
    user = await session.get(User, user_id)
    if user:
        return user
    user = User(id=user_id, email=f"{user_id}@local.algoflow", profile=DEFAULT_PROFILE)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def remember_attempt(
    session: AsyncSession,
    user_id: str,
    title: str,
    pattern: str | None = None,
    difficulty: str | None = None,
    language: str | None = None,
    code: str | None = None,
    review: dict[str, Any] | None = None,
) -> ProblemAttempt:
    await get_or_create_user(session, user_id)
    attempt = ProblemAttempt(
        user_id=user_id,
        title=title,
        pattern=pattern,
        difficulty=difficulty,
        language=language,
        code=code,
        review=review or {},
        status="reviewed" if review else "analyzed",
    )
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return attempt


async def remember_mistakes(
    session: AsyncSession, user_id: str, mistakes: list[str], pattern: str | None = None
) -> None:
    await get_or_create_user(session, user_id)
    for item in mistakes:
        session.add(Mistake(user_id=user_id, category=item, pattern=pattern, evidence=item))
    await session.commit()


async def record_learning_event(
    session: AsyncSession,
    user_id: str,
    event_type: str,
    *,
    source: str = "algoflow",
    problem_title: str | None = None,
    concept: str | None = None,
    evidence: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> LearningEvent:
    await get_or_create_user(session, user_id)
    event = LearningEvent(
        user_id=user_id,
        event_type=event_type,
        source=source,
        problem_title=problem_title,
        concept=concept,
        evidence=evidence or {},
        event_metadata=metadata or {},
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def learning_events_for_user(
    session: AsyncSession,
    user_id: str,
    *,
    event_type: str | None = None,
    limit: int = 50,
) -> list[LearningEvent]:
    query = select(LearningEvent).where(LearningEvent.user_id == user_id)
    if event_type:
        query = query.where(LearningEvent.event_type == event_type)
    query = query.order_by(LearningEvent.created_at.desc()).limit(limit)
    return (await session.execute(query)).scalars().all()


async def record_agent_trajectory(
    session: AsyncSession,
    user_id: str,
    trajectory: dict[str, Any],
    *,
    selected_skill: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AgentTrajectory:
    await get_or_create_user(session, user_id)
    events = trajectory.get("events", [])
    row = AgentTrajectory(
        id=trajectory["trajectory_id"],
        user_id=user_id,
        request_id=trajectory.get("request_id"),
        trace_id=trajectory.get("trace_id"),
        session_id=trajectory.get("session_id"),
        task=trajectory["task"],
        runtime_mode=trajectory["runtime_mode"],
        selected_capability=trajectory.get("selected_capability"),
        selected_skill=selected_skill,
        fallback_used=bool(trajectory.get("fallback_used")),
        duration_ms=trajectory.get("duration_ms"),
        schema_version=trajectory.get("schema_version", "trajectory-v1"),
        event_count=len(events),
        events=events,
        trajectory_metadata=metadata or {},
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def trajectory_for_user(
    session: AsyncSession, user_id: str, trajectory_id: str
) -> AgentTrajectory | None:
    query = select(AgentTrajectory).where(
        AgentTrajectory.user_id == user_id, AgentTrajectory.id == trajectory_id
    )
    return (await session.execute(query)).scalar_one_or_none()


async def recent_trajectories_for_user(
    session: AsyncSession, user_id: str, *, limit: int = 20
) -> list[AgentTrajectory]:
    query = (
        select(AgentTrajectory)
        .where(AgentTrajectory.user_id == user_id)
        .order_by(AgentTrajectory.created_at.desc())
        .limit(limit)
    )
    return (await session.execute(query)).scalars().all()


async def record_policy_decision(
    session: AsyncSession,
    *,
    user_id: str | None,
    tool_call: dict[str, Any],
    trajectory: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> PolicyDecisionRecord:
    if user_id:
        await get_or_create_user(session, user_id)
    decision = tool_call["decision"]
    decision_metadata = {
        **(metadata or {}),
        "structural_decision": decision,
        "semantic_decision": tool_call.get("semantic_decision"),
        "final_decision": tool_call.get("decision"),
    }
    row = PolicyDecisionRecord(
        user_id=user_id,
        request_id=(trajectory or {}).get("request_id") or decision.get("request_id"),
        trace_id=(trajectory or {}).get("trace_id"),
        session_id=(trajectory or {}).get("session_id"),
        trajectory_id=(trajectory or {}).get("trajectory_id"),
        tool_id=tool_call["tool_id"],
        caller=tool_call["caller"],
        operation=tool_call["operation"],
        risk=tool_call["risk"],
        decision=decision["decision"],
        policy_id=decision["policy_id"],
        reason=decision["reason"],
        success=bool(tool_call.get("success")),
        error=tool_call.get("error"),
        latency_ms=tool_call.get("latency_ms"),
        decision_metadata=decision_metadata,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def policy_decisions_for_trajectory(
    session: AsyncSession,
    user_id: str,
    trajectory_id: str,
) -> list[PolicyDecisionRecord]:
    query = (
        select(PolicyDecisionRecord)
        .where(
            PolicyDecisionRecord.user_id == user_id,
            PolicyDecisionRecord.trajectory_id == trajectory_id,
        )
        .order_by(PolicyDecisionRecord.created_at)
    )
    return (await session.execute(query)).scalars().all()


async def user_memory_snapshot(session: AsyncSession, user_id: str) -> dict[str, Any]:
    user = await get_or_create_user(session, user_id)
    attempts = (
        await session.execute(
            select(ProblemAttempt).where(ProblemAttempt.user_id == user_id).order_by(ProblemAttempt.created_at)
        )
    ).scalars().all()
    mistakes = (
        await session.execute(select(Mistake).where(Mistake.user_id == user_id))
    ).scalars().all()
    learning_events = (
        await session.execute(select(LearningEvent).where(LearningEvent.user_id == user_id))
    ).scalars().all()

    pattern_counts = Counter(a.pattern for a in attempts if a.pattern)
    mistake_counts = Counter(m.category for m in mistakes)
    learning_event_counts = Counter(event.event_type for event in learning_events)
    recent = [
        {"title": a.title, "pattern": a.pattern, "difficulty": a.difficulty, "status": a.status}
        for a in attempts[-10:]
    ]

    topic_history: dict[str, list[str]] = defaultdict(list)
    for a in attempts:
        if a.pattern:
            topic_history[a.pattern].append(a.title)

    return {
        "profile": user.profile or DEFAULT_PROFILE,
        "attempt_count": len(attempts),
        "learning_event_count": len(learning_events),
        "learning_event_counts": dict(learning_event_counts),
        "recent_attempts": recent,
        "pattern_counts": dict(pattern_counts),
        "mistake_counts": dict(mistake_counts),
        "topic_history": dict(topic_history),
    }
