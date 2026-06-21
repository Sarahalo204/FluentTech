""""""

import json
import os
import re
from pydantic import BaseModel, Field
from typing import Literal

from agents.state import AgentState
from agents.llm_config import get_llm, RECENT_MESSAGES_WINDOW



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
1. User says bye, exit, stop, quit, goodbye, i have to go → end
2. NO profile OR assessment incomplete → learning_agent
3. IF the user is currently in a session (e.g., '{current_session_type}') and is responding naturally to it, KEEP routing them to '{current_session_type}'. Do NOT switch agents.
4. User explicitly submits text for correction, asks for feedback, check, or review → feedback_agent
5. User explicitly asks HOW to do something, asks for advice, or asks a general question (e.g., "what are the most common interview questions?", "explain X") → conversation_agent
6. User explicitly asks to START a roleplay/simulation, OR says they are preparing for an upcoming interview/meeting and want to practice → roleplay_agent
7. User asks about progress, goals, plan, level → learning_agent
8. User wants conversation practice or discusses a general/tech topic → conversation_agent

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

Respond based on the provided routing rules and context."""

class RouterDecision(BaseModel):
    next_agent: Literal["learning_agent", "conversation_agent", "roleplay_agent", "feedback_agent", "end"] = Field(
        description="The exact name of the agent to route the user to next."
    )
    reason: str = Field(
        description="A brief explanation of why this agent was chosen."
    )

def supervisor_node(state: AgentState) -> AgentState:
    """"""

    # ─── Turn Guard ──────────────────────────────────────────────────────────
    messages = state.get("messages", [])
    current_session = state.get("current_session_type")
    if messages and messages[-1].get("role") == "assistant":
        return {
            **state,
            "next_agent": "end",
            "routing_reason": f"Turn complete — {current_session} already responded",
        }

    user_input = state.get("user_input", "")

    # ─── Absolute Context Lock for Roleplay ──────────────────────────────────
    # Ensure the user NEVER exits a roleplay scenario until it's explicitly ended.
    if current_session == "roleplay_agent":
        end_kws = ["bye", "goodbye", "exit", "stop", "quit", "going to go", "have to go", "مع السلامة", "خلاص"]
        user_lower = user_input.lower().strip()
        words = user_lower.split()
        
        # Only trigger hard-end if it's a very short phrase to avoid false positives in long answers
        is_short_phrase = len(words) <= 6
        if is_short_phrase and any(kw in user_lower for kw in end_kws):
            return {**state, "next_agent": "end", "routing_reason": "User ended roleplay explicitly"}
        else:
            return {**state, "next_agent": "roleplay_agent", "routing_reason": "Hard-locked in active roleplay session"}

    profile = state.get("learner_profile")
    has_profile = profile is not None
    current_level = profile.get("current_level", "Unknown") if has_profile else "Unknown"
    target_level = profile.get("target_level", "B2") if has_profile else "B2"
    assessment_complete = state.get("assessment_complete", False)
    current_session_type = current_session if current_session else "None"
    current_topic = state.get("current_topic", "Not set")
    context_summary = state.get("context_summary", "No conversation history yet.")
    total_messages = state.get("total_messages_count", 0)
    agent_switches = state.get("agent_switches", 0)

    learning_goals = profile.get("learning_goals", []) if has_profile else []
    weak_areas = profile.get("weak_areas", []) if has_profile else []

    window = RECENT_MESSAGES_WINDOW
    recent_messages = messages[-window:] if len(messages) >= window else messages
    recent_str = "\n".join([
        f"  {m['role'].upper()}: {m['content'][:200]}"
        for m in recent_messages
    ]) if recent_messages else "  (no messages yet)"

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

    try:
        llm = get_llm("supervisor")
        structured_llm = llm.with_structured_output(RouterDecision)
        decision = structured_llm.invoke(prompt)

        agent_choice = decision.next_agent
        routing_reason = decision.reason


    except Exception as e:
        agent_choice = _keyword_fallback(user_input, assessment_complete)
        routing_reason = f"Error: {str(e)[:80]}, keyword fallback: {agent_choice}"

    new_switches = agent_switches
    if (current_session_type and
            agent_choice != "end" and
            agent_choice != current_session_type):
        new_switches += 1

    return {
        **state,
        "next_agent": agent_choice,
        "routing_reason": routing_reason,
        "agent_switches": new_switches,
    }


def route_to_agent(state: AgentState) -> str:
    """"""
    next_agent = state.get("next_agent")
    return next_agent if next_agent is not None else "learning_agent"






def _keyword_fallback(user_input: str, assessment_complete: bool) -> str:
    """"""
    user_lower = user_input.lower().strip()

    # End signals
    end_keywords = ["bye", "goodbye", "exit", "stop", "quit",
                     "going to go", "have to go", "مع السلامة", "خلاص"]
    if any(kw in user_lower for kw in end_keywords):
        return "end"

    # Feedback signals
    feedback_keywords = ["check", "correct", "fix", "feedback", "evaluate",
                         "review my", "analyze", "grade", "score",
                         "is this correct", "mistakes", "how is my writing"]
    if any(kw in user_lower for kw in feedback_keywords):
        return "feedback_agent"
        
    # How-to signals (teaching) -> conversation_agent
    howto_keywords = ["how to", "best structure", "how do i", "explain", "meaning of", "what are", "what the", "what is", "how many"]
    if any(kw in user_lower for kw in howto_keywords):
        return "conversation_agent"

    # Roleplay signals
    roleplay_keywords = ["mock interview", "prepare for interview", "i have interview",
                          "i have a meeting", "i have a call", "i have client",
                          "roleplay", "simulate", "pretend", "practice interview",
                          "client call", "salary discussion", "recruiter screening",
                          "sprint meeting", "scenario"]
    if any(kw in user_lower for kw in roleplay_keywords):
        return "roleplay_agent"

    # Learning signals
    learning_keywords = ["progress", "plan", "goal", "level", "assessment",
                          "schedule", "how am i doing", "weak", "improve",
                          "track", "summary"]
    if any(kw in user_lower for kw in learning_keywords):
        return "learning_agent"

    if not assessment_complete:
        return "learning_agent"

    # Default → conversation
    return "conversation_agent"
