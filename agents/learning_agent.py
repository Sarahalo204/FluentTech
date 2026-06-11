"""
agents/learning_agent.py
------------------------
Learning & Progress Agent — دماغ النظام.

مسؤولياته:
1. تشخيص مستوى CEFR للمستخدم عبر أسئلة تدريجية (5 أسئلة)
2. تحديد الأهداف مع المستخدم
3. توليد خطة تعلم أسبوعية مخصصة
4. عرض ملخص التقدم
5. تحديث البروفايل في DB عبر الـ Tools

لماذا هو الـ Agent الافتراضي (Fallback)؟
- أول شيء يحتاجه أي مستخدم جديد هو التشخيص
- بدون معرفة المستوى، بقية الـ Agents لا تعمل بشكل صحيح
"""

import os
import json
from langchain.agents import AgentExecutor, create_react_agent
# from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from agents.state import AgentState
from agents.llm_config import get_llm, MAX_ASSESSMENT_QUESTIONS
from tools.profile_tool import PROFILE_TOOLS
from tools.progress_tool import PROGRESS_TOOLS


# ─── Tools للـ Learning Agent ───────────────────────────────────────────────
# يستخدم Profile Tools + Progress Tools
LEARNING_AGENT_TOOLS = PROFILE_TOOLS + PROGRESS_TOOLS


# ─── Assessment Questions Bank ─────────────────────────────────────────────
# أسئلة تشخيص متدرجة — الـ Agent يختار السؤال المناسب بناءً على الرد السابق

ASSESSMENT_RUBRIC = """
ASSESSMENT SCORING RUBRIC:
- A1: Can only use basic phrases, many Arabic interference errors
- A2: Can form simple sentences but makes frequent grammar errors
- B1: Can communicate on familiar topics with some grammar errors
- B2: Can interact with fluency, occasional errors in complex structures
- C1: Can express ideas fluently with rare errors
- C2: Near-native proficiency, sophisticated vocabulary
"""


# ─── Prompt للـ Learning Agent ──────────────────────────────────────────────

LEARNING_AGENT_PROMPT = PromptTemplate.from_template("""You are a friendly and professional English Learning Coach for Saudi tech learners.

Your personality:
- Encouraging and patient
- Clear and structured in your explanations
- Focused on practical, career-oriented English
- Aware of challenges Arabic speakers face in English (articles, verb tenses, prepositions)

Your available tools:
{tools}

Tool names: {tool_names}

Current learner context:
- Learner ID: {learner_id}
- Has profile: {has_profile}
- Current level: {current_level}
- Assessment complete: {assessment_complete}
- Questions asked so far: {questions_asked} / {max_questions}
- Learning goals: {learning_goals}
- Weak areas: {weak_areas}

Conversation Summary (previous context):
{context_summary}

{assessment_protocol}

WEEKLY PLAN FORMAT (when user asks for a plan):
Based on learner's weak areas and recurring mistakes, create:
Day 1-2: [Grammar focus — target specific weak areas]
Day 3-4: [Conversation practice — topics from preferred_topics]
Day 5: [Roleplay practice — workplace scenarios]
Day 6: [Writing practice — professional emails]
Day 7: [Review — vocabulary and grammar quiz]

Include estimated time per session (15-30 mins).

Use ReAct format:
Thought: [your reasoning]
Action: [tool name]
Action Input: [tool input as JSON]
Observation: [tool result]
... (repeat as needed)
Final Answer: [your response to the learner]

User message: {input}
{agent_scratchpad}""")


# ─── الـ Agent Node ─────────────────────────────────────────────────────────

