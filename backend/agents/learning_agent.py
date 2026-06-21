""""""

import os
import json
from langchain.agents import AgentExecutor, create_react_agent
# from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from agents.state import AgentState
from agents.llm_config import get_llm, MAX_ASSESSMENT_QUESTIONS
from tools.profile_tool import PROFILE_TOOLS
from tools.progress_tool import PROGRESS_TOOLS


LEARNING_AGENT_TOOLS = PROFILE_TOOLS + PROGRESS_TOOLS


# ─── Assessment Questions Bank ─────────────────────────────────────────────

ASSESSMENT_RUBRIC = """
ASSESSMENT SCORING RUBRIC:
- A1: Can only use basic phrases, many Arabic interference errors
- A2: Can form simple sentences but makes frequent grammar errors
- B1: Can communicate on familiar topics with some grammar errors
- B2: Can interact with fluency, occasional errors in complex structures
- C1: Can express ideas fluently with rare errors
- C2: Near-native proficiency, sophisticated vocabulary
"""



from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

LEARNING_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Senior Silicon Valley Career Strategist & Language Assessor.
You specialize in evaluating Saudi tech professionals and designing elite, highly effective English learning roadmaps.

Your personality:
- Authoritative, deeply analytical, and highly structured.
- Professional, yet supportive and empowering.
- You understand the specific linguistic challenges Arabic speakers face in technical English.

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

CRITICAL ASSESSMENT RULE:
If the user's message is a valid attempt at answering your assessment question, you MUST include the exact string "[VALID_ANSWER]" somewhere in your response. If they are just asking a clarifying question, chatting off-topic, or refusing to answer, DO NOT include this marker.

WEEKLY PLAN FORMAT (when user asks for a plan):
Based on the learner's weak areas and recurring mistakes, you MUST use the provided tools (e.g., update_learning_goals, add_weak_area) BEFORE generating the plan. Then, output the plan using beautiful, structured Markdown:

### 🚀 Your Elite Weekly Learning Plan
*Targeted to improve: [List 2-3 weak areas]*

**📅 Day 1-2: Core Foundation**
- **Grammar/Structure:** [Target specific weak areas]
- *Time:* 20 mins

**📅 Day 3-4: Tech Immersion**
- **Conversation Practice:** [Topics from preferred_topics]
- *Time:* 25 mins

**📅 Day 5: Scenario Simulation**
- **Roleplay Practice:** [Workplace scenarios]
- *Time:* 30 mins

**📅 Day 6: Professional Output**
- **Writing Practice:** [Professional emails/docs]
- *Time:* 20 mins

**📅 Day 7: Retrospective & Review**
- **Assessment:** [Vocabulary and grammar review]
- *Time:* 15 mins

Include actionable advice on how to integrate this into a busy engineering schedule."""),
    ("human", "User message: {input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])



def learning_agent_node(state: AgentState) -> AgentState:
    """"""
    profile = state.get("learner_profile")
    user_input = state.get("user_input", "")
    assessment_complete = state.get("assessment_complete", False)
    questions_asked = state.get("assessment_questions_asked", 0)
    context_summary = state.get("context_summary", "No previous context.")

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

        from langchain.agents import create_tool_calling_agent
        agent = create_tool_calling_agent(
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

        result = executor.invoke({
            "input": user_input,
            "assessment_protocol": assessment_protocol,
            **context,
        })

        agent_response = result.get("output", "I'm sorry, I couldn't process your request.")

        if not assessment_complete:
            if "[VALID_ANSWER]" in agent_response:
                questions_asked += 1
                if questions_asked >= MAX_ASSESSMENT_QUESTIONS:
                    assessment_complete = True
            
        # Clean up marker before showing to user
        agent_response = agent_response.replace("[VALID_ANSWER]", "").strip()

    except Exception as e:
        agent_response = (
            "I encountered an issue. Let me try again. "
            "Could you tell me a bit about your English learning goals?"
        )

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
