from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import Principal, ensure_same_user, get_principal
from app.db.session import get_session
from app.memory.repository import policy_decisions_for_trajectory, trajectory_for_user
from app.schemas.mentor import (
    AgentTrajectoryResponse,
    AnalyticsResponse,
    CodeReviewRequest,
    CodeReviewResponse,
    HintRequest,
    HintResponse,
    InterviewTurnRequest,
    InterviewTurnResponse,
    MentorRouteRequest,
    MentorRouteResponse,
    PatternTransferResponse,
    PolicyDecisionRecordResponse,
    ProblemInput,
    RecommendationResponse,
    StudyPlanRequest,
    StudyPlanResponse,
    TopicAnalysis,
)
from app.services.mentor_service import mentor_service

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "algoflow"}


@router.post("/mentor/route", response_model=MentorRouteResponse)
async def mentor_route(
    payload: MentorRouteRequest,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(get_principal),
):
    return await mentor_service.route_mentor_request(session, payload, principal.user_id)


@router.get("/agent-trajectories/{trajectory_id}", response_model=AgentTrajectoryResponse)
async def agent_trajectory(
    trajectory_id: str,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(get_principal),
):
    trajectory = await trajectory_for_user(session, principal.user_id, trajectory_id)
    if trajectory is None:
        raise HTTPException(status_code=404, detail="Trajectory not found")
    return AgentTrajectoryResponse(
        trajectory_id=trajectory.id,
        request_id=trajectory.request_id,
        trace_id=trajectory.trace_id,
        session_id=trajectory.session_id,
        task=trajectory.task,
        runtime_mode=trajectory.runtime_mode,
        selected_capability=trajectory.selected_capability,
        selected_skill=trajectory.selected_skill,
        fallback_used=trajectory.fallback_used,
        duration_ms=trajectory.duration_ms,
        schema_version=trajectory.schema_version,
        event_count=trajectory.event_count,
        events=trajectory.events,
        metadata=trajectory.trajectory_metadata,
    )


@router.get(
    "/agent-trajectories/{trajectory_id}/policy-decisions",
    response_model=list[PolicyDecisionRecordResponse],
)
async def agent_trajectory_policy_decisions(
    trajectory_id: str,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(get_principal),
):
    trajectory = await trajectory_for_user(session, principal.user_id, trajectory_id)
    if trajectory is None:
        raise HTTPException(status_code=404, detail="Trajectory not found")
    decisions = await policy_decisions_for_trajectory(session, principal.user_id, trajectory_id)
    return [
        PolicyDecisionRecordResponse(
            id=decision.id,
            request_id=decision.request_id,
            trace_id=decision.trace_id,
            session_id=decision.session_id,
            trajectory_id=decision.trajectory_id,
            tool_id=decision.tool_id,
            caller=decision.caller,
            operation=decision.operation,
            risk=decision.risk,
            decision=decision.decision,
            policy_id=decision.policy_id,
            reason=decision.reason,
            success=decision.success,
            error=decision.error,
            latency_ms=decision.latency_ms,
            metadata=decision.decision_metadata,
        )
        for decision in decisions
    ]


@router.post("/problems/analyze", response_model=TopicAnalysis)
async def analyze_problem(
    payload: ProblemInput,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(get_principal),
):
    return await mentor_service.analyze_problem(session, payload, principal.user_id)


@router.post("/hints/next", response_model=HintResponse)
async def next_hint(
    payload: HintRequest,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(get_principal),
):
    return await mentor_service.next_hint(session, payload, principal.user_id)


@router.post("/code-review", response_model=CodeReviewResponse)
async def code_review(
    payload: CodeReviewRequest,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(get_principal),
):
    return await mentor_service.review_code(session, payload, principal.user_id)


@router.post("/study-plan", response_model=StudyPlanResponse)
async def study_plan(
    payload: StudyPlanRequest,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(get_principal),
):
    return await mentor_service.study_plan(session, payload, principal.user_id)


@router.post("/recommendations", response_model=RecommendationResponse)
async def recommendations(
    payload: ProblemInput,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(get_principal),
):
    return await mentor_service.recommendations(session, payload, principal.user_id)


@router.post("/pattern-transfer", response_model=PatternTransferResponse)
async def pattern_transfer(
    payload: ProblemInput,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(get_principal),
):
    return await mentor_service.pattern_transfer(session, payload, principal.user_id)


@router.get("/analytics/{user_id}", response_model=AnalyticsResponse)
async def analytics(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(get_principal),
):
    ensure_same_user(principal, user_id)
    return await mentor_service.analytics(session, user_id)


@router.post("/mock-interview/turn", response_model=InterviewTurnResponse)
async def interview_turn(
    payload: InterviewTurnRequest,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(get_principal),
):
    return await mentor_service.interview_turn(session, payload, principal.user_id)
