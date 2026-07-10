from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.db.init_db import init_db
from app.main import app
from app.runtime.adk_runtime import AdkCoordinatorRuntime, CoordinatorDecision, MentorRoutingInput
from app.runtime.trajectory import Trajectory
from app.services import mentor_service as mentor_module


def test_coordinator_decision_accepts_bounded_tool_requests() -> None:
    decision = CoordinatorDecision.model_validate(
        {
            "selected_capability": "problem_analysis",
            "selected_skill": "problem_intelligence_workflow",
            "confidence": 0.9,
            "rationale": "Need bounded pattern detection before analysis.",
            "fallback_allowed": True,
            "tool_requests": [
                {
                    "tool_id": "problem.detect_pattern",
                    "purpose": "Classify the problem pattern.",
                    "arguments": {"title": "Untrusted model argument is not executed directly."},
                }
            ],
        }
    )

    assert decision.tool_requests[0].tool_id == "problem.detect_pattern"
    assert decision.tool_requests[0].purpose == "Classify the problem pattern."


@pytest.mark.asyncio
async def test_mentor_route_executes_adk_requested_detect_pattern_through_gateway(monkeypatch) -> None:
    async def invoker(agent, routing_input: MentorRoutingInput, trajectory: Trajectory):
        return {
            "selected_capability": "problem_analysis",
            "selected_skill": "problem_intelligence_workflow",
            "confidence": 0.92,
            "rationale": "Mock ADK requested bounded pattern detection.",
            "fallback_allowed": True,
            "tool_requests": [
                {
                    "tool_id": "problem.detect_pattern",
                    "purpose": "Classify the problem before selecting analysis response.",
                    "arguments": {"title": "Two Sum"},
                }
            ],
        }

    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True), invoker=invoker)
    monkeypatch.setattr(mentor_module, "adk_coordinator_runtime", runtime)
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/mentor/route",
            json={
                "requested_capability": "problem_analysis",
                "title": "Largest Divisible Subset",
                "description": "Given distinct positive integers, return the largest subset where pairs divide.",
            },
            headers={"x-request-id": "req_adk_tool_detect", "x-user-id": "adk-tool-user"},
        )
        body = response.json()
        policy_response = await client.get(
            f"/api/v1/agent-trajectories/{body['trajectory']['trajectory_id']}/policy-decisions",
            headers={"x-user-id": "adk-tool-user"},
        )

    event_types = [event["event_type"] for event in body["trajectory"]["events"]]
    tool_request_event = next(
        event for event in body["trajectory"]["events"] if event["event_type"] == "ADK_TOOL_REQUESTED"
    )
    policy = policy_response.json()[0]

    assert response.status_code == 200
    assert body["result"]["pattern"] == "Dynamic Programming"
    assert "ADK_TOOL_REQUESTED" in event_types
    assert "STRUCTURAL_POLICY_EVALUATED" in event_types
    assert "SEMANTIC_POLICY_EVALUATED" in event_types
    assert "TOOL_CALL_COMPLETED" in event_types
    assert tool_request_event["metadata"]["provided_argument_keys"] == ["title"]
    assert tool_request_event["metadata"]["trusted_argument_keys"] == ["description", "title"]
    assert policy_response.status_code == 200
    assert policy["tool_id"] == "problem.detect_pattern"
    assert policy["success"] is True
    assert policy["metadata"]["semantic_decision"]["reason_code"] == "BOUNDED_ANALYSIS_ALLOWED"


@pytest.mark.asyncio
async def test_mentor_route_denies_misaligned_adk_related_problem_request(monkeypatch) -> None:
    async def invoker(agent, routing_input: MentorRoutingInput, trajectory: Trajectory):
        return {
            "selected_capability": "next_hint",
            "selected_skill": "progressive_hinting_workflow",
            "confidence": 0.88,
            "rationale": "Mock ADK requested a recommendation tool in hint mode.",
            "fallback_allowed": True,
            "tool_requests": [
                {
                    "tool_id": "problem.related_problems",
                    "purpose": "Recommend transfer problems too early.",
                    "arguments": {"pattern": "Dynamic Programming"},
                }
            ],
        }

    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True), invoker=invoker)
    monkeypatch.setattr(mentor_module, "adk_coordinator_runtime", runtime)
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/mentor/route",
            json={
                "requested_capability": "next_hint",
                "user_message": "Give me one hint, not the answer.",
                "title": "House Robber",
                "description": "Find max sum without adjacent houses.",
                "current_hint_level": 0,
            },
            headers={"x-request-id": "req_adk_tool_deny", "x-user-id": "adk-tool-deny-user"},
        )
        body = response.json()
        policy_response = await client.get(
            f"/api/v1/agent-trajectories/{body['trajectory']['trajectory_id']}/policy-decisions",
            headers={"x-user-id": "adk-tool-deny-user"},
        )

    event_types = [event["event_type"] for event in body["trajectory"]["events"]]
    policy = policy_response.json()[0]

    assert response.status_code == 200
    assert body["selected_capability"] == "next_hint"
    assert body["result"]["reveals_solution"] is False
    assert "ADK_TOOL_REQUESTED" in event_types
    assert "TOOL_CALL_DENIED" in event_types
    assert "TOOL_CALL_COMPLETED" not in event_types
    assert policy_response.status_code == 200
    assert policy["tool_id"] == "problem.related_problems"
    assert policy["success"] is False
    assert policy["metadata"]["semantic_decision"]["reason_code"] == "CAPABILITY_TOOL_MISMATCH"


