""""""

from langgraph.graph import StateGraph, END

from agents.state import AgentState, create_initial_state
from agents.supervisor import supervisor_node, route_to_agent
from agents.learning_agent import learning_agent_node
from agents.conversation_agent import conversation_agent_node
from agents.roleplay_agent import roleplay_agent_node
from agents.feedback_agent import feedback_agent_node
from agents.llm_config import get_llm, SUMMARY_UPDATE_THRESHOLD


# ─── Context Summarizer Node ───────────────────────────────────────────────

def context_summarizer_node(state: AgentState) -> AgentState:
    """"""
    messages = state.get("messages", [])
    messages_since = state.get("messages_since_last_summary", 0)
    current_summary = state.get("context_summary")
    total_messages = len(messages)

    if total_messages < SUMMARY_UPDATE_THRESHOLD or messages_since < SUMMARY_UPDATE_THRESHOLD:
        return {
            **state,
            "total_messages_count": total_messages,
        }

    try:
        llm = get_llm("summarizer")

        new_messages = messages[-(messages_since):]
        messages_text = "\n".join([
            f"{m['role'].upper()}: {m['content'][:300]}"
            for m in new_messages
        ])

        profile = state.get("learner_profile")
        profile_context = ""
        if profile:
            profile_context = (
                f"Learner: {profile.get('name', 'Unknown')}, "
                f"Level: {profile.get('current_level', '?')}, "
                f"Goals: {profile.get('learning_goals', [])}"
            )

        mistakes = state.get("session_mistakes", [])
        mistakes_text = ""
        if mistakes:
            mistake_strs = []
            for m in mistakes[-5:]:
                if isinstance(m, dict):
                    mistake_strs.append(f"{m.get('type', '?')}: {m.get('original', '?')} → {m.get('correction', '?')}")
                else:
                    mistake_strs.append(str(m))
            mistakes_text = f"\nDiscovered mistakes: {'; '.join(mistake_strs)}"

        summary_prompt = f"""Summarize this English learning conversation in 2-3 concise sentences.
Focus on: what topics were discussed, what the learner practiced, any errors found, and current activity.

{profile_context}

Previous summary: {current_summary or 'None'}

New messages to incorporate:
{messages_text}
{mistakes_text}

Current activity: {state.get('current_session_type', 'None')}
Current topic: {state.get('current_topic', 'None')}

Write a brief, factual summary (2-3 sentences max):"""

        new_summary = llm.invoke(summary_prompt).strip()

        if new_summary.startswith(("Summary:", "Here")):
            new_summary = new_summary.split(":", 1)[-1].strip()

        return {
            **state,
            "context_summary": new_summary,
            "messages_since_last_summary": 0,
            "total_messages_count": total_messages,
        }

    except Exception as e:
        fallback_summary = _build_rule_based_summary(state)
        return {
            **state,
            "context_summary": fallback_summary,
            "messages_since_last_summary": 0,
            "total_messages_count": total_messages,
        }


def _build_rule_based_summary(state: AgentState) -> str:
    """"""
    parts = []

    profile = state.get("learner_profile")
    if profile:
        parts.append(
            f"Learner {profile.get('name', '?')} (Level {profile.get('current_level', '?')}) "
            f"is working towards {profile.get('target_level', '?')}."
        )

    topic = state.get("current_topic")
    if topic:
        parts.append(f"Currently discussing: {topic}.")

    session_type = state.get("current_session_type")
    if session_type:
        type_names = {
            "learning_agent": "level assessment and learning planning",
            "conversation_agent": "conversation practice",
            "roleplay_agent": "workplace roleplay simulation",
            "feedback_agent": "writing feedback and evaluation",
        }
        parts.append(f"Active session: {type_names.get(session_type, session_type)}.")

    mistakes = state.get("session_mistakes", [])
    if mistakes:
        recent = mistakes[-3:]
        mistake_strs = []
        for m in recent:
            if isinstance(m, dict):
                mistake_strs.append(m.get("type", "unknown error"))
            else:
                mistake_strs.append(str(m))
        parts.append(f"Recent mistakes: {', '.join(mistake_strs)}.")

    return " ".join(parts) if parts else "New conversation started."


# ─── Graph Builder ──────────────────────────────────────────────────────────

def create_graph():
    """"""

    graph = StateGraph(AgentState)

    graph.add_node("context_summarizer", context_summarizer_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("learning_agent", learning_agent_node)
    graph.add_node("conversation_agent", conversation_agent_node)
    graph.add_node("roleplay_agent", roleplay_agent_node)
    graph.add_node("feedback_agent", feedback_agent_node)

    graph.set_entry_point("context_summarizer")

    # ─── Edge: Summarizer → Supervisor ─────────────────────────────────────
    graph.add_edge("context_summarizer", "supervisor")

    graph.add_conditional_edges(
        source="supervisor",
        path=route_to_agent,
        path_map={
            "learning_agent": "learning_agent",
            "conversation_agent": "conversation_agent",
            "roleplay_agent": "roleplay_agent",
            "feedback_agent": "feedback_agent",
            "end": END,
        }
    )

    graph.add_edge("learning_agent", END)
    graph.add_edge("conversation_agent", END)
    graph.add_edge("roleplay_agent", END)
    graph.add_edge("feedback_agent", END)

    return graph.compile()



def run_agent(
    user_input: str,
    learner_id: str,
    existing_state: AgentState = None
) -> dict:
    """"""

    if existing_state:
        messages_since = existing_state.get("messages_since_last_summary", 0)
        state = {
            **existing_state,
            "user_input": user_input,
            "messages": existing_state.get("messages", []) + [
                {"role": "user", "content": user_input}
            ],
            "next_agent": None,
            "current_session_type": existing_state.get("current_session_type"),
            "messages_since_last_summary": messages_since + 1,
        }
    else:
        state = create_initial_state(
            learner_id=learner_id,
            user_input=user_input,
        )

    graph = create_graph()

    try:
        final_state = graph.invoke(state)

        messages = final_state.get("messages", [])
        last_assistant_message = next(
            (m["content"] for m in reversed(messages) if m["role"] == "assistant"),
            "I'm ready to help you practice English!"
        )

        return {
            "response": last_assistant_message,
            "updated_state": final_state,
            "agent_used": final_state.get("current_session_type", "unknown"),
            "feedback": final_state.get("last_feedback"),
            "routing_reason": final_state.get("routing_reason"),
            "context_summary": final_state.get("context_summary"),
        }

    except Exception as e:
        return {
            "response": "I'm sorry, something went wrong. Please try again.",
            "updated_state": state,
            "agent_used": "error",
            "feedback": None,
            "error": str(e),
        }
