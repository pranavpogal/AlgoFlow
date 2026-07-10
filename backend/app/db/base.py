from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String, default="AlgoFlow Learner")
    target_company: Mapped[str | None] = mapped_column(String, nullable=True)
    profile: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    problem_attempts: Mapped[list["ProblemAttempt"]] = relationship(back_populates="user")
    mistakes: Mapped[list["Mistake"]] = relationship(back_populates="user")
    interviews: Mapped[list["InterviewSession"]] = relationship(back_populates="user")
    learning_events: Mapped[list["LearningEvent"]] = relationship(back_populates="user")
    agent_trajectories: Mapped[list["AgentTrajectory"]] = relationship(back_populates="user")
    policy_decisions: Mapped[list["PolicyDecisionRecord"]] = relationship(back_populates="user")


class ProblemAttempt(Base, TimestampMixin):
    __tablename__ = "problem_attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    problem_number: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, index=True)
    difficulty: Mapped[str | None] = mapped_column(String, nullable=True)
    pattern: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="attempted")
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    review: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    user: Mapped[User] = relationship(back_populates="problem_attempts")


class Mistake(Base, TimestampMixin):
    __tablename__ = "mistakes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    pattern: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[int] = mapped_column(Integer, default=2)
    evidence: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    user: Mapped[User] = relationship(back_populates="mistakes")


class InterviewSession(Base, TimestampMixin):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    persona: Mapped[str] = mapped_column(String, default="Generic DSA Interviewer")
    problem_title: Mapped[str | None] = mapped_column(String, nullable=True)
    transcript: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    scorecard: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    user: Mapped[User] = relationship(back_populates="interviews")


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String, default="algoflow")
    problem_title: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    concept: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="learning_events")


class AgentTrajectory(Base):
    __tablename__ = "agent_trajectories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    request_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    trace_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    task: Mapped[str] = mapped_column(String, index=True)
    runtime_mode: Mapped[str] = mapped_column(String, index=True)
    selected_capability: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    selected_skill: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    fallback_used: Mapped[bool] = mapped_column(default=False)
    duration_ms: Mapped[float | None] = mapped_column(nullable=True)
    schema_version: Mapped[str] = mapped_column(String, default="trajectory-v1")
    event_count: Mapped[int] = mapped_column(Integer, default=0)
    events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    trajectory_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="agent_trajectories")


class PolicyDecisionRecord(Base):
    __tablename__ = "policy_decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    request_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    trace_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    trajectory_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    tool_id: Mapped[str] = mapped_column(String, index=True)
    caller: Mapped[str] = mapped_column(String, index=True)
    operation: Mapped[str] = mapped_column(String, index=True)
    risk: Mapped[str] = mapped_column(String, index=True)
    decision: Mapped[str] = mapped_column(String, index=True)
    policy_id: Mapped[str] = mapped_column(String, index=True)
    reason: Mapped[str] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(default=False)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(nullable=True)
    decision_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User | None] = relationship(back_populates="policy_decisions")
