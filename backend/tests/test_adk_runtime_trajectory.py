from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.db.init_db import init_db
from app.main import app
from app.runtime import adk_runtime
from app.runtime.adk_runtime import AdkCoordinatorRuntime, LiveAdkDecisionInvoker, MentorRoutingInput
from app.runtime.trajectory import RuntimeMode, Trajectory


@pytest.mark.asyncio
async def test_adk_runtime_disabled_uses_deterministic_hint_fallback() -> None:
    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=False))
    trajectory = Trajectory.start("mentor_route", session_id="session_test")

    decision = await runtime.route(
        MentorRoutingInput(
            requested_capability="next_hint",
            user_message="give me one hint",
            title="House Robber",
            description="Find max sum without adjacent houses.",
            current_hint_level=1,
        ),
        trajectory,
    )

    assert runtime.agent is not None
    assert decision.selected_capability == "next_hint"
    assert decision.selected_skill == "progressive_hinting_workflow"
    assert trajectory.runtime_mode == RuntimeMode.ADK_DISABLED
    assert trajectory.fallback_used is True
    assert trajectory.selected_capability == "next_hint"
    assert any(event.event_type == "ADK_INVOCATION_SKIPPED" for event in trajectory.events)


@pytest.mark.asyncio
async def test_adk_runtime_mock_invoker_can_select_problem_analysis() -> None:
    async def invoker(agent, routing_input, trajectory):
        assert agent is not None
        return {
            "selected_capability": "problem_analysis",
            "selected_skill": "problem_intelligence_workflow",
            "confidence": 0.91,
            "rationale": "Mock ADK chose classification for a problem-analysis request.",
            "fallback_allowed": True,
        }

    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True), invoker=invoker)
    trajectory = Trajectory.start("mentor_route")

    decision = await runtime.route(
        MentorRoutingInput(
            requested_capability=None,
            user_message="what pattern is this?",
            title="Largest Divisible Subset",
            description="Find the largest divisible subset.",
        ),
        trajectory,
    )

    assert decision.selected_capability == "problem_analysis"
    assert trajectory.runtime_mode == RuntimeMode.ADK_MOCKED
    assert trajectory.fallback_used is False
    assert any(event.event_type == "ADK_INVOCATION_COMPLETED" for event in trajectory.events)


@pytest.mark.asyncio
async def test_adk_runtime_invalid_invoker_falls_back_safely() -> None:
    async def invalid_invoker(agent, routing_input, trajectory):
        return {"selected_capability": "unsupported"}

    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True), invoker=invalid_invoker)
    trajectory = Trajectory.start("mentor_route")

    decision = await runtime.route(
        MentorRoutingInput(
            requested_capability="next_hint",
            user_message="hint only please",
            title="House Robber",
            description="Find max sum without adjacent houses.",
            current_hint_level=0,
        ),
        trajectory,
    )

    assert decision.selected_capability == "next_hint"
    assert trajectory.runtime_mode == RuntimeMode.ADK_FALLBACK
    assert trajectory.fallback_used is True
    assert any(event.event_type == "ADK_INVOCATION_FAILED" for event in trajectory.events)


@pytest.mark.asyncio
async def test_live_adk_enabled_without_key_falls_back_without_invocation() -> None:
    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True, google_api_key=None))
    trajectory = Trajectory.start("mentor_route", session_id="session_test")

    decision = await runtime.route(
        MentorRoutingInput(
            requested_capability="problem_analysis",
            user_message="what pattern is this?",
            title="House Robber",
            description="Find max sum without adjacent houses.",
        ),
        trajectory,
    )

    assert decision.selected_capability == "problem_analysis"
    assert runtime.invoker is None
    assert trajectory.runtime_mode == RuntimeMode.ADK_FALLBACK
    assert trajectory.fallback_used is True
    assert any(event.event_type == "ADK_INVOCATION_SKIPPED" for event in trajectory.events)