def learning_agent_node(state: AgentState) -> AgentState:
    """
    Learning & Progress Agent Node.

    الخطوات:
    1. يستخرج السياق من الـ State (بما فيه context_summary)
    2. يحدد Assessment Protocol إذا التشخيص لم يكتمل
    3. يُنشئ ReAct Agent مع الـ Tools
    4. يُشغّل الـ Agent على رسالة المستخدم
    5. الـ Agent يستخدم الـ Tools (قراءة/كتابة DB) حسب الحاجة
    6. يُحدِّث الـ State بالرد والمعلومات الجديدة
    """
    profile = state.get("learner_profile")
    user_input = state.get("user_input", "")
    assessment_complete = state.get("assessment_complete", False)
    questions_asked = state.get("assessment_questions_asked", 0)
    context_summary = state.get("context_summary", "No previous context.")

    # استخرج السياق للـ Prompt
    context = {
        "learner_id": profile["learner_id"] if profile else "unknown",
        "has_profile": profile is not None,
        "current_level": profile["current_level"] if profile else "Unknown",
        "assessment_complete": assessment_complete,
        "questions_asked": questions_asked,
        "max_questions": MAX_ASSESSMENT_QUESTIONS,
        "learning_goals": profile["learning_goals"] if profile else [],
        "weak_areas": profile["weak_areas"] if profile else [],
        "context_summary": context_summary,
    }

    # Assessment Protocol — يتغير بناءً على المرحلة
    if not assessment_complete:
        if questions_asked == 0:
            assessment_protocol = f"""ASSESSMENT PROTOCOL — STAGE 1 (Introduction):
Ask the learner to introduce themselves in English.
This first question should be easy and welcoming.
Example: "Hello! I'd love to help you improve your English. Could you start by telling me a little about yourself — your name, your job or studies, and what you'd like to learn?"

{ASSESSMENT_RUBRIC}"""
        elif questions_asked < MAX_ASSESSMENT_QUESTIONS - 1:
            assessment_protocol = f"""ASSESSMENT PROTOCOL — STAGE {questions_asked + 1} (Evaluation):
Based on their previous answers, ask a question that tests a HARDER level.
Progressively increase difficulty. Focus on grammar, vocabulary, and fluency.
If their last answer was strong, ask a B2/C1 question.
If it was weak, ask a B1/A2 question.

{ASSESSMENT_RUBRIC}"""
        else:
            assessment_protocol = f"""ASSESSMENT PROTOCOL — FINAL STAGE (Level Assignment):
You've asked {questions_asked} questions. Now:
1. Estimate their CEFR level based on ALL their answers
2. Use update_learner_level tool to save the level
3. Ask about their learning goals (job interview, writing, conversation, etc.)
4. Use update_learning_goals tool to save the goals
5. Announce their level and suggest next steps

{ASSESSMENT_RUBRIC}"""
    else:
        assessment_protocol = "Assessment is complete. Focus on the user's request."

    try:
        llm = get_llm("learning")

        # إنشاء ReAct Agent
        agent = create_react_agent(
            llm=llm,
            tools=LEARNING_AGENT_TOOLS,
            prompt=LEARNING_AGENT_PROMPT,
        )

        executor = AgentExecutor(
            agent=agent,
            tools=LEARNING_AGENT_TOOLS,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
        )

        # تشغيل الـ Agent
        result = executor.invoke({
            "input": user_input,
            "assessment_protocol": assessment_protocol,
            **context,
        })

        agent_response = result.get("output", "I'm sorry, I couldn't process your request.")

        # تحديث عداد أسئلة التشخيص
        if not assessment_complete:
            questions_asked += 1
            if questions_asked >= MAX_ASSESSMENT_QUESTIONS:
                assessment_complete = True

    except Exception as e:
        agent_response = (
            "I encountered an issue. Let me try again. "
            "Could you tell me a bit about your English learning goals?"
        )

    # تحديث قائمة الرسائل بإضافة رد الـ Agent
    messages = list(state.get("messages", []))
    messages.append({"role": "assistant", "content": agent_response})

    return {
        **state,
        "messages": messages,
        "current_session_type": "learning_agent",
        "assessment_questions_asked": questions_asked,
        "assessment_complete": assessment_complete,
        "messages_since_last_summary": state.get("messages_since_last_summary", 0) + 1,
        "next_agent": None,
    }
