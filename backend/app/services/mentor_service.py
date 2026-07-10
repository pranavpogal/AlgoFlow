from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.core.auth import Principal
from app.core.errors import AlgoFlowError
from app.core.semantic_policy import MentoringMode, SemanticPolicyContext
from app.core.tool_gateway import ToolGatewayError, tool_gateway
from app.memory.repository import (
    learning_events_for_user,
    get_or_create_interview_session,
    record_agent_trajectory,
    record_learning_event,
    record_policy_decision,
    remember_attempt,
    remember_mistakes,
    update_interview_session,
    user_memory_snapshot,
)
from app.memory.learner_state import derive_learner_state
from app.memory.context import MemoryContext, retrieve_memory_context
from app.memory.vector_store import vector_memory
from app.schemas.mentor import (
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
    ProblemInput,
    RecommendationResponse,
    StudyPlanRequest,
    StudyPlanResponse,
    TopicAnalysis,
)
from app.runtime.adk_runtime import CoordinatorToolRequest, MentorRoutingInput, adk_coordinator_runtime
from app.runtime.trajectory import Trajectory, TrajectoryEventType
from app.skills.code_review.workflow import CodeReviewContext, review_code_workflow
from app.skills.mock_interview.workflow import InterviewContext, conduct_interview_turn
from app.skills.pattern_transfer.workflow import PatternTransferContext, generate_pattern_transfer
from app.skills.progressive_hinting.workflow import HintContext, detect_intent, generate_progressive_hint
from app.tools.learning_tools import build_weekly_plan
from app.tools.problem_intelligence import detect_problem_pattern, recommend_related_problems