@pytest.mark.asyncio
async def test_live_adk_invoker_parses_runner_output_and_records_events(monkeypatch) -> None:
    class FakePart:
        def __init__(self, text):
            self.text = text

        @classmethod
        def from_text(cls, text):
            return cls(text)

    class FakeContent:
        def __init__(self, role=None, parts=None):
            self.role = role
            self.parts = parts or []

    class FakeTypes:
        Content = FakeContent
        Part = FakePart

    class FakeEvent:
        author = "algoflow_narrow_coordinator"
        output = {
            "selected_capability": "next_hint",
            "selected_skill": "progressive_hinting_workflow",
            "confidence": 0.93,
            "rationale": "Live ADK chose hint mode.",
            "fallback_allowed": True,
        }

        def is_final_response(self):
            return True

    class FakeRunner:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def run_async(self, **kwargs):
            yield FakeEvent()

    class FakeSessionService:
        pass

    monkeypatch.setattr(adk_runtime, "Runner", FakeRunner)
    monkeypatch.setattr(adk_runtime, "InMemorySessionService", FakeSessionService)
    monkeypatch.setattr(adk_runtime, "genai_types", FakeTypes)

    runtime = AdkCoordinatorRuntime(
        settings=Settings(enable_live_adk=True, google_api_key="test-key"),
    )
    trajectory = Trajectory.start("mentor_route", session_id="session_live_test")

    decision = await runtime.route(
        MentorRoutingInput(
            requested_capability=None,
            user_message="Can I get one hint?",
            title="House Robber",
            description="Find max sum without adjacent houses.",
            current_hint_level=0,
        ),
        trajectory,
    )

    assert isinstance(runtime.invoker, LiveAdkDecisionInvoker)
    assert decision.selected_capability == "next_hint"
    assert trajectory.runtime_mode == RuntimeMode.ADK_LIVE
    assert trajectory.fallback_used is False
    assert any(event.event_type == "ADK_LIVE_EVENT_RECEIVED" for event in trajectory.events)
    assert any(event.event_type == "ADK_INVOCATION_COMPLETED" for event in trajectory.events)


@pytest.mark.asyncio
async def test_mentor_route_endpoint_returns_trace_aligned_trajectory() -> None:
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
            headers={"x-request-id": "req_adk_route", "x-user-id": "adk-route-user"},
        )

    body = response.json()
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req_adk_route"
    assert body["selected_capability"] == "problem_analysis"
    assert body["selected_skill"] == "problem_intelligence_workflow"
    assert body["result"]["pattern"] == "Dynamic Programming"
    assert body["trajectory"]["request_id"] == "req_adk_route"
    assert body["trajectory"]["trajectory_id"].startswith("traj_")
    assert body["trajectory"]["trace_id"] == response.headers["x-trace-id"]
    assert body["trajectory"]["runtime_mode"] == "adk_disabled"
    assert body["trajectory"]["fallback_used"] is True
    assert body["trajectory"]["selected_capability"] == "problem_analysis"
    assert any(
        event["event_type"] == "ROUTE_SELECTED" for event in body["trajectory"]["events"]
    )
    assert any(
        event["event_type"] == "TOOL_CALL_COMPLETED" for event in body["trajectory"]["events"]
    )

    trajectory_id = body["trajectory"]["trajectory_id"]
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        stored = await client.get(
            f"/api/v1/agent-trajectories/{trajectory_id}",
            headers={"x-user-id": "adk-route-user"},
        )
        policy_decisions = await client.get(
            f"/api/v1/agent-trajectories/{trajectory_id}/policy-decisions",
            headers={"x-user-id": "adk-route-user"},
        )
        cross_user_policy_decisions = await client.get(
            f"/api/v1/agent-trajectories/{trajectory_id}/policy-decisions",
            headers={"x-user-id": "other-user"},
        )

    stored_body = stored.json()
    assert stored.status_code == 200
    assert stored_body["trajectory_id"] == trajectory_id
    assert stored_body["request_id"] == "req_adk_route"
    assert stored_body["trace_id"] == response.headers["x-trace-id"]
    assert stored_body["selected_capability"] == "problem_analysis"
    assert stored_body["selected_skill"] == "problem_intelligence_workflow"
    assert stored_body["event_count"] == len(body["trajectory"]["events"])
    assert any(event["event_type"] == "TOOL_CALL_COMPLETED" for event in stored_body["events"])

    policy_body = policy_decisions.json()
    assert policy_decisions.status_code == 200
    assert len(policy_body) >= 1
    assert policy_body[0]["trajectory_id"] == trajectory_id
    assert policy_body[0]["request_id"] == "req_adk_route"
    assert policy_body[0]["trace_id"] == response.headers["x-trace-id"]
    assert policy_body[0]["tool_id"] == "problem.detect_pattern"
    assert policy_body[0]["caller"] == "adk_narrow_coordinator"
    assert policy_body[0]["decision"] == "allow"
    assert policy_body[0]["policy_id"] == "tool.read.allowed"
    assert policy_body[0]["success"] is True
    assert cross_user_policy_decisions.status_code == 404
