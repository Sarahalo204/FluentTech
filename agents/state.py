"""
agents/state.py
---------------
الـ State المشترك بين جميع الـ Agents في الـ LangGraph Pipeline.

لماذا نحتاجه؟
- كل Agent يقرأ من الـ State ويكتب فيه
- هو الذاكرة قصيرة المدى (Short-term Memory) للجلسة الحالية
- الـ Supervisor يستخدمه لتحديد أي Agent يشتغل
- في نهاية الجلسة، يُحفظ الجزء المهم منه في PostgreSQL (Long-term Memory)

الذاكرة الملخصة (Context Summary Memory):
- بدل إرسال كل الرسائل للـ LLM (مكلف) أو آخر 3 فقط (ناقص)
- نحفظ ملخص ذكي للمحادثة + آخر 3 رسائل
- الـ Supervisor يقرأ: ملخص + آخر 3 رسائل + رسالة المستخدم
- هذا هو Industry Best Practice (Conversation Summary Buffer)
"""

from typing import TypedDict, Optional, List, Literal
from datetime import datetime


# أنواع الـ Agents المتاحة للـ Routing
AgentType = Literal[
    "learning_agent",
    "conversation_agent",
    "roleplay_agent",
    "feedback_agent",
    "end"  # إنهاء الجلسة
]

# أنواع جلسات الـ Roleplay
RoleplayScenario = Literal[
    "job_interview",
    "sprint_meeting",
    "client_call",
    "project_presentation",
    "salary_discussion",
    "recruiter_screening"
]


class LearnerProfile(TypedDict):
    """
    بروفايل المستخدم — يُجلب من PostgreSQL في بداية كل جلسة
    ويُحدَّث في نهاية الجلسة
    """
    learner_id: str
    name: str
    current_level: str          # A1, A2, B1, B2, C1, C2
    target_level: str
    learning_goals: List[str]   # ["job interview", "technical communication"]
    weak_areas: List[str]       # ["grammar", "vocabulary", "fluency"]
    preferred_topics: List[str] # ["AI", "cloud", "software engineering"]
    sessions_completed: int


class FeedbackResult(TypedDict):
    """
    نتيجة تحليل الـ Feedback Agent
    """
    original_text: str
    corrected_text: str
    grammar_score: float        # 0.0 - 10.0
    vocabulary_score: float     # 0.0 - 10.0
    clarity_score: float        # 0.0 - 10.0
    tone_score: float           # 0.0 - 10.0
    job_readiness_score: float  # 0.0 - 100.0
    corrections: List[str]      # ["Subject-verb agreement error: ..."]
    suggestions: List[str]      # ["Consider using more formal vocabulary"]
    rag_sources: List[str]      # المصادر اللي استخدمها الـ RAG


class MistakeRecord(TypedDict):
    """
    سجل خطأ مُكتشف — أكثر تفصيلاً من مجرد string
    يُستخدم لتتبع الأخطاء المتكررة عبر الجلسات
    """
    type: str              # "grammar", "vocabulary", "pronunciation", "structure"
    original: str          # النص الأصلي
    correction: str        # التصحيح
    rule: str              # القاعدة المنتهكة
    agent_source: str      # أي agent اكتشف الخطأ


class AgentState(TypedDict):
    """
    الـ State الرئيسي — يمر عبر جميع الـ Nodes في الـ LangGraph Graph

    كيف يعمل؟
    1. المستخدم يرسل رسالة → تُضاف لـ messages
    2. الـ Summarizer يُحدّث context_summary (لو تجاوز العتبة)
    3. الـ Supervisor يقرأ context_summary + آخر 3 رسائل → يحدد next_agent
    4. الـ Agent المحدد يعمل → يضيف رده لـ messages ويحدث الـ State
    5. الدورة تنتهي عبر Turn Guard في الـ Supervisor
    """

    # ─── معلومات المستخدم ───────────────────────────────────────
    learner_profile: Optional[LearnerProfile]

    # ─── المحادثة الحالية ────────────────────────────────────────
    # قائمة الرسائل: [{"role": "user"/"assistant", "content": "..."}]
    messages: List[dict]

    # آخر رسالة من المستخدم (اختصار لسهولة الوصول)
    user_input: str

    # ─── Context Summary Memory ────────────────────────────────
    # ملخص ذكي للمحادثة — يُحدَّث كل SUMMARY_UPDATE_THRESHOLD رسائل
    # مثال: "المستخدم يتعلم الإنجليزية لمقابلات العمل في مجال AI.
    #        مستواه B1. ناقش سابقاً Cloud Computing وكتابة الإيميلات.
    #        يعاني من أخطاء في past tense و subject-verb agreement."
    context_summary: Optional[str]

    # عدد الرسائل منذ آخر تحديث للملخص
    messages_since_last_summary: int

    # إجمالي الرسائل في الجلسة (user + assistant)
    total_messages_count: int

    # ─── قرارات الـ Supervisor ───────────────────────────────────
    # أي Agent سيشتغل التالي
    next_agent: Optional[AgentType]

    # سبب قرار الـ Supervisor (للـ Debugging والـ Logging)
    routing_reason: Optional[str]

    # ─── سياق الجلسة الحالية ─────────────────────────────────────
    # نوع الجلسة الحالية
    current_session_type: Optional[AgentType]

    # الموضوع الرئيسي الحالي للمحادثة
    current_topic: Optional[str]

    # سيناريو الـ Roleplay لو الجلسة roleplay
    roleplay_scenario: Optional[RoleplayScenario]

    # مرحلة الـ Roleplay الحالية (index في flow list)
    roleplay_stage_index: int

    # مرحلة التشخيص — هل اكتمل تشخيص مستوى المستخدم؟
    assessment_complete: bool

    # عدد أسئلة التشخيص اللي اتجاوبت
    assessment_questions_asked: int

    # عدد مرات تبديل الـ Agent في هذه الجلسة
    agent_switches: int

    # ─── نتائج الجلسة ────────────────────────────────────────────
    # آخر تمرين تم توليده
    current_exercise: Optional[str]

    # آخر نتيجة feedback
    last_feedback: Optional[FeedbackResult]

    # الأخطاء اللي اكتُشفت في هذه الجلسة — structured records
    session_mistakes: List[dict]

    # ─── RAG Context ─────────────────────────────────────────────
    # السياق اللي جلبه الـ RAG Retriever (يستخدمه Feedback Agent)
    rag_context: Optional[str]

    # ─── تحكم في الـ Flow ────────────────────────────────────────
    # رسالة خطأ لو صار شيء غلط
    error_message: Optional[str]

    # هل انتهت الجلسة؟
    session_ended: bool

    # وقت بداية الجلسة (ISO format)
    session_start_time: Optional[str]


def create_initial_state(
    learner_id: str,
    user_input: str,
    learner_profile: Optional[LearnerProfile] = None
) -> AgentState:
    """
    ينشئ State جديد في بداية كل جلسة.

    يُستدعى من الـ Backend عند:
    POST /api/session/start
    """
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
