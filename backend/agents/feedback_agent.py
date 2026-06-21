""""""

import os
import json
import re
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.agents import AgentExecutor, create_react_agent
# from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.tools import tool
from agents.state import AgentState, FeedbackResult
from agents.llm_config import get_llm
from tools.progress_tool import save_feedback_result



from rag.retriever import retrieve

def retrieve_context(query: str, n_results: int = 3) -> str:
    """"""
    try:
        results = retrieve(query, top_k=n_results)
        
        if not results:
            return "No relevant grammar rules found."

        context_parts = []
        for res in results:
            source = res.get("source_file", "Knowledge Base")
            context_parts.append(f"[{source}]\n{res['content']}")

        return "\n\n---\n\n".join(context_parts)

    except Exception as e:
        print(f"RAG not available: {e}")
        return "Grammar reference not available. Using general knowledge."



BUILTIN_GRAMMAR_RULES = {
    "subject-verb agreement": (
        "Subject-verb agreement: The verb must agree with its subject in number. "
        "Singular subjects take singular verbs (he goes), "
        "plural subjects take plural verbs (they go)."
    ),
    "tenses": (
        "Common tense errors: Use Simple Past for completed actions (I went, not I have went). "
        "Use Present Perfect for actions with current relevance (I have finished). "
        "Don't mix tenses within the same sentence."
    ),
    "articles": (
        "Articles (a/an/the): Use 'a' before consonant sounds, 'an' before vowel sounds. "
        "Use 'the' for specific/known things. "
        "Arabic speakers often omit articles — pay special attention."
    ),
    "prepositions": (
        "Common preposition errors by Arabic speakers: "
        "'depend on' (not 'depend from'), 'interested in' (not 'interested with'), "
        "'responsible for' (not 'responsible on')."
    ),
}


# ─── RAG Tools ──────────────────────────────────────────────────────────────

@tool
def search_grammar_rules(query: str) -> str:
    """Search for grammar rules in the knowledge base."""
    context = retrieve_context(query)

    if "not available" in context or "error" in context.lower():
        query_lower = query.lower()
        for topic, rule in BUILTIN_GRAMMAR_RULES.items():
            if any(kw in query_lower for kw in topic.split()):
                return f"[Built-in Rule]\n{rule}"
        return context

    return context


@tool
def search_interview_examples(query: str) -> str:
    """Search for interview examples in the knowledge base."""
    context = retrieve_context(f"interview answer example: {query}")
    return context


FEEDBACK_TOOLS = [search_grammar_rules, search_interview_examples]



from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

FEEDBACK_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert English evaluator for Saudi tech learners preparing for careers in technology.

Learner context:
- Name: {learner_name}
- Current CEFR Level: {current_level}
- Learning goals: {learning_goals}
- Known weak areas: {weak_areas}

Conversation Summary (previous context):
{context_summary}

EVALUATION PROTOCOL:
1. First, use search_grammar_rules to find relevant rules for any errors you notice
2. If this is interview text, use search_interview_examples for comparison
3. Then write your complete evaluation

OUTPUT FORMAT (use EXACTLY this structure — the system parses these headers):

## ORIGINAL_TEXT
[quote the original text exactly]

## CORRECTED_TEXT
[the corrected version]

## CORRECTIONS
[For each correction on a new line: "- Error -> Fix: explanation"]

## SCORES
- Grammar Accuracy: X/10
- Vocabulary Range: X/10
- Clarity & Structure: X/10
- Professional Tone: X/10

## JOB_READINESS
Score: XX/100
[Brief justification]

## SUGGESTIONS
1. [Specific, actionable suggestion]
2. [Specific, actionable suggestion]
3. [Specific, actionable suggestion]

