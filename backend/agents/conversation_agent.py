""""""

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
    "Web Development": [
        "web", "react", "angular", "vue", "html", "css", "javascript",
        "typescript", "nextjs", "node", "express", "ui", "ux", "accessibility"
    ],
    "Mobile App Development": [
        "mobile", "ios", "android", "flutter", "react native", "swift",
        "kotlin", "app", "apk", "testflight"
    ],
    "Database Administration": [
        "database", "sql", "nosql", "postgres", "mysql", "mongodb", "redis",
        "schema", "migration", "query", "indexing"
    ],
    "Networking": [
        "network", "tcp", "ip", "dns", "http", "https", "routing",
        "latency", "bandwidth", "vpn", "proxy", "load balancer"
    ],
    "Digital Marketing": [
        "marketing", "seo", "campaign", "social media", "ads", "conversion",
        "roi", "analytics", "funnel", "customer acquisition", "strategy"
    ],
}


from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

CONVERSATION_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an Elite Silicon Valley Technical Lead and Executive Communication Coach.
You are mentoring a Saudi tech professional to help them achieve global standards of technical communication.

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

Your conversational style and directives:
1. Speak with the authority, clarity, and precision of a Senior Tech Lead at a top-tier tech company. Be highly encouraging and empowering.
2. ALWAYS prioritize answering the user's explicit questions or requests FIRST. Provide deep, valuable technical or linguistic insight.
3. If they make a grammar or vocabulary mistake, gently correct it inline using exactly this syntax on a new line: *[Correction: ...]*
   Example: 
   *[Correction: I have been working on the API]*
   Then continue your response naturally.
4. Keep the conversation moving by asking ONE thought-provoking technical or strategic follow-up question. Do NOT ask a question if they just wanted an explanation.
5. Adapt your complexity to match their level, but maintain a highly professional tech-industry tone.

When to use tools:
- generate_vocabulary_exercise: When introducing new advanced vocabulary for their topic
- generate_grammar_exercise: When you notice a repeated structural mistake
- generate_email_writing_task: When they want to practice professional communication
- generate_sentence_rewrite: When they use a simple sentence that could be more impactful

Current topic: {current_topic}
Exchange count in this session: {exchange_count}

Recent conversation:
{conversation_history}"""),
    ("human", "User's message: {input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


def extract_current_topic(messages: list) -> str:
    """"""
    if not messages:
        return "general conversation"

    recent_text = " ".join([
        m.get("content", "") for m in messages[-5:]
    ]).lower()

    # Try semantic classification first
    try:
        from pydantic import BaseModel, Field
        from typing import Literal
        
        class TopicClassification(BaseModel):
            topic: Literal[
                "AI / Machine Learning", "Cloud Computing", "Software Engineering",
                "Data Science", "Cybersecurity", "Product Management",
                "Job & Career", "Web Development", "Mobile App Development",
                "Database Administration", "Networking", "Digital Marketing",
                "general tech conversation"
            ] = Field(description="The technical topic that best matches the conversation.")

        llm = get_llm("summarizer")
        if hasattr(llm, "with_structured_output"):
            classifier = llm.with_structured_output(TopicClassification)
            result = classifier.invoke(f"Classify the main topic of this conversation excerpt:\n{recent_text[:500]}")
            return result.topic
    except Exception:
        pass  # Fall through to keyword matching

    # Keyword fallback
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in recent_text for kw in keywords):
            return topic

    return "general tech conversation"


def _extract_inline_corrections(response: str) -> list:
    """"""
    corrections = []

    # Catch standard inline corrections: *[Correction: ...]*
    pattern = r'\*\[Correction:\s*(.*?)\]\*'
    matches = re.findall(pattern, response, re.IGNORECASE)
    for match in matches:
        if len(match.strip()) > 3:
            corrections.append({
                "type": "grammar",
                "original": "",
                "correction": match.strip(),
                "rule": "inline correction by conversation agent",
                "agent_source": "conversation_agent",
            })

    return corrections


def conversation_agent_node(state: AgentState) -> AgentState:
    """"""
    profile = state.get("learner_profile", {})
    user_input = state.get("user_input", "")
    messages = state.get("messages", [])
    context_summary = state.get("context_summary", "No previous context.")

    current_level = profile.get("current_level", "B1") if profile else "B1"
    language_rule = LANGUAGE_RULES_BY_LEVEL.get(current_level, LANGUAGE_RULES_BY_LEVEL["B1"])

    conversation_history = "\n".join([
        f"  {m['role'].upper()}: {m['content'][:800]}"
        for m in messages[-5:]
    ])

    current_topic = extract_current_topic(messages)

    exchange_count = len([m for m in messages if m["role"] == "user"])

    try:
        llm = get_llm("conversation")

        from langchain.agents import create_tool_calling_agent
        agent = create_tool_calling_agent(
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