@pytest.mark.asyncio
async def test_adk_runtime_deterministic_route_can_select_recommendations() -> None:
    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=False))
    trajectory = Trajectory.start("mentor_route", session_id="session_recommendations")

    decision = await runtime.route(
        MentorRoutingInput(
            requested_capability="recommendations",
            user_message="Recommend related practice problems.",
            title="House Robber",
            description="Find max sum without adjacent houses.",
        ),
        trajectory,
    )

    assert decision.selected_capability == "recommendations"
    assert decision.selected_skill == "pattern_recommendation_workflow"
    assert trajectory.fallback_used is True


@pytest.mark.asyncio
async def test_adk_runtime_deterministic_route_can_select_pattern_transfer() -> None:
    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=False))
    trajectory = Trajectory.start("mentor_route", session_id="session_pattern_transfer")

    decision = await runtime.route(
        MentorRoutingInput(
            requested_capability="pattern_transfer",
            user_message="Show me how to transfer this pattern.",
            title="House Robber",
            description="Find max sum without adjacent houses.",
        ),
        trajectory,
    )

    assert decision.selected_capability == "pattern_transfer"
    assert decision.selected_skill == "pattern_transfer_workflow"
    assert trajectory.fallback_used is True


@pytest.mark.asyncio
async def test_adk_runtime_deterministic_route_can_select_code_review() -> None:
    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=False))
    trajectory = Trajectory.start("mentor_route", session_id="session_code_review")

    decision = await runtime.route(
        MentorRoutingInput(
            requested_capability="code_review",
            user_message="Review my code and find the bug.",
            title="House Robber",
            description="Find max sum without adjacent houses.",
        ),
        trajectory,
    )

    assert decision.selected_capability == "code_review"
    assert decision.selected_skill == "code_review_workflow"
    assert trajectory.fallback_used is True


@pytest.mark.asyncio
async def test_adk_runtime_deterministic_route_can_select_study_plan() -> None:
    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=False))
    trajectory = Trajectory.start("mentor_route", session_id="session_study_plan")

    decision = await runtime.route(
        MentorRoutingInput(
            requested_capability="study_plan",
            user_message="Build a study plan for my interview prep.",
            title="Study Planner",
            description="Create a realistic preparation plan.",
        ),
        trajectory,
    )

    assert decision.selected_capability == "study_plan"
    assert decision.selected_skill == "study_planning_workflow"
    assert trajectory.fallback_used is True


@pytest.mark.asyncio
async def test_mentor_route_executes_adk_requested_related_problems_for_recommendations(monkeypatch) -> None:
    async def invoker(agent, routing_input: MentorRoutingInput, trajectory: Trajectory):
        return {
            "selected_capability": "recommendations",
            "selected_skill": "pattern_recommendation_workflow",
            "confidence": 0.9,
            "rationale": "Mock ADK requested governed related-problem recommendations.",
            "fallback_allowed": True,
            "tool_requests": [
                {
                    "tool_id": "problem.related_problems",
                    "purpose": "Recommend structurally related practice problems.",
                    "arguments": {"pattern": "Dynamic Programming"},
                }
            ],
        }

    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True), invoker=invoker)
    monkeypatch.setattr(mentor_module, "adk_coordinator_runtime", runtime)
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/mentor/route",
            json={
                "requested_capability": "recommendations",
                "user_message": "Recommend what I should solve next.",
                "title": "House Robber",
                "description": "Find max sum without adjacent houses.",
            },
            headers={"x-request-id": "req_adk_recommend", "x-user-id": "adk-recommend-user"},
        )
        body = response.json()
        policy_response = await client.get(
            f"/api/v1/agent-trajectories/{body['trajectory']['trajectory_id']}/policy-decisions",
            headers={"x-user-id": "adk-recommend-user"},
        )

    event_types = [event["event_type"] for event in body["trajectory"]["events"]]
    policy = policy_response.json()[0]

    assert response.status_code == 200
    assert body["selected_capability"] == "recommendations"
    assert body["selected_skill"] == "pattern_recommendation_workflow"
    assert body["result"]["core_pattern"] == "Dynamic Programming"
    assert body["result"]["related_problems"]
    assert body["result"]["fallback_reason"] is None
    assert "ADK_TOOL_REQUESTED" in event_types
    assert "TOOL_CALL_COMPLETED" in event_types
    assert policy_response.status_code == 200
    assert policy["tool_id"] == "problem.related_problems"
    assert policy["success"] is True
    assert policy["metadata"]["semantic_decision"]["reason_code"] == "INTENT_ALIGNED"


