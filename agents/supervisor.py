"""
agents/supervisor.py
--------------------
الـ Supervisor Node — يستقبل كل رسالة ويقرر أي Agent يشتغل.

كيف يعمل (بعد التحديث)؟
1. يقرأ context_summary + آخر 3 رسائل (بدل آخر 3 رسائل فقط)
2. يبني Prompt غني بالسياق
3. يستدعي الـ LLM للحصول على قرار الـ Routing
4. يُحدِّث next_agent في الـ State

الذاكرة الملخصة (Context Summary Memory):
- الملخص يُبنى بواسطة context_summarizer_node (في __init__.py)
- الـ Supervisor يقرأه فقط — لا يُعدّله
- هذا يوفر tokens مع الحفاظ على كل السياق المهم

لماذا Sequential وليس Parallel؟
- كل Agent يحتاج يعرف ما فعله الـ Agent قبله
- الـ State يتراكم عبر الجلسة
- لا يمكن تشغيل Feedback Agent قبل أن يكتب المستخدم نصاً
"""

import json
import os
import re

from agents.state import AgentState
from agents.llm_config import get_llm, RECENT_MESSAGES_WINDOW


# ─── Prompt الـ Supervisor (محسّن مع Context Summary) ──────────────────────

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor of FluentTech — an English Learning AI system for Saudi tech professionals.

Your ONLY job is to decide which specialized agent should handle the user's message.
Respond with ONLY one agent name — no explanation, no extra text.

═══════════════════════════════════════════════
AVAILABLE AGENTS:
═══════════════════════════════════════════════
- learning_agent: Level assessment, goal setting, learning plans, progress review
- conversation_agent: English conversation practice on daily/technical topics
- roleplay_agent: Job interview simulations and workplace scenario practice  
- feedback_agent: Grammar correction, text evaluation, writing analysis
- end: User wants to stop, says goodbye, or session is done

═══════════════════════════════════════════════
ROUTING RULES (in priority order):
═══════════════════════════════════════════════
1. NO profile OR assessment incomplete → learning_agent
2. User asks about progress, goals, plan, level → learning_agent
3. User wants conversation practice or discusses a topic → conversation_agent
4. User mentions interview, meeting, presentation, roleplay, simulation → roleplay_agent
5. User submits text for correction, asks for feedback, check, or review → feedback_agent
6. User wants exercise, drill, quiz → conversation_agent (uses exercise tools)
7. User says bye, exit, stop, done, quit, goodbye → end

═══════════════════════════════════════════════
CONTEXT (use this to make accurate decisions):
═══════════════════════════════════════════════
Learner Profile:
- Has profile: {has_profile}
- Current level: {current_level}
- Target level: {target_level}
- Assessment complete: {assessment_complete}
- Learning goals: {learning_goals}
- Weak areas: {weak_areas}

Conversation Summary (what happened so far):
{context_summary}

Current Session:
- Current agent: {current_session_type}
- Current topic: {current_topic}
- Messages in session: {total_messages}
- Agent switches so far: {agent_switches}

Recent Messages (last {window_size}):
{recent_messages}

═══════════════════════════════════════════════
User's latest message: "{user_input}"
═══════════════════════════════════════════════

