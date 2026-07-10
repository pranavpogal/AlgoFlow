from __future__ import annotations

import pytest

from app.core.auth import Principal
from app.core.semantic_policy import MentoringMode, SemanticPolicyContext
from app.core.tool_gateway import ToolGatewayError, tool_gateway
from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal
from app.memory.repository import (
    policy_decisions_for_trajectory,
    record_agent_trajectory,
    record_policy_decision,
)
from app.runtime.trajectory import Trajectory


def _semantic_context(
    *,
    tool_id: str = "problem.detect_pattern",
    capability: str = "problem_analysis",
    intent: str = "PROBLEM_ANALYSIS",
    mode: str = MentoringMode.EXPLAIN_CONCEPT.value,
    title: str = "House Robber",
    description: str = "Find max sum without adjacent houses.",
) -> SemanticPolicyContext:
    payload = {"title": title, "description": description}
    if tool_id == "problem.related_problems":
        payload = {"pattern": "Dynamic Programming"}
    return SemanticPolicyContext(
        principal_id="tool-user",
        caller_id="adk_narrow_coordinator",
        selected_capability=capability,
        user_intent=intent,
        mentoring_mode=mode,
        requested_tool_id=tool_id,
        operation_type="draft" if tool_id == "problem.related_problems" else "read",
        tool_arguments=payload,
        task_context={"title": title, "description": description, "user_message": ""},
        reveal_authorized=False,
    )


def test_tool_gateway_allows_registered_read_tool_and_records_trajectory() -> None:
    trajectory = Trajectory.start("tool_gateway_test", session_id="session_tool")

    result, record = tool_gateway.call(
        "problem.detect_pattern",
        {"title": "House Robber", "description": "Find max sum without adjacent houses."},
        caller="adk_narrow_coordinator",
        principal=Principal(user_id="tool-user", auth_mode="test"),
        trajectory=trajectory,
        semantic_context=_semantic_context(),
    )

    assert result["pattern"] == "Dynamic Programming"
    assert record.success is True
    assert record.decision.decision == "allow"
    assert any(event.event_type == "TOOL_CALL_COMPLETED" for event in trajectory.events)


def test_tool_gateway_denies_unregistered_caller_and_records_denial() -> None:
    trajectory = Trajectory.start("tool_gateway_test", session_id="session_tool")

    with pytest.raises(ToolGatewayError):
        tool_gateway.call(
            "problem.detect_pattern",
            {"title": "House Robber", "description": "Find max sum without adjacent houses."},
            caller="decorative_agent",
            principal=Principal(user_id="tool-user", auth_mode="test"),
            trajectory=trajectory,
            semantic_context=_semantic_context(),
        )

    assert any(event.event_type == "TOOL_CALL_DENIED" for event in trajectory.events)
    denial = next(event for event in trajectory.events if event.event_type == "TOOL_CALL_DENIED")
    assert denial.metadata["decision"]["policy_id"] == "tool.caller.denied"


def test_tool_gateway_rejects_invalid_input() -> None:
    trajectory = Trajectory.start("tool_gateway_test", session_id="session_tool")

    with pytest.raises(Exception):
        tool_gateway.call(
            "problem.detect_pattern",
            {"title": "House Robber"},
            caller="adk_narrow_coordinator",
            trajectory=trajectory,
            semantic_context=_semantic_context(),
        )

    failure = next(event for event in trajectory.events if event.event_type == "TOOL_CALL_DENIED")
    assert failure.metadata["error"] == "ValidationError"


def test_tool_gateway_recommend_related_problems_is_draft_only() -> None:
    result, record = tool_gateway.call(
        "problem.related_problems",
        {"pattern": "Dynamic Programming"},
        caller="mentor_service",
        principal=Principal(user_id="tool-user", auth_mode="test"),
        semantic_context=_semantic_context(
            tool_id="problem.related_problems",
            capability="recommendations",
            intent="RECOMMENDATION",
            mode=MentoringMode.RECOMMEND_TRANSFER.value,
        ),
    )

    assert result[0]["title"] == "Climbing Stairs"
    assert record.operation == "draft"
    assert record.risk == "low"


@pytest.mark.asyncio
async def test_tool_gateway_policy_decision_can_be_persisted_with_trajectory_identity() -> None:
    await init_db()
    trajectory = Trajectory.start("tool_gateway_persistence", session_id="session_policy_store")
    result, record = tool_gateway.call(
        "problem.detect_pattern",
        {"title": "House Robber", "description": "Find max sum without adjacent houses."},
        caller="adk_narrow_coordinator",
        principal=Principal(user_id="policy-store-user", auth_mode="test"),
        trajectory=trajectory,
        semantic_context=_semantic_context(),
    )
    trajectory.finish()
    trajectory_payload = trajectory.to_dict()

    async with AsyncSessionLocal() as session:
        await record_agent_trajectory(
            session,
            "policy-store-user",
            trajectory_payload,
            selected_skill="problem_intelligence_workflow",
        )
        stored = await record_policy_decision(
            session,
            user_id="policy-store-user",
            tool_call=record.to_dict(),
            trajectory=trajectory_payload,
            metadata={"source_route": "test"},
        )
        rows = await policy_decisions_for_trajectory(
            session,
            "policy-store-user",
            trajectory_payload["trajectory_id"],
        )

    assert result["pattern"] == "Dynamic Programming"
    assert stored.tool_id == "problem.detect_pattern"
    assert rows[0].trajectory_id == trajectory_payload["trajectory_id"]
    assert rows[0].trace_id == trajectory_payload["trace_id"]
    assert rows[0].session_id == "session_policy_store"
    assert rows[0].decision == "allow"
    assert rows[0].policy_id == "tool.read.allowed"
    assert rows[0].success is True
    assert rows[0].decision_metadata["source_route"] == "test"
    assert rows[0].decision_metadata["semantic_decision"]["policy_version"] == "semantic-tool-policy-v1"