## EXCELLENT_VERSION
[Show what a C1-level version would look like]
"""),
    ("human", "Text to evaluate: {input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


# ─── Score Parsing ──────────────────────────────────────────────────────────

def _parse_scores(response: str) -> dict:
    """"""
    scores = {
        "grammar_score": 0.0,
        "vocabulary_score": 0.0,
        "clarity_score": 0.0,
        "tone_score": 0.0,
        "job_readiness_score": 0.0,
    }

    patterns = {
        "grammar_score": r"(?:Grammar|Grammar Accuracy|grammar)[^\d]*(\d+\.?\d*)(?:\s*(?:/|out of)?\s*10)?",
        "vocabulary_score": r"(?:Vocabulary|Vocabulary Range|vocabulary)[^\d]*(\d+\.?\d*)(?:\s*(?:/|out of)?\s*10)?",
        "clarity_score": r"(?:Clarity|Clarity & Structure|Clarity and Structure|clarity)[^\d]*(\d+\.?\d*)(?:\s*(?:/|out of)?\s*10)?",
        "tone_score": r"(?:Tone|Professional Tone|tone)[^\d]*(\d+\.?\d*)(?:\s*(?:/|out of)?\s*10)?",
        "job_readiness_score": r"(?:Job Readiness|JOB_READINESS|Score)[^\d]*(\d+\.?\d*)(?:\s*(?:/|out of)?\s*100)?",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            try:
                scores[key] = float(match.group(1))
            except ValueError:
                pass

    return scores


def _parse_section(response: str, section: str) -> str:
    """"""
    # Allow #, ##, or ###, optional asterisks, and optional colon
    pattern = rf"(?:#+|\*\*)\s*(?:{section})[:\*]*\s*\n(.*?)(?=\n(?:#+|\*\*)[A-Z]|\Z)"
    match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _parse_corrections(response: str) -> list:
    """"""
    corrections_text = _parse_section(response, "CORRECTIONS")
    if not corrections_text:
        return []

    corrections = []
    for line in corrections_text.split("\n"):
        line = line.strip()
        if line.startswith("-") and "->" in line:
            corrections.append(line[1:].strip())
        elif line.startswith("-"):
            corrections.append(line[1:].strip())

    return corrections


def _parse_suggestions(response: str) -> list:
    """"""
    suggestions_text = _parse_section(response, "SUGGESTIONS")
    if not suggestions_text:
        return []

    suggestions = []
    for line in suggestions_text.split("\n"):
        line = line.strip()
        if re.match(r"^\d+\.", line):
            suggestions.append(re.sub(r"^\d+\.\s*", "", line))
        elif line.startswith("-"):
            suggestions.append(line[1:].strip())

    return suggestions



def feedback_agent_node(state: AgentState) -> AgentState:
    """"""
    profile = state.get("learner_profile", {})
    user_input = state.get("user_input", "")
    context_summary = state.get("context_summary", "No previous context.")

    current_level = profile.get("current_level", "B1") if profile else "B1"

    rag_context = retrieve_context(
        f"grammar rules for level {current_level} common mistakes"
    )

    try:
        llm = get_llm("feedback")

        all_tools = FEEDBACK_TOOLS + [save_feedback_result]

        from langchain.agents import create_tool_calling_agent

        agent = create_tool_calling_agent(
            llm=llm,
            tools=all_tools,
            prompt=FEEDBACK_AGENT_PROMPT,
        )

        executor = AgentExecutor(
            agent=agent,
            tools=all_tools,
            verbose=True,
            max_iterations=6,
            handle_parsing_errors=True,
        )

        result = executor.invoke({
            "input": user_input,
            "learner_name": profile.get("name", "Learner") if profile else "Learner",
            "current_level": current_level,
            "learning_goals": profile.get("learning_goals", []) if profile else [],
            "weak_areas": profile.get("weak_areas", []) if profile else [],
            "context_summary": context_summary,
        })

        agent_response = result.get("output", "I could not evaluate this text. Please try again.")

        # ─── Structured Parsing ─────────────────────────────────────────
        scores = _parse_scores(agent_response)
        corrected_text = _parse_section(agent_response, "CORRECTED_TEXT")
        corrections = _parse_corrections(agent_response)
        suggestions = _parse_suggestions(agent_response)

        feedback_result: FeedbackResult = {
            "original_text": user_input,
            "corrected_text": corrected_text,
            "grammar_score": scores["grammar_score"],
            "vocabulary_score": scores["vocabulary_score"],
            "clarity_score": scores["clarity_score"],
            "tone_score": scores["tone_score"],
            "job_readiness_score": scores["job_readiness_score"],
            "corrections": corrections,
            "suggestions": suggestions,
            "rag_sources": ["knowledge_base/grammar_rules.md"],
        }

        neat_response = f"🎯 **Excellent effort! Here is your technical evaluation:**\n\n"
        neat_response += f"**Corrected Text:**\n{corrected_text}\n\n**Corrections:**\n"
        for c in corrections:
            neat_response += f"- {c}\n"
        
        neat_response += f"\n📊 **Scores:**\n- Grammar: {scores['grammar_score']}/10\n- Vocabulary: {scores['vocabulary_score']}/10\n- Clarity: {scores['clarity_score']}/10\n- Professionalism: {scores['tone_score']}/10\n"
        
        if suggestions:
            neat_response += f"\n💡 **Pro Tips for Improvement:**\n"
            for s in suggestions:
                neat_response += f"- {s}\n"
                
        agent_response = neat_response

    except Exception as e:
        import traceback
        print(f"Error in feedback_agent_node: {e}")
        traceback.print_exc()
        agent_response = (
            "I encountered an issue analyzing your text. "
            "Please share what you'd like me to evaluate and I'll review it."
        )
        feedback_result = None
        rag_context = ""

    messages = list(state.get("messages", []))
    messages.append({"role": "assistant", "content": agent_response})

    return {
        **state,
        "messages": messages,
        "current_session_type": "feedback_agent",
        "last_feedback": feedback_result,
        "rag_context": rag_context,
        "current_topic": "Writing Feedback & Evaluation",
        "messages_since_last_summary": state.get("messages_since_last_summary", 0) + 1,
        "next_agent": None,
    }
