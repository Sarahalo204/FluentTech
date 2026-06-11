"""
agents/roleplay_agent.py
------------------------
Roleplay Agent — محاكي المواقف المهنية الحقيقية.

مسؤولياته:
1. محاكاة مقابلات العمل التقنية
2. محاكاة اجتماعات Sprint والعمل الجماعي
3. محاكاة مكالمات العملاء والعروض التقديمية
4. الحفاظ على شخصية المُحاوِر طوال الجلسة
5. تتبع مراحل الـ Roleplay عبر roleplay_stage_index
6. توليد Debrief مفصل في نهاية السيناريو

الفرق عن Conversation Agent:
- Roleplay Agent: يلعب دوراً محدداً (مدير، HR، عميل)
- الموقف محدد مسبقاً وله بداية ونهاية
- التقييم أكثر رسمية (Job Readiness Score)
"""

import os
import json
from langchain.agents import AgentExecutor, create_react_agent
# from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from agents.state import AgentState, RoleplayScenario
from agents.llm_config import get_llm
from tools.exercise_tool import generate_interview_question, EXERCISE_TOOLS


# ─── تعريف شخصيات الـ Roleplay ──────────────────────────────────────────────

ROLEPLAY_PERSONAS = {
    "job_interview": {
        "persona": "Senior Technical Hiring Manager at a top tech company in Riyadh",
        "context": "You are conducting a technical job interview for a software/data/AI engineering position.",
        "style": "Professional but friendly. Ask follow-up questions. Challenge vague answers politely.",
        "opening": "Good morning! Thank you for coming in today. I'm the hiring manager here. Let's start — could you please tell me about yourself and your technical background?",
        "flow": ["introduction", "technical_skills", "past_projects", "behavioral", "questions_for_us"],
        "stage_prompts": {
            "introduction": "Ask about their background and motivation",
            "technical_skills": "Ask a technical question about their core skill",
            "past_projects": "Ask them to describe a challenging project they worked on",
            "behavioral": "Ask a behavioral question: 'Tell me about a time when...'",
            "questions_for_us": "Ask if they have any questions for the company",
        },
    },
    "sprint_meeting": {
        "persona": "Engineering Team Lead facilitating a sprint review meeting",
        "context": "This is a sprint review meeting. The learner is presenting their work to the team.",
        "style": "Direct, focused on delivery and blockers. Ask about timelines and dependencies.",
        "opening": "Okay team, let's get started. Can you give us a quick update on your tasks from this sprint?",
        "flow": ["status_update", "blockers", "next_sprint", "team_feedback"],
        "stage_prompts": {
            "status_update": "Ask what they completed this sprint",
            "blockers": "Ask about any blockers or challenges",
            "next_sprint": "Discuss priorities for the next sprint",
            "team_feedback": "Give brief feedback on their update",
        },
    },
    "client_call": {
        "persona": "A client (non-technical business stakeholder) checking on project progress",
        "context": "The learner is updating a client on their project. The client is not technical.",
        "style": "Ask for simple explanations. Show concern about timeline and budget. Be politely demanding.",
        "opening": "Hi, thanks for joining the call. I wanted to get an update on where things stand with our project. Can you walk me through what's been done?",
        "flow": ["project_status", "timeline_check", "concerns", "next_steps"],
        "stage_prompts": {
            "project_status": "Ask for a high-level project status",
            "timeline_check": "Express concern about timeline — 'Are we on track?'",
            "concerns": "Raise a specific concern about a feature or deliverable",
            "next_steps": "Ask for clear next steps and a timeline",
        },
    },
    "recruiter_screening": {
        "persona": "HR Recruiter doing an initial phone screening for a tech role",
        "context": "This is a 15-minute initial screening call to assess basic fit.",
        "style": "Friendly but efficient. Cover salary, availability, and basic background.",
        "opening": "Hi! Thanks for taking my call. I'm reaching out about the position you applied for. Is this still a good time to chat for about 15 minutes?",
        "flow": ["availability", "salary_expectations", "background", "motivation", "next_steps"],
        "stage_prompts": {
            "availability": "Ask about their availability and notice period",
            "salary_expectations": "Ask about salary expectations",
            "background": "Quick overview of their background",
            "motivation": "Why are they interested in this role?",
            "next_steps": "Explain the next steps in the hiring process",
        },
    },
    "project_presentation": {
        "persona": "Panel of technical reviewers evaluating a capstone/final project",
        "context": "The learner is presenting their AI/software project to a panel.",
        "style": "Ask technical questions. Challenge design decisions. Be evaluative but constructive.",
        "opening": "Welcome! Please go ahead and start with an overview of your project — the problem you're solving and your approach.",
        "flow": ["overview", "technical_deep_dive", "challenges", "results", "future_work"],
        "stage_prompts": {
            "overview": "Ask for a project overview",
            "technical_deep_dive": "Ask about the technical implementation details",
            "challenges": "Ask about the biggest challenge they faced",
            "results": "Ask about results, metrics, or evaluation",
            "future_work": "Ask what they would do differently or next",
        },
    },
    "salary_discussion": {
        "persona": "Hiring Manager discussing compensation package",
        "context": "The job offer is on the table. Now discussing the salary and benefits.",
        "style": "Professional negotiation. Don't reveal the top budget immediately. Ask for their expectations.",
        "opening": "Congratulations — we'd like to move forward with you. Let's talk about the compensation. What are your salary expectations for this role?",
        "flow": ["expectations", "negotiation", "benefits", "final_offer"],
        "stage_prompts": {
            "expectations": "Ask for their salary expectations",
            "negotiation": "Counter-offer or negotiate terms",
            "benefits": "Discuss benefits, remote work, learning budget",
            "final_offer": "Present the final offer package",
        },
    },
}


