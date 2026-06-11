"""
agents/conversation_agent.py
-----------------------------
Conversation Agent — مدرب المحادثة اليومي.

مسؤولياته:
1. إجراء محادثات تكيفية على مواضيع يومية وتقنية
2. ضبط مستوى تعقيد اللغة بناءً على مستوى المستخدم
3. تصحيح الأخطاء بشكل خفيف وطبيعي داخل المحادثة
4. توليد تمارين Vocabulary وGrammar عند الحاجة
5. تتبع الموضوع الحالي وتحديثه في الـ State
6. تتبع الأخطاء بشكل structured

الفرق بينه وبين Feedback Agent:
- Conversation Agent: يصحح بشكل خفيف ويستمر في المحادثة
- Feedback Agent: يُحلل النص بالكامل ويُعطي تقييم شامل
"""

import os
import json
import re
# from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from agents.state import AgentState
from agents.llm_config import get_llm
from tools.exercise_tool import EXERCISE_TOOLS


# ─── Language Complexity Rules ──────────────────────────────────────────────
# كيف يتكلم الـ Agent مع كل مستوى — أكثر تفصيلاً

LANGUAGE_RULES_BY_LEVEL = {
    "A1": (
        "Use very simple words (max 8 words per sentence). No idioms. "
        "Repeat key words. Use present tense only. "
        "Avoid passive voice. Use 'he/she does' not 'one does'."
    ),
    "A2": (
        "Use simple vocabulary. Short-medium sentences (max 12 words). "
        "Avoid complex grammar. Use common phrases. "
        "Past tense OK. No conditionals or subjunctive."
    ),
    "B1": (
        "Use everyday vocabulary with some professional terms. "
        "Medium sentences. Simple idioms okay. "
        "All basic tenses. Simple conditionals (if + present, will + verb)."
    ),
    "B2": (
        "Use professional vocabulary. Complex sentences acceptable. "
        "Use idioms and collocations. All tenses including perfect. "
        "Passive voice OK. Technical jargon welcome."
    ),
    "C1": (
        "Use advanced vocabulary. Complex structures with subordinate clauses. "
        "Sophisticated idioms. Academic register. "
        "Nuanced expressions. Discuss abstract concepts."
    ),
    "C2": (
        "Use full professional English. All structures. Rich vocabulary. "
        "Native-level complexity. Humor and sarcasm appropriate. "
        "Discuss complex, nuanced, or philosophical topics."
    ),
}

# ─── Topic Detection Keywords ──────────────────────────────────────────────

TOPIC_KEYWORDS = {
    "AI / Machine Learning": [
        "ai", "machine learning", "neural", "model", "training",
        "deep learning", "nlp", "llm", "chatgpt", "transformer",
        "embedding", "fine-tuning", "prompt", "generative"
    ],
    "Cloud Computing": [
        "cloud", "aws", "azure", "gcp", "deployment", "kubernetes",
        "docker", "serverless", "microservices", "devops", "ci/cd"
    ],
    "Software Engineering": [
        "code", "programming", "software", "debugging", "api",
        "backend", "frontend", "database", "architecture", "git",
        "testing", "agile", "scrum", "sprint", "refactoring"
    ],
    "Data Science": [
        "data", "analysis", "pipeline", "dataset", "feature",
        "visualization", "statistics", "pandas", "sql", "etl",
        "warehouse", "bi", "dashboard"
    ],
    "Cybersecurity": [
        "security", "encryption", "firewall", "vulnerability",
        "authentication", "penetration", "hack", "malware"
    ],
    "Product Management": [
        "product", "roadmap", "stakeholder", "user story",
        "backlog", "prioritize", "mvp", "kpi", "metrics"
    ],
    "Job & Career": [
        "interview", "job", "hiring", "resume", "cv",
        "career", "promotion", "salary", "linkedin"
    ],
}


CONVERSATION_AGENT_PROMPT = PromptTemplate.from_template("""You are an English conversation coach having a natural practice conversation with a Saudi tech learner.

Learner's profile:
- Name: {learner_name}
- Current level: {current_level}
- Learning goals: {learning_goals}
- Weak areas: {weak_areas}
- Preferred topics: {preferred_topics}

Language complexity rule for this learner:
{language_rule}

Conversation Summary (what happened before):
{context_summary}

Your conversation style:
1. Respond naturally to what they said
2. If they make a grammar mistake, gently correct it inline like: 
   "Great point! (Small correction: it's 'I have been' not 'I have be') Now, continuing..."
3. Ask ONE follow-up question to keep the conversation going
4. Every 3-4 exchanges, introduce a new vocabulary word relevant to the topic
5. If they seem stuck, offer a simpler way to express the idea
6. Adapt your language complexity to match their level

Available tools (use when helpful):
{tools}

Tool names: {tool_names}

When to use tools:
- generate_vocabulary_exercise: When introducing new vocabulary for their topic
- generate_grammar_exercise: When you notice a repeated grammar mistake
- generate_email_writing_task: When they want to practice professional writing
- generate_sentence_rewrite: When they use a simple sentence that could be more advanced

Current topic: {current_topic}
Exchange count in this session: {exchange_count}

Recent conversation (last 5 messages):
{conversation_history}

User's message: {input}

Use ReAct format if using tools, otherwise respond directly:
Thought: [brief reasoning about level-appropriate response]
Final Answer: [your conversational response]

{agent_scratchpad}""")