class MentorService:
    """Application orchestration layer around ADK agents, tools, memory, and persistence."""

    async def route_mentor_request(
        self, session: AsyncSession, payload: MentorRouteRequest, user_id: str
    ) -> MentorRouteResponse:
        trajectory = Trajectory.start("mentor_route", session_id=payload.session_id)
        principal = Principal(user_id=user_id, auth_mode="resolved")
        tool_policy_records = []
        decision = await adk_coordinator_runtime.route(
            MentorRoutingInput(
                requested_capability=payload.requested_capability,
                user_message=payload.user_message,
                title=payload.title,
                description=payload.description,
                current_hint_level=payload.current_hint_level,
                reveal_solution=payload.reveal_solution,
            ),
            trajectory,
        )
        detected_via_gateway = None
        related_via_gateway = None
        related_pattern = None
        code_review_via_gateway = None
        for tool_request in self._tool_requests_for_route(decision):
            trusted_tool_payload = self._trusted_tool_payload_for_route(
                tool_request,
                payload,
                detected_pattern=detected_via_gateway.get("pattern") if detected_via_gateway else None,
            )
            trajectory.add(
                TrajectoryEventType.ADK_TOOL_REQUESTED,
                "Coordinator requested a policy-gated tool.",
                agent_id="algoflow_narrow_coordinator",
                selected_skill=decision.selected_skill,
                tool_name=tool_request.tool_id,
                metadata={
                    "tool_id": tool_request.tool_id,
                    "purpose": tool_request.purpose,
                    "provided_argument_keys": sorted(tool_request.arguments.keys()),
                    "trusted_argument_keys": sorted(trusted_tool_payload.keys()),
                },
            )
            try:
                tool_result, tool_record = tool_gateway.call(
                    tool_request.tool_id,
                    trusted_tool_payload,
                    caller="adk_narrow_coordinator",
                    principal=principal,
                    trajectory=trajectory,
                    semantic_context=self._semantic_context_for_route(
                        payload,
                        decision.selected_capability,
                        principal,
                        trajectory,
                        tool_id=tool_request.tool_id,
                        tool_arguments=trusted_tool_payload,
                    ),
                )
                tool_policy_records.append(tool_record.to_dict())
                if tool_request.tool_id == "problem.detect_pattern":
                    detected_via_gateway = tool_result
                if tool_request.tool_id == "problem.related_problems":
                    related_via_gateway = tool_result
                    related_pattern = trusted_tool_payload.get("pattern")
                if tool_request.tool_id == "code.review_static":
                    code_review_via_gateway = tool_result
            except ToolGatewayError as exc:
                if exc.record is not None:
                    tool_policy_records.append(exc.record.to_dict())
                trajectory.add(
                    TrajectoryEventType.DETERMINISTIC_FALLBACK_USED,
                    "Semantic policy denied gateway tool call; using safe non-tool fallback.",
                    selected_skill=decision.selected_skill,
                    metadata={"error": type(exc).__name__},
                )
        if decision.selected_capability == "study_plan":
            result_model = await self.study_plan(
                session,
                self._study_plan_request_from_route(payload),
                user_id,
                source_route="mentor.route",
            )
        elif decision.selected_capability == "code_review":
            if code_review_via_gateway:
                result_model = CodeReviewResponse.model_validate(code_review_via_gateway)
                await self._persist_code_review_response(
                    session,
                    self._code_review_request_from_route(payload),
                    user_id,
                    result_model,
                    source_route="mentor.route",
                )
            else:
                result_model = self._safe_policy_denied_code_review()
        elif decision.selected_capability == "pattern_transfer":
            if related_via_gateway:
                result_model = self._pattern_transfer_response_from_related(
                    pattern=str(related_pattern or "Unknown"),
                    related=related_via_gateway,
                )
            else:
                result_model = self._safe_policy_denied_pattern_transfer()
        elif decision.selected_capability == "recommendations":
            if related_via_gateway:
                result_model = self._recommendation_response_from_related(
                    pattern=str(related_pattern or "Unknown"),
                    related=related_via_gateway,
                )
            else:
                result_model = self._safe_policy_denied_recommendations()
        elif decision.selected_capability == "next_hint":
            if detected_via_gateway:
                result_model = await self.next_hint(
                    session,
                    HintRequest(
                        user_id=payload.user_id,
                        problem_number=payload.problem_number,
                        title=payload.title,
                        url=payload.url,
                        description=payload.description,
                        current_hint_level=payload.current_hint_level or 0,
                        user_attempt=payload.user_attempt or payload.user_message,
                        reveal_solution=payload.reveal_solution,
                    ),
                    user_id,
                )
            else:
                result_model = self._safe_policy_denied_hint(payload)
        else:
            if detected_via_gateway:
                result_model = self._topic_analysis_from_detected(payload, detected_via_gateway)
                await self._persist_problem_analysis(session, payload, user_id, result_model)
            else:
                result_model = self._safe_policy_denied_analysis(payload)
        await self._apply_route_memory_context(
            session,
            user_id=user_id,
            payload=payload,
            selected_capability=decision.selected_capability,
            result_model=result_model,
        )
        trajectory.add(
            TrajectoryEventType.WORKFLOW_EXECUTED,
            "Selected deterministic workflow executed successfully.",
            selected_skill=decision.selected_skill,
            metadata={"selected_capability": decision.selected_capability},
        )
        trajectory.add(
            TrajectoryEventType.RESPONSE_VALIDATED,
            "Response serialized through the route response contract.",
            selected_skill=decision.selected_skill,
        )
        trajectory.finish()
        trajectory_payload = trajectory.to_dict()
        await record_agent_trajectory(
            session,
            user_id,
            trajectory_payload,
            selected_skill=decision.selected_skill,
            metadata={
                "source_route": "mentor.route",
                "selected_capability": decision.selected_capability,
            },
        )
        for tool_policy_record in tool_policy_records:
            await record_policy_decision(
                session,
                user_id=user_id,
                tool_call=tool_policy_record,
                trajectory=trajectory_payload,
                metadata={"source_route": "mentor.route"},
            )
        return MentorRouteResponse(
            selected_capability=decision.selected_capability,
            selected_skill=decision.selected_skill,
            result=result_model.model_dump(),
            trajectory=trajectory_payload,
        )

    def _semantic_context_for_route(
        self,
        payload: MentorRouteRequest,
        selected_capability: str,
        principal: Principal,
        trajectory: Trajectory,
        *,
        tool_id: str = "problem.detect_pattern",
        tool_arguments: dict[str, Any] | None = None,
    ) -> SemanticPolicyContext:
        hint_intent = detect_intent(payload.user_attempt or payload.user_message, payload.reveal_solution)
        if selected_capability == "code_review":
            user_intent = "CODE_REVIEW"
            mentoring_mode = MentoringMode.CODE_REVIEW.value
        elif selected_capability == "pattern_transfer":
            user_intent = "RECOMMEND_TRANSFER"
            mentoring_mode = MentoringMode.RECOMMEND_TRANSFER.value
        elif selected_capability == "recommendations":
            user_intent = "RECOMMENDATION"
            mentoring_mode = MentoringMode.RECOMMEND_TRANSFER.value
        elif selected_capability == "next_hint":
            user_intent = hint_intent.value
            if hint_intent.value == "FULL_SOLUTION" and payload.reveal_solution:
                mentoring_mode = MentoringMode.EXPLICIT_SOLUTION.value
            elif hint_intent.value in {"IDEA_VALIDATION", "APPROACH_REVIEW", "WHY_STATE_WRONG"}:
                mentoring_mode = MentoringMode.VALIDATE_APPROACH.value
            else:
                mentoring_mode = MentoringMode.HINT_ONLY.value
        else:
            user_intent = "PROBLEM_ANALYSIS"
            mentoring_mode = MentoringMode.EXPLAIN_CONCEPT.value
        arguments = tool_arguments or {"title": payload.title, "description": payload.description}
        return SemanticPolicyContext(
            principal_id=principal.user_id,
            request_id=trajectory.request_id,
            trace_id=trajectory.trace_id,
            session_id=trajectory.session_id,
            trajectory_id=trajectory.trajectory_id,
            caller_id="adk_narrow_coordinator",
            selected_capability=selected_capability,
            user_intent=user_intent,
            mentoring_mode=mentoring_mode,
            requested_tool_id=tool_id,
            operation_type="draft" if tool_id in {"problem.related_problems", "code.review_static"} else "read",
            tool_arguments=arguments,
            prior_hint_context={"current_hint_level": payload.current_hint_level},
            task_context={
                "title": payload.title,
                "description": payload.description,
                "user_message": payload.user_message or payload.user_attempt or "",
            },
            trusted_context={"runtime": "mentor.route", "policy_context_source": "server"},
            untrusted_user_content_present=True,
            reveal_authorized=bool(payload.reveal_solution and hint_intent.value == "FULL_SOLUTION"),
        )

    def _tool_requests_for_route(self, decision: Any) -> list[CoordinatorToolRequest]:
        if decision.tool_requests:
            return decision.tool_requests
        if decision.selected_capability in {"problem_analysis", "next_hint"}:
            return [
                CoordinatorToolRequest(
                    tool_id="problem.detect_pattern",
                    purpose="Default policy-gated pattern detection required by the selected workflow.",
                    arguments={},
                )
            ]
        return []

    def _trusted_tool_payload_for_route(
        self,
        tool_request: CoordinatorToolRequest,
        payload: MentorRouteRequest,
        *,
        detected_pattern: str | None,
    ) -> dict[str, Any]:
        if tool_request.tool_id == "problem.detect_pattern":
            return {"title": payload.title, "description": payload.description}
        if tool_request.tool_id == "problem.related_problems":
            requested_pattern = tool_request.arguments.get("pattern")
            pattern = detected_pattern or (requested_pattern if isinstance(requested_pattern, str) else None)
            return {"pattern": pattern or "Unknown"}
        if tool_request.tool_id == "code.review_static":
            return {
                "title": payload.title,
                "language": payload.language or "unknown",
                "code": payload.code or "",
                "problem_description": payload.problem_description or payload.description,
                "user_intent": payload.user_message or payload.user_attempt,
            }
        return {}

    def _recommendation_response_from_related(
        self, *, pattern: str, related: list[dict[str, Any]]
    ) -> RecommendationResponse:
        return RecommendationResponse(
            core_pattern=pattern,
            related_problems=related,
            difficulty_progression=[str(item.get("difficulty", "Unknown")) for item in related],
            explanation=(
                "Recommendations were produced through the governed ADK route using the "
                "policy-gated related-problems tool. They are practice suggestions, not mastery evidence."
            ),
            recommendations=[],
            learner_state_confidence="unknown",
            fallback_reason=None,
            same_topic_shortcut_used=False,
        )

    def _safe_policy_denied_recommendations(self) -> RecommendationResponse:
        return RecommendationResponse(
            core_pattern="Unknown",
            related_problems=[],
            difficulty_progression=[],
            explanation=(
                "A governed recommendation requires an approved related-problems tool request. "
                "No raw recommendation fallback was used."
            ),
            recommendations=[],
            learner_state_confidence="unknown",
            fallback_reason="policy_gated_tool_unavailable",
            same_topic_shortcut_used=False,
        )

    def _pattern_transfer_response_from_related(
        self, *, pattern: str, related: list[dict[str, Any]]
    ) -> PatternTransferResponse:
        transfer_items = [
            {
                "problem_number": item.get("number"),
                "title": item.get("title"),
                "difficulty": item.get("difficulty", "Unknown"),
                "variation": item.get("why", "Practice the same structural pattern in a new setting."),
                "transfer_bridge": item.get(
                    "why", "Map the learned decision structure before looking for implementation details."
                ),
            }
            for item in related
        ]
        return PatternTransferResponse(
            core_idea=f"Transfer the {pattern} structure to nearby variations before memorizing solutions.",
            transfer_to=transfer_items,
            pattern_evolution=[
                str(item.get("why", "Apply the same pattern under a slightly different constraint."))
                for item in related
            ],
            learning_opportunities=[
                "Compare the state, invariant, or traversal choice before writing code.",
                "Explain what stays the same and what changes across the recommended problems.",
            ],
            source_pattern=pattern,
            learner_state_confidence="unknown",
            recommendations=[],
            transfer_taxonomy={"source_pattern": pattern},
            evidence_hierarchy=[
                {
                    "source": "policy_gated_tool",
                    "tool_id": "problem.related_problems",
                    "claim": "Related practice candidates were returned by a governed deterministic tool.",
                }
            ],
            fallback_reason=None,
            same_topic_shortcut_used=False,
        )

    def _safe_policy_denied_pattern_transfer(self) -> PatternTransferResponse:
        return PatternTransferResponse(
            core_idea=(
                "Governed pattern transfer requires an approved related-problems tool request. "
                "No raw pattern-transfer fallback was used."
            ),
            transfer_to=[],
            pattern_evolution=[],
            learning_opportunities=[],
            source_pattern="Unknown",
            learner_state_confidence="unknown",
            recommendations=[],
            transfer_taxonomy={},
            evidence_hierarchy=[],
            fallback_reason="policy_gated_tool_unavailable",
            same_topic_shortcut_used=False,
        )

    def _safe_policy_denied_code_review(self) -> CodeReviewResponse:
        return CodeReviewResponse(
            correctness="A governed code review requires an approved static-review tool request.",
            time_complexity="Unknown",
            space_complexity="Unknown",
            edge_cases=[],
            optimization_opportunities=[],
            readability_feedback=[
                "No raw code-review fallback was used because the policy-gated tool was unavailable."
            ],
            alternative_approaches=[],
            suspected_mistakes=[],
            senior_engineer_summary=(
                "I did not review the code because the governed route did not receive an approved "
                "code.review_static tool request."
            ),
            review_intent="CODE_REVIEW",
            language_supported=False,
            analysis_layers=["policy_gated_tool_unavailable"],
            findings=[],
            corrected_code=None,
            rewrite_allowed=False,
            unsupported_claims=["No code analysis was performed."],
        )

    def _safe_policy_denied_hint(self, payload: MentorRouteRequest) -> HintResponse:
        return HintResponse(
            level=min((payload.current_hint_level or 0) + 1, 4),
            hint="I can still help safely: restate the subproblem or invariant you think applies, and I will validate that direction without escalating tool use.",
            reveals_solution=False,
            mentor_note="A tool call was blocked by policy, so I am keeping this response bounded and non-spoiling.",
        )

    async def _apply_route_memory_context(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        payload: MentorRouteRequest,
        selected_capability: str,
        result_model: Any,
    ) -> None:
        existing_context = getattr(result_model, "memory_context", None)
        if isinstance(existing_context, dict) and existing_context.get("purpose"):
            return
        if not hasattr(result_model, "memory_context"):
            return
        purpose_by_capability = {
            "code_review": "mentor_route_code_review_personalization",
            "recommendations": "mentor_route_recommendation_personalization",
            "pattern_transfer": "mentor_route_pattern_transfer_personalization",
        }
        purpose = purpose_by_capability.get(selected_capability)
        if not purpose:
            return
        memory_context = await retrieve_memory_context(
            session,
            user_id=user_id,
            query=f"{payload.title} {payload.description} {payload.user_message or payload.user_attempt or ''}",
            purpose=purpose,
            problem_title=payload.title,
            concept=selected_capability,
        )
        result_model.memory_context = self._memory_context_payload(memory_context)
        if not memory_context.applied:
            return
        if isinstance(result_model, CodeReviewResponse):
            result_model.readability_feedback.append(
                "Route personalization note: retrieved memory was considered while framing this governed review."
            )
            result_model.unsupported_claims = self._with_memory_limitations(
                result_model.unsupported_claims, memory_context
            )
        elif isinstance(result_model, RecommendationResponse):
            result_model.explanation = self._with_memory_note(result_model.explanation, memory_context)
        elif isinstance(result_model, PatternTransferResponse):
            result_model.evidence_hierarchy.append(
                {
                    "source": "retrieved_memory",
                    "claim": "Prior memory was used as advisory personalization context.",
                    "provenance": memory_context.provenance(),
                }
            )

    def _safe_policy_denied_analysis(self, payload: MentorRouteRequest) -> TopicAnalysis:
        return TopicAnalysis(
            problem=payload.title,
            difficulty="Unknown",
            pattern="Unknown",
            sub_patterns=[],
            prerequisites=[],
            reasoning="A gateway policy check blocked automated pattern analysis, so no raw tool fallback was used.",
            confidence=0.0,
            provenance=["mentor_service.safe_policy_denied_analysis"],
            unsupported_claims=[],
        )

    async def analyze_problem(
        self, session: AsyncSession, payload: ProblemInput, user_id: str
    ) -> TopicAnalysis:
        detected = detect_problem_pattern(
            payload.title,
            payload.description,
            payload.problem_number,
            use_canonical_title_catalog=True,
        )
        analysis = self._topic_analysis_from_detected(payload, detected)
        await self._persist_problem_analysis(session, payload, user_id, analysis)
        return analysis

    def _topic_analysis_from_detected(
        self, payload: ProblemInput, detected: dict
    ) -> TopicAnalysis:
        analysis = TopicAnalysis(
            problem=payload.title,
            difficulty=detected.get("difficulty", "Unknown"),
            pattern=detected["pattern"],
            sub_patterns=detected["sub_patterns"],
            prerequisites=detected["prerequisites"],
            reasoning=detected["reasoning"],
            primary_topic=detected.get("primary_topic"),
            secondary_topics=detected.get("secondary_topics", []),
            primary_pattern=detected.get("primary_pattern"),
            structural_cues=detected.get("structural_cues", []),
            related_patterns=detected.get("related_patterns", []),
            difficulty_signals=detected.get("difficulty_signals", []),
            confidence=detected.get("confidence"),
            evidence=detected.get("evidence", []),
            provenance=detected.get("provenance", []),
            unsupported_claims=detected.get("unsupported_claims", []),
            taxonomy_version=detected.get("taxonomy_version"),
        )
        return analysis

    async def _persist_problem_analysis(
        self, session: AsyncSession, payload: ProblemInput, user_id: str, analysis: TopicAnalysis
    ) -> None:
        await remember_attempt(
            session,
            user_id,
            title=payload.title,
            pattern=analysis.pattern,
            difficulty=analysis.difficulty,
        )
        await record_learning_event(
            session,
            user_id,
            "ProblemClassified",
            problem_title=payload.title,
            concept=analysis.pattern,
            evidence={
                "problem_number": payload.problem_number,
                "difficulty": analysis.difficulty,
                "sub_patterns": analysis.sub_patterns,
                "prerequisites": analysis.prerequisites,
                "primary_topic": analysis.primary_topic,
                "primary_pattern": analysis.primary_pattern,
                "secondary_topics": analysis.secondary_topics,
                "confidence": analysis.confidence,
                "provenance": analysis.provenance,
                "taxonomy_version": analysis.taxonomy_version,
                "classification_only": True,
                "mastery_evidence": False,
            },
            metadata={"source_route": "problems.analyze"},
        )
        if analysis.primary_pattern and (analysis.confidence or 0) >= 0.7:
            await record_learning_event(
                session,
                user_id,
                "PatternDetected",
                problem_title=payload.title,
                concept=analysis.primary_pattern,
                evidence={
                    "primary_topic": analysis.primary_topic,
                    "confidence": analysis.confidence,
                    "provenance": analysis.provenance,
                    "mastery_evidence": False,
                },
                metadata={"source_route": "problems.analyze"},
            )
        for cue in analysis.structural_cues[:3]:
            await record_learning_event(
                session,
                user_id,
                "StructuralCueDetected",
                problem_title=payload.title,
                concept=cue,
                evidence={
                    "primary_pattern": analysis.primary_pattern,
                    "confidence": analysis.confidence,
                    "mastery_evidence": False,
                },
                metadata={"source_route": "problems.analyze"},
            )
        vector_memory.add(
            user_id,
            f"Analyzed {payload.title}: {analysis.pattern}, {analysis.primary_pattern}, confidence={analysis.confidence}",
            {
                "type": "topic_analysis",
                "problem": payload.title,
                "pattern": analysis.pattern,
                "primary_pattern": analysis.primary_pattern,
            },
        )

    async def next_hint(self, session: AsyncSession, payload: HintRequest, user_id: str) -> HintResponse:
        memory = await user_memory_snapshot(session, user_id)
        learner_state = derive_learner_state(memory)
        detected = detect_problem_pattern(payload.title, payload.description)
        pattern = detected["pattern"]
        memory_context = await retrieve_memory_context(
            session,
            user_id=user_id,
            query=f"{payload.title} {pattern} {payload.user_attempt or ''}",
            purpose="hint_personalization",
            problem_title=payload.title,
            concept=pattern,
        )
        learner_state["retrieved_memory"] = memory_context.snippets()
        previous_hints = [
            event
            for event in await learning_events_for_user(session, user_id, event_type="HintDelivered", limit=10)
            if event.problem_title == payload.title
        ]
        await record_learning_event(
            session,
            user_id,
            "HintRequested",
            problem_title=payload.title,
            concept=pattern,
            evidence={
                "current_hint_level": payload.current_hint_level,
                "had_user_attempt": bool(payload.user_attempt),
                "requested_reveal": payload.reveal_solution,
                "previous_hint_count": len(previous_hints),
            },
            metadata={"source_route": "hints.next"},
        )
        hint_result = generate_progressive_hint(
            HintContext(
                title=payload.title,
                description=payload.description,
                pattern=pattern,
                difficulty=detected.get("difficulty", "Unknown"),
                current_hint_level=payload.current_hint_level,
                user_attempt=payload.user_attempt,
                reveal_solution=payload.reveal_solution,
                learner_state=learner_state,
                previous_hint_events=previous_hints,
            )
        )
        response = HintResponse(
            level=hint_result.hint_level,
            hint=hint_result.hint,
            reveals_solution=hint_result.reveals_solution,
            mentor_note=self._with_memory_note(hint_result.mentor_note, memory_context),
            memory_context=self._memory_context_payload(memory_context),
        )
        await record_learning_event(
            session,
            user_id,
            "HintDelivered",
            problem_title=payload.title,
            concept=pattern,
            evidence={
                "level": response.level,
                "intervention_type": hint_result.intervention_type.value,
                "intent": hint_result.intent.value,
                "reveals_solution": response.reveals_solution,
                "had_user_attempt": bool(payload.user_attempt),
                "requested_reveal": payload.reveal_solution,
                "learner_state_confidence": hint_result.learner_state_confidence,
                "detected_misconception": hint_result.detected_misconception,
                "uses_previous_hint_context": hint_result.uses_previous_hint_context,
                "solution_leakage_risk": hint_result.solution_leakage_risk,
                "next_escalation_condition": hint_result.next_escalation_condition,
                "memory_context_applied": memory_context.applied,
                "memory_provenance": memory_context.provenance(),
            },
            metadata={"source_route": "hints.next"},
        )
        if hint_result.repeated_hint:
            await record_learning_event(
                session,
                user_id,
                "HintEscalated",
                problem_title=payload.title,
                concept=pattern,
                evidence={
                    "intervention_type": hint_result.intervention_type.value,
                    "reason": "avoided_repeating_previous_hint",
                },
                metadata={"source_route": "hints.next"},
            )
        if hint_result.detected_misconception:
            await record_learning_event(
                session,
                user_id,
                "MisconceptionAddressed",
                problem_title=payload.title,
                concept=hint_result.detected_misconception,
                evidence={
                    "intervention_type": hint_result.intervention_type.value,
                    "pattern": pattern,
                },
                metadata={"source_route": "hints.next"},
            )
        return response

    async def review_code(
        self, session: AsyncSession, payload: CodeReviewRequest, user_id: str
    ) -> CodeReviewResponse:
        memory = await user_memory_snapshot(session, user_id)
        learner_state = derive_learner_state(memory)
        memory_context = await retrieve_memory_context(
            session,
            user_id=user_id,
            query=f"{payload.title} {payload.language} {payload.user_intent or ''} {payload.problem_description or ''}",
            purpose="code_review_personalization",
            problem_title=payload.title,
            concept="code_review",
        )
        learner_state["retrieved_memory"] = memory_context.snippets()
        await record_learning_event(
            session,
            user_id,
            "CodeReviewRequested",
            problem_title=payload.title,
            evidence={
                "language": payload.language,
                "code_length": len(payload.code),
                "has_problem_description": bool(payload.problem_description),
                "has_user_intent": bool(payload.user_intent),
            },
            metadata={"source_route": "code-review"},
        )
        review_result = review_code_workflow(
            CodeReviewContext(
                title=payload.title,
                language=payload.language,
                code=payload.code,
                problem_description=payload.problem_description,
                user_intent=payload.user_intent,
                learner_state=learner_state,
            )
        )
        response = CodeReviewResponse(
            correctness=review_result.correctness,
            time_complexity=review_result.time_complexity,
            space_complexity=review_result.space_complexity,
            edge_cases=review_result.edge_cases,
            optimization_opportunities=review_result.optimization_opportunities,
            readability_feedback=review_result.readability_feedback,
            alternative_approaches=review_result.alternative_approaches,
            suspected_mistakes=review_result.suspected_mistakes,
            senior_engineer_summary=review_result.senior_engineer_summary,
            review_intent=review_result.intent.value,
            language_supported=review_result.language_supported,
            analysis_layers=review_result.analysis_layers,
            findings=[finding.to_dict() for finding in review_result.findings],
            corrected_code=review_result.corrected_code,
            rewrite_allowed=review_result.rewrite_allowed,
            unsupported_claims=self._with_memory_limitations(review_result.unsupported_claims, memory_context),
            memory_context=self._memory_context_payload(memory_context),
        )
        if memory_context.applied:
            response.readability_feedback.append(
                "Personalization note: I considered a small set of your prior memory snippets while framing this review."
            )
        await self._persist_code_review_response(
            session,
            payload,
            user_id,
            response,
            source_route="code-review",
        )
        return response

    async def _persist_code_review_response(
        self,
        session: AsyncSession,
        payload: CodeReviewRequest,
        user_id: str,
        response: CodeReviewResponse,
        *,
        source_route: str,
    ) -> None:
        await remember_attempt(
            session,
            user_id,
            title=payload.title,
            language=payload.language,
            code=payload.code,
            review=response.model_dump(),
        )
        await remember_mistakes(session, user_id, response.suspected_mistakes)
        await record_learning_event(
            session,
            user_id,
            "CodeSubmitted",
            problem_title=payload.title,
            evidence={
                "language": payload.language,
                "code_length": len(payload.code),
                "has_problem_description": bool(payload.problem_description),
            },
            metadata={"source_route": source_route},
        )
        await record_learning_event(
            session,
            user_id,
            "ReviewDelivered",
            problem_title=payload.title,
            evidence={
                "language": payload.language,
                "correctness": response.correctness,
                "time_complexity": response.time_complexity,
                "space_complexity": response.space_complexity,
                "suspected_mistakes": response.suspected_mistakes,
                "review_intent": response.review_intent,
                "analysis_layers": response.analysis_layers,
                "finding_count": len(response.findings),
            },
            metadata={"source_route": source_route},
        )
        await record_learning_event(
            session,
            user_id,
            "CodeReviewCompleted",
            problem_title=payload.title,
            evidence={
                "language": payload.language,
                "review_intent": response.review_intent,
                "finding_count": len(response.findings),
                "high_confidence_findings": sum(1 for finding in response.findings if finding.confidence >= 0.75),
                "language_supported": response.language_supported,
                "rewrite_allowed": response.rewrite_allowed,
                "unsupported_claims": response.unsupported_claims,
            },
            metadata={"source_route": source_route},
        )
        for finding in response.findings:
            await record_learning_event(
                session,
                user_id,
                "CodeFindingProduced",
                problem_title=payload.title,
                concept=finding.category,
                evidence={
                    "finding_id": finding.finding_id,
                    "category": finding.category,
                    "severity": finding.severity,
                    "confidence": finding.confidence,
                    "evidence_type": finding.evidence_type,
                    "location": finding.location.model_dump(),
                    "provenance": finding.provenance,
                },
                metadata={"source_route": source_route},
            )
            if finding.severity in {"medium", "high"} and finding.confidence >= 0.7:
                await record_learning_event(
                    session,
                    user_id,
                    "MisconceptionDetected",
                    problem_title=payload.title,
                    concept=finding.category,
                    evidence={
                        "category": finding.category,
                        "finding_id": finding.finding_id,
                        "confidence": finding.confidence,
                        "provenance": finding.provenance,
                    },
                    metadata={"source_route": source_route},
                )
        vector_memory.add(
            user_id,
            f"Code review for {payload.title}: mistakes={response.suspected_mistakes}",
            {"type": "code_review", "problem": payload.title},
        )

    def _code_review_request_from_route(self, payload: MentorRouteRequest) -> CodeReviewRequest:
        return CodeReviewRequest(
            user_id=payload.user_id,
            title=payload.title,
            language=payload.language or "unknown",
            code=payload.code or "",
            problem_description=payload.problem_description or payload.description,
            user_intent=payload.user_message or payload.user_attempt,
        )

    def _study_plan_request_from_route(self, payload: MentorRouteRequest) -> StudyPlanRequest:
        return StudyPlanRequest(
            user_id=payload.user_id,
            target_company=payload.target_company or "Google",
            days_remaining=payload.days_remaining if payload.days_remaining is not None else 45,
            hours_per_week=payload.hours_per_week if payload.hours_per_week is not None else 8,
        )

    async def study_plan(
        self,
        session: AsyncSession,
        payload: StudyPlanRequest,
        user_id: str,
        *,
        source_route: str = "study-plan",
    ) -> StudyPlanResponse:
        memory = await user_memory_snapshot(session, user_id)
        memory["derived_learner_state"] = derive_learner_state(memory)
        memory_context = await retrieve_memory_context(
            session,
            user_id=user_id,
            query=f"{payload.target_company} study plan {payload.days_remaining} days {payload.hours_per_week} hours",
            purpose="study_plan_personalization",
            problem_title="Study Plan",
            concept=payload.target_company,
        )
        plan = build_weekly_plan(memory, payload.days_remaining, payload.hours_per_week)
        response = StudyPlanResponse(
            target_company=payload.target_company,
            days_remaining=payload.days_remaining,
            weekly_plan=plan,
            checkpoints=[
                "Weekly timed mock with communication scoring",
                "Mistake review every 10 solved problems",
                "Pattern transfer drill after every DP/graph problem",
            ],
            personalization_notes=[
                "Schedule emphasizes current weak topics from memory.",
                "Each week includes review loops so solved problems turn into durable skill.",
                *self._memory_notes(memory_context),
            ],
            memory_context=self._memory_context_payload(memory_context),
        )
        await record_learning_event(
            session,
            user_id,
            "StudyPlanGenerated",
            evidence={
                "target_company": payload.target_company,
                "days_remaining": payload.days_remaining,
                "hours_per_week": payload.hours_per_week,
                "weeks": len(response.weekly_plan),
                "memory_context_applied": memory_context.applied,
                "memory_provenance": memory_context.provenance(),
            },
            metadata={"source_route": source_route},
        )
        return response

    async def recommendations(
        self, session: AsyncSession, payload: ProblemInput, user_id: str
    ) -> RecommendationResponse:
        detected = detect_problem_pattern(payload.title, payload.description)
        memory_context = await retrieve_memory_context(
            session,
            user_id=user_id,
            query=f"{payload.title} {detected['pattern']} recommendations related practice",
            purpose="recommendation_personalization",
            problem_title=payload.title,
            concept=detected["pattern"],
        )
        transfer = await self._pattern_transfer_result(session, payload, user_id)
        related = [
            {
                "number": item.target_problem_id,
                "title": item.target_title,
                "difficulty": item.target_difficulty,
                "variation": item.recommendation_type.value,
                "confidence": item.recommendation_confidence,
                "why": item.transfer_bridge,
            }
            for item in transfer.recommendations
        ] or recommend_related_problems(detected["pattern"])
        return RecommendationResponse(
            core_pattern=detected.get("primary_pattern") or detected["pattern"],
            related_problems=related,
            difficulty_progression=[item["difficulty"] for item in related],
            explanation=(
                "Recommendations are selected by structural transfer evidence, learner-state confidence, "
                "bounded corpus relationships, and retrieved memory when available; they are not mastery claims."
            ),
            recommendations=[item.to_dict() for item in transfer.recommendations],
            learner_state_confidence=transfer.learner_state_confidence_bucket,
            fallback_reason=transfer.fallback_reason,
            same_topic_shortcut_used=transfer.same_topic_shortcut_used,
            memory_context=self._memory_context_payload(memory_context),
        )

    async def pattern_transfer(
        self, session: AsyncSession, payload: ProblemInput, user_id: str
    ) -> PatternTransferResponse:
        transfer = await self._pattern_transfer_result(session, payload, user_id)
        memory_context = await retrieve_memory_context(
            session,
            user_id=user_id,
            query=f"{payload.title} {transfer.source_pattern} pattern transfer",
            purpose="pattern_transfer_personalization",
            problem_title=payload.title,
            concept=transfer.source_pattern,
        )
        related = [
            {
                "number": item.target_problem_id,
                "title": item.target_title,
                "difficulty": item.target_difficulty,
                "variation": item.recommendation_type.value,
                "confidence": item.recommendation_confidence,
                "why": item.transfer_bridge,
            }
            for item in transfer.recommendations
        ]
        return PatternTransferResponse(
            core_idea="Transfer the structural invariant, not the surface topic label.",
            transfer_to=related,
            pattern_evolution=[item.transfer_bridge for item in transfer.recommendations],
            learning_opportunities=[
                item.expected_learning_goal for item in transfer.recommendations
            ],
            source_problem_id=transfer.source_problem_id,
            source_pattern=transfer.source_pattern,
            classification_confidence=transfer.classification_confidence,
            learner_state_confidence=transfer.learner_state_confidence_bucket,
            recommendations=[item.to_dict() for item in transfer.recommendations],
            transfer_taxonomy={key.value: value for key, value in transfer.transfer_taxonomy.items()},
            evidence_hierarchy=transfer.evidence_hierarchy,
            fallback_reason=transfer.fallback_reason,
            same_topic_shortcut_used=transfer.same_topic_shortcut_used,
            memory_context=self._memory_context_payload(memory_context),
        )

    async def _pattern_transfer_result(
        self, session: AsyncSession, payload: ProblemInput, user_id: str
    ):
        memory = await user_memory_snapshot(session, user_id)
        learner_state = derive_learner_state(memory)
        previous_events = await learning_events_for_user(
            session, user_id, event_type="PatternTransferRecommended", limit=20
        )
        await record_learning_event(
            session,
            user_id,
            "PatternTransferRequested",
            problem_title=payload.title,
            evidence={
                "has_description": bool(payload.description),
                "problem_number": payload.problem_number,
                "mastery_evidence": False,
            },
            metadata={"source_route": "pattern-transfer"},
        )
        transfer = generate_pattern_transfer(
            PatternTransferContext(
                title=payload.title,
                description=payload.description,
                learner_state=learner_state,
                memory=memory,
                previous_transfer_events=previous_events,
            )
        )
        for recommendation in transfer.recommendations:
            await record_learning_event(
                session,
                user_id,
                "PatternTransferRecommended",
                problem_title=payload.title,
                concept=recommendation.recommendation_type.value,
                evidence={
                    "target_problem_id": recommendation.target_problem_id,
                    "target_title": recommendation.target_title,
                    "source_pattern": recommendation.source_pattern,
                    "target_pattern": recommendation.target_pattern,
                    "relationship_confidence": recommendation.relationship_confidence,
                    "recommendation_confidence": recommendation.recommendation_confidence,
                    "mastery_evidence": False,
                },
                metadata={"source_route": "pattern-transfer"},
            )
        return transfer

    async def analytics(self, session: AsyncSession, user_id: str) -> AnalyticsResponse:
        memory = await user_memory_snapshot(session, user_id)
        learner_state = derive_learner_state(memory)
        response = AnalyticsResponse(
            readiness_score=learner_state["readiness_score"],
            readiness_components=learner_state["readiness_components"],
            confidence=learner_state["confidence"],
            evidence_count=learner_state["evidence_count"],
            strongest_topics=learner_state["strong_topics"],
            weakest_topics=learner_state["weak_topics"],
            common_mistakes=learner_state["common_mistakes"],
            mistake_trends=learner_state["mistake_trends"],
            topic_mastery=learner_state["topic_mastery"],
            topic_risk=learner_state["topic_risk"],
            learning_velocity=learner_state["learning_velocity"],
            interview_readiness=learner_state["interview_readiness"],
            next_best_actions=learner_state["next_best_actions"],
            recommendations=learner_state["recommendations"],
            evidence_summary=learner_state["evidence_summary"],
            limitations=learner_state["limitations"],
        )
        await record_learning_event(
            session,
            user_id,
            "AnalyticsViewed",
            evidence={
                "readiness_score": response.readiness_score,
                "readiness_components": response.readiness_components,
                "attempt_count": memory.get("attempt_count", 0),
                "learning_event_count": memory.get("learning_event_count", 0),
                "confidence": response.confidence,
            },
            metadata={"source_route": "analytics"},
        )
        return response

    async def interview_turn(
        self, session: AsyncSession, payload: InterviewTurnRequest, user_id: str
    ) -> InterviewTurnResponse:
        session_id = payload.session_id or str(uuid4())
        memory_context = await retrieve_memory_context(
            session,
            user_id=user_id,
            query=f"{payload.problem_title or ''} {payload.persona} interview {payload.message}",
            purpose="mock_interview_personalization",
            problem_title=payload.problem_title,
            concept=payload.persona,
        )
        try:
            interview = await get_or_create_interview_session(
                session,
                user_id,
                session_id=session_id,
                persona=payload.persona,
                problem_title=payload.problem_title,
            )
        except PermissionError as exc:
            raise AlgoFlowError(
                code="FORBIDDEN",
                message="You are not allowed to access this interview session.",
                status_code=status.HTTP_403_FORBIDDEN,
                details={"resource": "interview_session"},
            ) from exc
        interview_result = conduct_interview_turn(
            InterviewContext(
                session_id=session_id,
                persona=payload.persona,
                problem_title=payload.problem_title or interview.problem_title,
                message=payload.message,
                transcript=interview.transcript or [],
                scorecard=interview.scorecard or {},
                memory_snippets=memory_context.snippets(),
            )
        )
        await update_interview_session(
            session,
            interview,
            transcript_entries=interview_result.transcript_entries,
            scorecard=interview_result.scorecard,
            persona=payload.persona,
            problem_title=payload.problem_title,
        )
        response = InterviewTurnResponse(
            session_id=session_id,
            interviewer_message=self._with_memory_note(interview_result.interviewer_message, memory_context),
            follow_up_focus=interview_result.follow_up_focus,
            score_delta=interview_result.score_delta,
            feedback=[
                *interview_result.feedback,
                *self._memory_notes(memory_context),
            ],
            memory_context=self._memory_context_payload(memory_context),
            stage=interview_result.stage,
            turn_index=interview_result.turn_index,
            rubric_scores=interview_result.rubric_scores,
            scorecard=interview_result.scorecard,
            evaluation_summary=interview_result.evaluation_summary,
            persona_style=interview_result.persona_style,
        )
        await record_learning_event(
            session,
            user_id,
            "InterviewAnswerSubmitted",
            problem_title=payload.problem_title,
            evidence={
                "session_id": session_id,
                "persona": payload.persona,
                "message_length": len(payload.message),
                "follow_up_focus": response.follow_up_focus,
                "score_delta": response.score_delta,
                "stage": response.stage,
                "turn_index": response.turn_index,
                "rubric_scores": response.rubric_scores,
                "scorecard_total": response.scorecard.get("total_score"),
                "memory_context_applied": memory_context.applied,
                "memory_provenance": memory_context.provenance(),
            },
            metadata={"source_route": "mock-interview.turn"},
        )
        return response

    def _memory_context_payload(self, memory_context: MemoryContext) -> dict[str, Any]:
        return {
            "applied": memory_context.applied,
            "purpose": memory_context.purpose,
            "retrieved_count": len(memory_context.retrieved),
            "snippets": memory_context.snippets(),
            "provenance": memory_context.provenance(),
            "policy": {
                "decision": memory_context.policy_decision.decision,
                "policy_id": memory_context.policy_decision.policy_id,
                "reason": memory_context.policy_decision.reason,
                "constraints": memory_context.policy_decision.constraints,
            },
            "limitations": memory_context.limitations,
        }

    def _with_memory_note(self, text: str, memory_context: MemoryContext) -> str:
        if not memory_context.applied:
            return text
        return (
            f"{text} I also found relevant prior memory, so I am biasing this guidance toward "
            "your recent evidence rather than treating this as a fresh isolated interaction."
        )

    def _memory_notes(self, memory_context: MemoryContext) -> list[str]:
        if not memory_context.applied:
            return []
        return [
            (
                f"Retrieved memory applied for {memory_context.purpose}: "
                f"{memory_context.snippets()[0]}"
            )
        ]

    def _with_memory_limitations(
        self, unsupported_claims: list[str], memory_context: MemoryContext
    ) -> list[str]:
        claims = list(unsupported_claims)
        if memory_context.applied:
            claims.append("Retrieved memory was used as advisory context, not as proof of correctness.")
        return claims


mentor_service = MentorService()
