""""""

from typing import TypedDict, Optional, List, Literal
from datetime import datetime


AgentType = Literal[
    "learning_agent",
    "conversation_agent",
    "roleplay_agent",
    "feedback_agent",
    "end"
]

RoleplayScenario = Literal[
    "job_interview",
    "sprint_meeting",
    "client_call",
    "project_presentation",
    "salary_discussion",
    "recruiter_screening"
]


class LearnerProfile(TypedDict):
    """"""
    learner_id: str
    name: str
    current_level: str          # A1, A2, B1, B2, C1, C2
    target_level: str
    learning_goals: List[str]   # ["job interview", "technical communication"]
    weak_areas: List[str]       # ["grammar", "vocabulary", "fluency"]
    preferred_topics: List[str] # ["AI", "cloud", "software engineering"]
    sessions_completed: int


class FeedbackResult(TypedDict):
    """"""
    original_text: str
    corrected_text: str
    grammar_score: float        # 0.0 - 10.0
    vocabulary_score: float     # 0.0 - 10.0
    clarity_score: float        # 0.0 - 10.0
    tone_score: float           # 0.0 - 10.0
    job_readiness_score: float  # 0.0 - 100.0
    corrections: List[str]      # ["Subject-verb agreement error: ..."]
    suggestions: List[str]      # ["Consider using more formal vocabulary"]
    rag_sources: List[str]


class MistakeRecord(TypedDict):
    """"""
    type: str              # "grammar", "vocabulary", "pronunciation", "structure"
    original: str
    correction: str
    rule: str
    agent_source: str


class AgentState(TypedDict):
    """"""

    learner_profile: Optional[LearnerProfile]

    messages: List[dict]

    user_input: str

    # ─── Context Summary Memory ────────────────────────────────
    context_summary: Optional[str]

    messages_since_last_summary: int

    total_messages_count: int

    next_agent: Optional[AgentType]

    routing_reason: Optional[str]

    current_session_type: Optional[AgentType]

    current_topic: Optional[str]

    roleplay_scenario: Optional[RoleplayScenario]

    roleplay_stage_index: int

    assessment_complete: bool

    assessment_questions_asked: int

    agent_switches: int

    current_exercise: Optional[str]

    last_feedback: Optional[FeedbackResult]

    session_mistakes: List[dict]

    # ─── RAG Context ─────────────────────────────────────────────
    rag_context: Optional[str]

    error_message: Optional[str]

    session_ended: bool

    session_start_time: Optional[str]


def create_initial_state(
    learner_id: str,
    user_input: str,
    learner_profile: Optional[LearnerProfile] = None
) -> AgentState:
    """"""
    return AgentState(
        learner_profile=learner_profile,
        messages=[{"role": "user", "content": user_input}],
        user_input=user_input,
        # Context Summary Memory
        context_summary=None,
        messages_since_last_summary=1,
        total_messages_count=1,
        # Supervisor
        next_agent=None,
        routing_reason=None,
        # Session context
        current_session_type=None,
        current_topic=None,
        roleplay_scenario=None,
        roleplay_stage_index=0,
        assessment_complete=learner_profile is not None,
        assessment_questions_asked=0,
        agent_switches=0,
        # Results
        current_exercise=None,
        last_feedback=None,
        session_mistakes=[],
        rag_context=None,
        # Flow
        error_message=None,
        session_ended=False,
        session_start_time=datetime.utcnow().isoformat(),
    )