ROLEPLAY_AGENT_PROMPT = PromptTemplate.from_template("""You are playing the role of: {persona}

Scenario context: {context}
Your interaction style: {style}

CRITICAL RULES:
1. Stay in character at ALL times
2. Do NOT break character to give English lessons mid-scenario
3. React realistically to what the learner says
4. If the learner gives a weak answer, probe deeper: "Could you elaborate on that?"
5. If the answer is very poor, react naturally: "I see... let me ask this differently..."
6. When all stages are complete, provide a brief OOC (Out of Character) debrief:
   - What they did well
   - What to improve
   - 2-3 specific language tips

Stage guidance for current stage:
{stage_guidance}

Learner profile:
- Level: {current_level}
- Goals: {learning_goals}

Conversation Summary (context from earlier):
{context_summary}

Scenario progress:
- Current stage: {current_stage} ({stage_index}/{total_stages})
- Remaining stages: {remaining_stages}
- Is this the final stage? {is_final_stage}

Available tools:
{tools}

Tool names: {tool_names}

When to use tools:
- generate_interview_question: To get structured questions for interview scenarios
- generate_vocabulary_exercise: ONLY at the end for debrief vocabulary

Conversation so far:
{conversation_history}

Learner's response: {input}

Thought: [Am I in character? What's the natural next response? Should I advance to next stage?]
Final Answer: [Stay in character. Natural, realistic response.]

{agent_scratchpad}""")


def determine_scenario(user_input: str, state: AgentState) -> str:
    """
    يحدد نوع الـ Roleplay من رسالة المستخدم.
    لو موجود في الـ State، يستخدمه مباشرة.
    """
    existing = state.get("roleplay_scenario")
    if existing:
        return existing

    user_lower = user_input.lower()

    if any(w in user_lower for w in ["interview", "hiring", "job"]):
        return "job_interview"
    elif any(w in user_lower for w in ["sprint", "meeting", "standup", "team"]):
        return "sprint_meeting"
    elif any(w in user_lower for w in ["client", "customer", "stakeholder"]):
        return "client_call"
    elif any(w in user_lower for w in ["salary", "offer", "compensation", "negotiate"]):
        return "salary_discussion"
    elif any(w in user_lower for w in ["present", "project", "demo", "showcase"]):
        return "project_presentation"
    elif any(w in user_lower for w in ["recruiter", "screening", "phone", "hr"]):
        return "recruiter_screening"
    else:
        return "job_interview"  # Fallback