Respond with EXACTLY one of: learning_agent, conversation_agent, roleplay_agent, feedback_agent, end"""


# ─── الـ Supervisor Node ────────────────────────────────────────────────────

def supervisor_node(state: AgentState) -> AgentState:
    """
    الـ Node الرئيسي في الـ LangGraph Graph.

    الخطوات:
    1. Turn Guard — يشيك إذا Agent رد بالفعل
    2. يستخرج السياق من الـ State (بما فيه context_summary)
    3. يبني الـ Prompt مع كل السياق
    4. يستدعي الـ LLM
    5. يُحدِّث next_agent + agent_switches

    Turn Guard:
    - إذا Agent رد بالفعل (آخر رسالة assistant) → "end" مباشرة
    - هذا يمنع الـ Infinite Loop مع الحفاظ على بنية agents→supervisor
    """

    # ─── Turn Guard ──────────────────────────────────────────────────────────
    messages = state.get("messages", [])
    current_session = state.get("current_session_type")
    if current_session and messages and messages[-1].get("role") == "assistant":
        return {
            **state,
            "next_agent": "end",
            "routing_reason": f"Turn complete — {current_session} already responded",
        }

    # ─── استخراج السياق ─────────────────────────────────────────────────────
    profile = state.get("learner_profile")
    has_profile = profile is not None
    current_level = profile["current_level"] if has_profile else "Unknown"
    target_level = profile.get("target_level", "B2") if has_profile else "B2"
    assessment_complete = state.get("assessment_complete", False)
    current_session_type = state.get("current_session_type", "None")
    current_topic = state.get("current_topic", "Not set")
    user_input = state.get("user_input", "")
    context_summary = state.get("context_summary", "No conversation history yet.")
    total_messages = state.get("total_messages_count", 0)
    agent_switches = state.get("agent_switches", 0)

    # معلومات البروفايل
    learning_goals = profile.get("learning_goals", []) if has_profile else []
    weak_areas = profile.get("weak_areas", []) if has_profile else []

    # ─── آخر N رسائل للـ Context ────────────────────────────────────────────
    window = RECENT_MESSAGES_WINDOW
    recent_messages = messages[-window:] if len(messages) >= window else messages
    recent_str = "\n".join([
        f"  {m['role'].upper()}: {m['content'][:200]}"  # نقطع الرسائل الطويلة
        for m in recent_messages
    ]) if recent_messages else "  (no messages yet)"

    # ─── بناء الـ Prompt ────────────────────────────────────────────────────
    prompt = SUPERVISOR_SYSTEM_PROMPT.format(
        has_profile=has_profile,
        current_level=current_level,
        target_level=target_level,
        assessment_complete=assessment_complete,
        learning_goals=learning_goals,
        weak_areas=weak_areas,
        context_summary=context_summary,
        current_session_type=current_session_type,
        current_topic=current_topic,
        total_messages=total_messages,
        agent_switches=agent_switches,
        window_size=window,
        recent_messages=recent_str,
        user_input=user_input,
    )

    # ─── استدعاء الـ LLM ───────────────────────────────────────────────────
    try:
        llm = get_llm("supervisor")
        response = llm.invoke(prompt)

        # تنظيف الرد — نريد فقط اسم الـ Agent
        # نبحث عن أول agent name في الرد
        agent_choice = _extract_agent_name(response)

        if agent_choice:
            routing_reason = f"LLM decision: {agent_choice}"
        else:
            # Fallback بناءً على intent keywords
            agent_choice = _keyword_fallback(user_input, assessment_complete)
            routing_reason = f"LLM unclear ('{response[:50]}'), keyword fallback: {agent_choice}"

    except Exception as e:
        # Fallback عند أي خطأ — نستخدم keyword matching
        agent_choice = _keyword_fallback(user_input, assessment_complete)
        routing_reason = f"Error: {str(e)[:80]}, keyword fallback: {agent_choice}"

    # ─── تحديث agent_switches ──────────────────────────────────────────────
    new_switches = agent_switches
    if (current_session_type and
            agent_choice != "end" and
            agent_choice != current_session_type):
        new_switches += 1

    # ─── تحديث الـ State ───────────────────────────────────────────────────
    return {
        **state,
        "next_agent": agent_choice,
        "routing_reason": routing_reason,
        "agent_switches": new_switches,
    }


def route_to_agent(state: AgentState) -> str:
    """
    دالة الـ Conditional Edge في الـ LangGraph Graph.

    LangGraph يستدعيها بعد الـ Supervisor Node
    وتُرجع اسم الـ Node التالي.
    """
    next_agent = state.get("next_agent")
    return next_agent if next_agent is not None else "learning_agent"


# ─── دوال مساعدة ────────────────────────────────────────────────────────────

def _extract_agent_name(response: str) -> str:
    """
    يستخرج اسم الـ Agent من رد الـ LLM.

    يبحث عن أول ظهور لأي اسم agent في النص.
    أقوى من split()[0] لأن الـ LLM أحياناً يرد بجمل.
    """
    valid_agents = [
        "learning_agent", "conversation_agent",
        "roleplay_agent", "feedback_agent", "end"
    ]

    cleaned = response.strip().lower()

    # محاولة 1: الرد كله = اسم agent
    first_word = cleaned.split()[0] if cleaned else ""
    if first_word in valid_agents:
        return first_word

    # محاولة 2: البحث في كل النص
    for agent in valid_agents:
        if agent in cleaned:
            return agent

    return ""  # لم يُعثر على agent name


def _keyword_fallback(user_input: str, assessment_complete: bool) -> str:
    """
    Fallback ذكي بناءً على keywords في رسالة المستخدم.

    يُستخدم عندما:
    - الـ LLM يرد بشكل غير متوقع
    - الـ LLM يفشل (خطأ شبكة، rate limit, etc.)

    أفضل من fallback ثابت (مثل دائماً learning_agent).
    """
    user_lower = user_input.lower().strip()

    # End signals
    end_keywords = ["bye", "goodbye", "exit", "stop", "quit", "done",
                     "thanks", "شكراً", "مع السلامة", "خلاص"]
    if any(kw in user_lower for kw in end_keywords):
        return "end"

    # Feedback signals
    feedback_keywords = ["check", "correct", "fix", "feedback", "evaluate",
                         "review my", "analyze", "grade", "score",
                         "is this correct", "mistakes"]
    if any(kw in user_lower for kw in feedback_keywords):
        return "feedback_agent"

    # Roleplay signals
    roleplay_keywords = ["interview", "roleplay", "simulate", "pretend",
                          "meeting", "presentation", "client call",
                          "salary", "recruiter", "sprint", "scenario"]
    if any(kw in user_lower for kw in roleplay_keywords):
        return "roleplay_agent"

    # Learning signals
    learning_keywords = ["progress", "plan", "goal", "level", "assessment",
                          "schedule", "how am i doing", "weak", "improve",
                          "track", "summary"]
    if any(kw in user_lower for kw in learning_keywords):
        return "learning_agent"

    # لو ما عنده بروفايل → learning (تشخيص)
    if not assessment_complete:
        return "learning_agent"

    # Default → conversation
    return "conversation_agent"