@pytest.mark.asyncio
async def test_mentor_route_executes_adk_requested_related_problems_for_pattern_transfer(
    monkeypatch,
) -> None:
    async def invoker(agent, routing_input: MentorRoutingInput, trajectory: Trajectory):
        return {
            "selected_capability": "pattern_transfer",
            "selected_skill": "pattern_transfer_workflow",
            "confidence": 0.9,
            "rationale": "Mock ADK requested governed pattern-transfer candidates.",
            "fallback_allowed": True,
            "tool_requests": [
                {
                    "tool_id": "problem.related_problems",
                    "purpose": "Find structurally transferable practice problems.",
                    "arguments": {"pattern": "Dynamic Programming"},
                }
            ],
        }

    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True), invoker=invoker)
    monkeypatch.setattr(mentor_module, "adk_coordinator_runtime", runtime)
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/mentor/route",
            json={
                "requested_capability": "pattern_transfer",
                "user_message": "Transfer this pattern to related variations.",
                "title": "House Robber",
                "description": "Find max sum without adjacent houses.",
            },
            headers={"x-request-id": "req_adk_transfer", "x-user-id": "adk-transfer-user"},
        )
        body = response.json()
        policy_response = await client.get(
            f"/api/v1/agent-trajectories/{body['trajectory']['trajectory_id']}/policy-decisions",
            headers={"x-user-id": "adk-transfer-user"},
        )

    event_types = [event["event_type"] for event in body["trajectory"]["events"]]
    policy = policy_response.json()[0]

    assert response.status_code == 200
    assert body["selected_capability"] == "pattern_transfer"
    assert body["selected_skill"] == "pattern_transfer_workflow"
    assert body["result"]["source_pattern"] == "Dynamic Programming"
    assert body["result"]["transfer_to"]
    assert body["result"]["fallback_reason"] is None
    assert "ADK_TOOL_REQUESTED" in event_types
    assert "TOOL_CALL_COMPLETED" in event_types
    assert policy_response.status_code == 200
    assert policy["tool_id"] == "problem.related_problems"
    assert policy["success"] is True
    assert policy["metadata"]["semantic_decision"]["reason_code"] == "INTENT_ALIGNED"


@pytest.mark.asyncio
async def test_mentor_route_executes_adk_requested_static_code_review(monkeypatch) -> None:
    async def invoker(agent, routing_input: MentorRoutingInput, trajectory: Trajectory):
        return {
            "selected_capability": "code_review",
            "selected_skill": "code_review_workflow",
            "confidence": 0.9,
            "rationale": "Mock ADK requested governed static code review.",
            "fallback_allowed": True,
            "tool_requests": [
                {
                    "tool_id": "code.review_static",
                    "purpose": "Review learner code without executing it.",
                    "arguments": {"code": "Untrusted model-provided code is ignored."},
                }
            ],
        }

    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True), invoker=invoker)
    monkeypatch.setattr(mentor_module, "adk_coordinator_runtime", runtime)
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/mentor/route",
            json={
                "requested_capability": "code_review",
                "user_message": "Review my code and find the bug.",
                "title": "House Robber",
                "description": "Find max sum without adjacent houses.",
                "language": "Python",
                "code": "def rob(nums):\n    dp = [0] * len(nums)\n    for i in range(len(nums)):\n        dp[i] = max(dp[i-1], nums[i] + dp[i-1])\n    return dp[-1]",
            },
            headers={"x-request-id": "req_adk_code_review", "x-user-id": "adk-code-review-user"},
        )
        body = response.json()
        policy_response = await client.get(
            f"/api/v1/agent-trajectories/{body['trajectory']['trajectory_id']}/policy-decisions",
            headers={"x-user-id": "adk-code-review-user"},
        )

    event_types = [event["event_type"] for event in body["trajectory"]["events"]]
    policy = policy_response.json()[0]

    assert response.status_code == 200
    assert body["selected_capability"] == "code_review"
    assert body["selected_skill"] == "code_review_workflow"
    assert body["result"]["findings"]
    assert body["result"]["rewrite_allowed"] is False
    assert "python_ast_parse" in body["result"]["analysis_layers"]
    assert "ADK_TOOL_REQUESTED" in event_types
    assert "TOOL_CALL_COMPLETED" in event_types
    assert policy_response.status_code == 200
    assert policy["tool_id"] == "code.review_static"
    assert policy["success"] is True
    assert policy["metadata"]["semantic_decision"]["reason_code"] == "INTENT_ALIGNED"