def roleplay_agent_node(state: AgentState) -> AgentState:
    """
    Roleplay Agent Node.

    ما يميزه:
    1. يحمل شخصية محددة طوال الجلسة
    2. يتتبع مرحلة الـ Roleplay عبر roleplay_stage_index من الـ State
    3. يستخدم context_summary للسياق
    4. ينتقل بين المراحل تلقائياً
    5. يُنشئ Debrief في المرحلة الأخيرة
    """
    profile = state.get("learner_profile", {})
    user_input = state.get("user_input", "")
    messages = state.get("messages", [])
    context_summary = state.get("context_summary", "No previous context.")

    # تحديد السيناريو
    scenario_key = determine_scenario(user_input, state)
    scenario = ROLEPLAY_PERSONAS.get(scenario_key, ROLEPLAY_PERSONAS["job_interview"])

    current_level = profile.get("current_level", "B1") if profile else "B1"

    # إذا هذه أول رسالة في الـ Roleplay — ابدأ بالافتتاحية
    is_first_message = state.get("roleplay_scenario") is None

    conversation_history = "\n".join([
        f"  {m['role'].upper()}: {m['content'][:250]}"
        for m in messages[-6:]
    ])

    # ─── Stage Management عبر الـ State ────────────────────────────────────
    flow = scenario["flow"]
    stage_index = state.get("roleplay_stage_index", 0)

    # ننتقل للمرحلة التالية بعد كل ردين من المستخدم
    if not is_first_message:
        user_messages_in_roleplay = len([
            m for m in messages if m["role"] == "user"
        ]) - 1  # نطرح الرسالة اللي بدأت الـ roleplay
        # كل ردين = مرحلة جديدة
        stage_index = min(user_messages_in_roleplay // 2, len(flow) - 1)

    current_stage = flow[stage_index]
    remaining_stages = flow[stage_index + 1:]
    is_final_stage = stage_index >= len(flow) - 1
    stage_guidance = scenario.get("stage_prompts", {}).get(
        current_stage, "Continue the conversation naturally."
    )

    try:
        llm = get_llm("roleplay")

        agent = create_react_agent(
            llm=llm,
            tools=EXERCISE_TOOLS,
            prompt=ROLEPLAY_AGENT_PROMPT,
        )

        executor = AgentExecutor(
            agent=agent,
            tools=EXERCISE_TOOLS,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True,
        )

        # أول رسالة = الافتتاحية
        actual_input = (
            scenario["opening"] + "\n\n[The learner has arrived. Start the scenario.]"
            if is_first_message
            else user_input
        )

        result = executor.invoke({
            "input": actual_input,
            "persona": scenario["persona"],
            "context": scenario["context"],
            "style": scenario["style"],
            "current_level": current_level,
            "learning_goals": profile.get("learning_goals", []) if profile else [],
            "context_summary": context_summary,
            "current_stage": current_stage,
            "stage_index": stage_index + 1,
            "total_stages": len(flow),
            "remaining_stages": remaining_stages,
            "is_final_stage": is_final_stage,
            "stage_guidance": stage_guidance,
            "conversation_history": conversation_history,
        })

        agent_response = result.get("output", scenario["opening"])

    except Exception as e:
        agent_response = (
            scenario["opening"] if is_first_message
            else "I see. Could you tell me more about that?"
        )

    messages = list(state.get("messages", []))
    messages.append({"role": "assistant", "content": agent_response})

    return {
        **state,
        "messages": messages,
        "current_session_type": "roleplay_agent",
        "roleplay_scenario": scenario_key,
        "roleplay_stage_index": stage_index,
        "current_topic": f"Roleplay: {scenario_key.replace('_', ' ').title()}",
        "messages_since_last_summary": state.get("messages_since_last_summary", 0) + 1,
        "next_agent": None,
    }
