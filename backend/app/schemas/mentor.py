from typing import Any, Literal

from pydantic import BaseModel, Field


class ProblemInput(BaseModel):
    user_id: str = "demo-user"
    problem_number: str | None = None
    title: str
    url: str | None = None
    description: str


class TopicAnalysis(BaseModel):
    problem: str
    difficulty: str = "Unknown"
    pattern: str
    sub_patterns: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    reasoning: str
    primary_topic: str | None = None
    secondary_topics: list[str] = Field(default_factory=list)
    primary_pattern: str | None = None
    structural_cues: list[str] = Field(default_factory=list)
    related_patterns: list[str] = Field(default_factory=list)
    difficulty_signals: list[str] = Field(default_factory=list)
    confidence: float | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    taxonomy_version: str | None = None


class HintRequest(ProblemInput):
    current_hint_level: int = 0
    user_attempt: str | None = None
    reveal_solution: bool = False


class HintResponse(BaseModel):
    level: int
    max_level: int = 5
    hint: str
    reveals_solution: bool = False
    mentor_note: str
    memory_context: dict[str, Any] = Field(default_factory=dict)


class CodeReviewRequest(BaseModel):
    user_id: str = "demo-user"
    title: str
    language: str
    code: str
    problem_description: str | None = None
    user_intent: str | None = None


class FindingLocation(BaseModel):
    line_start: int | None = None
    line_end: int | None = None


class CodeFinding(BaseModel):
    finding_id: str
    category: str
    severity: str
    confidence: float
    evidence_type: str
    evidence: str
    location: FindingLocation
    message: str
    pedagogical_action: str
    provenance: str


class CodeReviewResponse(BaseModel):
    correctness: str
    time_complexity: str
    space_complexity: str
    edge_cases: list[str]
    optimization_opportunities: list[str]
    readability_feedback: list[str]
    alternative_approaches: list[str]
    suspected_mistakes: list[str]
    senior_engineer_summary: str
    review_intent: str = "REVIEW_CODE"
    language_supported: bool = False
    analysis_layers: list[str] = Field(default_factory=list)
    findings: list[CodeFinding] = Field(default_factory=list)
    corrected_code: str | None = None
    rewrite_allowed: bool = False
    unsupported_claims: list[str] = Field(default_factory=list)
    memory_context: dict[str, Any] = Field(default_factory=dict)


class StudyPlanRequest(BaseModel):
    user_id: str = "demo-user"
    target_company: str = "Google"
    days_remaining: int = 45
    hours_per_week: int = 8


class StudyPlanResponse(BaseModel):
    target_company: str
    days_remaining: int
    weekly_plan: list[dict[str, Any]]
    checkpoints: list[str]
    personalization_notes: list[str]
    memory_context: dict[str, Any] = Field(default_factory=dict)


class InterviewTurnRequest(BaseModel):
    user_id: str = "demo-user"
    session_id: str | None = None
    persona: Literal["Google", "Meta", "Amazon", "Generic"] = "Google"
    problem_title: str | None = None
    message: str


class InterviewTurnResponse(BaseModel):
    session_id: str
    interviewer_message: str
    follow_up_focus: str
    score_delta: int = 0
    feedback: list[str] = Field(default_factory=list)
    memory_context: dict[str, Any] = Field(default_factory=dict)


class AnalyticsResponse(BaseModel):
    readiness_score: int
    confidence: str = "unknown"
    evidence_count: int = 0
    strongest_topics: list[str]
    weakest_topics: list[str]
    common_mistakes: list[dict[str, Any]]
    topic_mastery: list[dict[str, Any]]
    learning_velocity: list[dict[str, Any]]
    recommendations: list[str]
    evidence_summary: dict[str, Any] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    core_pattern: str
    related_problems: list[dict[str, Any]]
    difficulty_progression: list[str]
    explanation: str
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    learner_state_confidence: str = "unknown"
    fallback_reason: str | None = None
    same_topic_shortcut_used: bool = False
    memory_context: dict[str, Any] = Field(default_factory=dict)


class PatternTransferResponse(BaseModel):
    core_idea: str
    transfer_to: list[dict[str, Any]]
    pattern_evolution: list[str]
    learning_opportunities: list[str]
    source_problem_id: str | None = None
    source_pattern: str | None = None
    classification_confidence: float | None = None
    learner_state_confidence: str = "unknown"
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    transfer_taxonomy: dict[str, str] = Field(default_factory=dict)
    evidence_hierarchy: list[dict[str, Any]] = Field(default_factory=list)
    fallback_reason: str | None = None
    same_topic_shortcut_used: bool = False
    memory_context: dict[str, Any] = Field(default_factory=dict)


class MentorRouteRequest(ProblemInput):
    requested_capability: Literal[
        "problem_analysis",
        "next_hint",
        "recommendations",
        "pattern_transfer",
        "code_review",
        "study_plan",
    ] | None = None
    user_message: str | None = None
    current_hint_level: int | None = None
    user_attempt: str | None = None
    reveal_solution: bool = False
    session_id: str | None = None
    language: str | None = None
    code: str | None = None
    problem_description: str | None = None
    target_company: str | None = None
    days_remaining: int | None = None
    hours_per_week: int | None = None


class MentorRouteResponse(BaseModel):
    selected_capability: str
    selected_skill: str
    result: dict[str, Any]
    trajectory: dict[str, Any]


class AgentTrajectoryResponse(BaseModel):
    trajectory_id: str
    request_id: str | None = None
    trace_id: str | None = None
    session_id: str | None = None
    task: str
    runtime_mode: str
    selected_capability: str | None = None
    selected_skill: str | None = None
    fallback_used: bool
    duration_ms: float | None = None
    schema_version: str
    event_count: int
    events: list[dict[str, Any]]
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyDecisionRecordResponse(BaseModel):
    id: str
    request_id: str | None = None
    trace_id: str | None = None
    session_id: str | None = None
    trajectory_id: str | None = None
    tool_id: str
    caller: str
    operation: str
    risk: str
    decision: str
    policy_id: str
    reason: str
    success: bool
    error: str | None = None
    latency_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