@pytest.mark.asyncio
async def test_mentor_route_recommendations_without_tool_request_uses_safe_fallback() -> None:
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/mentor/route",
            json={
                "requested_capability": "recommendations",
                "user_message": "Recommend what I should solve next.",
                "title": "House Robber",
                "description": "Find max sum without adjacent houses.",
            },
            headers={"x-request-id": "req_adk_recommend_fallback", "x-user-id": "adk-recommend-fallback-user"},
        )

    body = response.json()
    event_types = [event["event_type"] for event in body["trajectory"]["events"]]

    assert response.status_code == 200
    assert body["selected_capability"] == "recommendations"
    assert body["result"]["related_problems"] == []
    assert body["result"]["fallback_reason"] == "policy_gated_tool_unavailable"
    assert "TOOL_CALL_COMPLETED" not in event_types


@pytest.mark.asyncio
async def test_mentor_route_pattern_transfer_without_tool_request_uses_safe_fallback() -> None:
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/mentor/route",
            json={
                "requested_capability": "pattern_transfer",
                "user_message": "Transfer this pattern to related variations.",
                "title": "House Robber",
                "description": "Find max sum without adjacent houses.",
            },
            headers={"x-request-id": "req_adk_transfer_fallback", "x-user-id": "adk-transfer-fallback-user"},
        )

    body = response.json()
    event_types = [event["event_type"] for event in body["trajectory"]["events"]]

    assert response.status_code == 200
    assert body["selected_capability"] == "pattern_transfer"
    assert body["result"]["transfer_to"] == []
    assert body["result"]["fallback_reason"] == "policy_gated_tool_unavailable"
    assert "TOOL_CALL_COMPLETED" not in event_types


@pytest.mark.asyncio
async def test_mentor_route_code_review_without_tool_request_uses_safe_fallback() -> None:
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/mentor/route",
            json={
                "requested_capability": "code_review",
                "user_message": "Review my code.",
                "title": "House Robber",
                "description": "Find max sum without adjacent houses.",
                "language": "Python",
                "code": "def rob(nums):\n    return sum(nums)",
            },
            headers={"x-request-id": "req_adk_code_review_fallback", "x-user-id": "adk-code-review-fallback"},
        )

    body = response.json()
    event_types = [event["event_type"] for event in body["trajectory"]["events"]]

    assert response.status_code == 200
    assert body["selected_capability"] == "code_review"
    assert body["result"]["analysis_layers"] == ["policy_gated_tool_unavailable"]
    assert body["result"]["unsupported_claims"] == ["No code analysis was performed."]
    assert "TOOL_CALL_COMPLETED" not in event_types


@pytest.mark.asyncio
async def test_mentor_route_study_plan_executes_deterministic_planner_without_tools() -> None:
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/mentor/route",
            json={
                "requested_capability": "study_plan",
                "user_message": "Create a 30 day Google study plan.",
                "title": "Study Planner",
                "description": "Create a realistic preparation plan.",
                "target_company": "Google",
                "days_remaining": 30,
                "hours_per_week": 10,
            },
            headers={"x-request-id": "req_adk_study_plan", "x-user-id": "adk-study-plan-user"},
        )

    body = response.json()
    event_types = [event["event_type"] for event in body["trajectory"]["events"]]

    assert response.status_code == 200
    assert body["selected_capability"] == "study_plan"
    assert body["selected_skill"] == "study_planning_workflow"
    assert body["result"]["target_company"] == "Google"
    assert body["result"]["days_remaining"] == 30
    assert body["result"]["weekly_plan"]
    assert "WORKFLOW_EXECUTED" in event_types
    assert "ADK_TOOL_REQUESTED" not in event_types
    assert "TOOL_CALL_COMPLETED" not in event_types