def extract_current_topic(messages: list) -> str:
    """
    يحدد الموضوع الحالي من تاريخ المحادثة.
    يبحث في آخر 5 رسائل عن كلمات مفتاحية.
    يدعم مواضيع أكثر من النسخة السابقة.
    """
    if not messages:
        return "general conversation"

    recent_text = " ".join([
        m.get("content", "") for m in messages[-5:]
    ]).lower()

    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in recent_text for kw in keywords):
            return topic

    return "general tech conversation"


def _extract_inline_corrections(response: str) -> list:
    """
    يستخرج التصحيحات من رد الـ Agent بشكل structured.

    يبحث عن أنماط مثل:
    - "(Small correction: it's X not Y)"
    - "(correction: X → Y)"
    """
    corrections = []

    # Pattern 1: (Small correction: ...)
    pattern1 = r'\((?:Small |small )?correction:\s*(.+?)\)'
    matches = re.findall(pattern1, response, re.IGNORECASE)
    for match in matches:
        corrections.append({
            "type": "grammar",
            "original": "",
            "correction": match.strip(),
            "rule": "inline correction by conversation agent",
            "agent_source": "conversation_agent",
        })

    return corrections


def conversation_agent_node(state: AgentState) -> AgentState:
    """
    Conversation Agent Node.

    ما يميزه:
    - يستخدم context_summary للسياق الكامل
    - يتتبع الموضوع ويُحدّثه في الـ State
    - يكتشف الأخطاء ويحفظها structured
    - يتكيف مع مستوى المستخدم عبر language rules
    """
    profile = state.get("learner_profile", {})
    user_input = state.get("user_input", "")
    messages = state.get("messages", [])
    context_summary = state.get("context_summary", "No previous context.")

    current_level = profile.get("current_level", "B1") if profile else "B1"
    language_rule = LANGUAGE_RULES_BY_LEVEL.get(current_level, LANGUAGE_RULES_BY_LEVEL["B1"])

    # آخر 5 رسائل للسياق
    conversation_history = "\n".join([
        f"  {m['role'].upper()}: {m['content'][:200]}"
        for m in messages[-5:]
    ])

    # تحديد الموضوع
    current_topic = extract_current_topic(messages)

    # عدد التبادلات (user messages فقط)
    exchange_count = len([m for m in messages if m["role"] == "user"])

    try:
        llm = get_llm("conversation")

        agent = create_react_agent(
            llm=llm,
            tools=EXERCISE_TOOLS,
            prompt=CONVERSATION_AGENT_PROMPT,
        )

        executor = AgentExecutor(
            agent=agent,
            tools=EXERCISE_TOOLS,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True,
        )

        result = executor.invoke({
            "input": user_input,
            "learner_name": profile.get("name", "Learner") if profile else "Learner",
            "current_level": current_level,
            "learning_goals": profile.get("learning_goals", []) if profile else [],
            "weak_areas": profile.get("weak_areas", []) if profile else [],
            "preferred_topics": profile.get("preferred_topics", []) if profile else [],
            "language_rule": language_rule,
            "context_summary": context_summary,
            "conversation_history": conversation_history,
            "current_topic": current_topic,
            "exchange_count": exchange_count,
        })

        agent_response = result.get("output", "Let's continue our conversation. What would you like to discuss?")

        # اكتشاف الأخطاء من رد الـ Agent — structured
        session_mistakes = list(state.get("session_mistakes", []))
        new_corrections = _extract_inline_corrections(agent_response)
        session_mistakes.extend(new_corrections)

    except Exception as e:
        agent_response = (
            "That's a great topic to discuss! "
            "Could you tell me more about your experience with it?"
        )
        session_mistakes = list(state.get("session_mistakes", []))

    messages = list(state.get("messages", []))
    messages.append({"role": "assistant", "content": agent_response})

    return {
        **state,
        "messages": messages,
        "current_session_type": "conversation_agent",
        "current_topic": current_topic,
        "session_mistakes": session_mistakes,
        "messages_since_last_summary": state.get("messages_since_last_summary", 0) + 1,
        "next_agent": None,
    }
