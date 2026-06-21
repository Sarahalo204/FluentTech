""""""

import os
import json
import re
from pydantic import BaseModel, Field
from typing import List
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

Recent Conversation History:
{conversation_history}

EVALUATION PROTOCOL:
You handle TWO types of inputs:
Type A: The user submits text for correction (e.g., "check this: X", "is this correct: X", or just typing a sentence).
Type B: The user asks a question about English grammar, your previous feedback, or a language rule (e.g., "why did you correct this?", "explain past simple").

FOR TYPE A (Correction):
1. Extract ONLY the target text that needs checking. IGNORE introductory phrases like "check my sentence:", "ok, I want you to review:", etc.
2. Use search_grammar_rules to find relevant rules for any errors.
3. Write your evaluation using EXACTLY this format (the system parses these headers):

## ORIGINAL_TEXT
[quote ONLY the target text, ignoring conversational filler]

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

FOR TYPE B (Question/Explanation):
1. Use search_grammar_rules if needed to find the answer.
2. Answer the user's question clearly, concisely, and with examples.
3. DO NOT output the ## ORIGINAL_TEXT or ## SCORES headers. Just provide a helpful and conversational explanation.
"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


# ─── Score Parsing ──────────────────────────────────────────────────────────

class FeedbackExtraction(BaseModel):
    corrected_text: str = Field(description="The corrected version of the user's text.")
    grammar_score: float = Field(description="Grammar Accuracy score from 0.0 to 10.0.")
    vocabulary_score: float = Field(description="Vocabulary Range score from 0.0 to 10.0.")
    clarity_score: float = Field(description="Clarity & Structure score from 0.0 to 10.0.")
    tone_score: float = Field(description="Professional Tone score from 0.0 to 10.0.")
    job_readiness_score: float = Field(description="Job Readiness score from 0.0 to 100.0.")
    corrections: List[str] = Field(description="List of specific corrections made.")
    suggestions: List[str] = Field(description="List of actionable suggestions for improvement.")

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

        conversation_history = "\n".join([
            f"  {m['role'].upper()}: {m['content'][:800]}"
            for m in state.get("messages", [])[-6:]
        ])

        result = executor.invoke({
            "input": user_input,
            "learner_name": profile.get("name", "Learner") if profile else "Learner",
            "current_level": current_level,
            "learning_goals": profile.get("learning_goals", []) if profile else [],
            "weak_areas": profile.get("weak_areas", []) if profile else [],
            "context_summary": context_summary,
            "conversation_history": conversation_history,
        })

        agent_response = result.get("output", "I could not evaluate this text. Please try again.")

        # ─── Structured Parsing ─────────────────────────────────────────
        if "## CORRECTED_TEXT" in agent_response or "## ORIGINAL_TEXT" in agent_response:
            try:
                extractor = llm.with_structured_output(FeedbackExtraction)
                extracted: FeedbackExtraction = extractor.invoke(f"Extract the feedback data from the following evaluation:\n\n{agent_response}")
                
                feedback_result: FeedbackResult = {
                    "original_text": user_input,
                    "corrected_text": extracted.corrected_text,
                    "grammar_score": extracted.grammar_score,
                    "vocabulary_score": extracted.vocabulary_score,
                    "clarity_score": extracted.clarity_score,
                    "tone_score": extracted.tone_score,
                    "job_readiness_score": extracted.job_readiness_score,
                    "corrections": extracted.corrections,
                    "suggestions": extracted.suggestions,
                    "rag_sources": ["knowledge_base/grammar_rules.md"],
                }
            except Exception as e:
                print(f"Error extracting feedback structured output: {e}")
                feedback_result = None

            if feedback_result:
                # Explicitly save feedback result to database
                learner_id = profile.get("learner_id", "unknown") if profile else "unknown"
                session_id = state.get("session_id", "unknown_session")
                try:
                    import json
                    save_feedback_result.invoke({
                        "learner_id": learner_id,
                        "session_id": session_id,
                        "original_text": feedback_result["original_text"],
                        "corrected_text": feedback_result["corrected_text"],
                        "grammar_score": feedback_result["grammar_score"],
                        "vocabulary_score": feedback_result["vocabulary_score"],
                        "clarity_score": feedback_result["clarity_score"],
                        "tone_score": feedback_result["tone_score"],
                        "job_readiness_score": feedback_result["job_readiness_score"],
                        "mistakes": json.dumps(feedback_result["corrections"])
                    })
                except Exception as db_e:
                    print(f"Error saving feedback to db: {db_e}")

                neat_response = f"🎯 **Excellent effort! Here is your technical evaluation:**\n\n"
                neat_response += f"**Corrected Text:**\n{extracted.corrected_text}\n\n**Corrections:**\n"
                for c in extracted.corrections:
                    neat_response += f"- {c}\n"
                
                neat_response += f"\n📊 **Scores:**\n- Grammar: {extracted.grammar_score}/10\n- Vocabulary: {extracted.vocabulary_score}/10\n- Clarity: {extracted.clarity_score}/10\n- Professionalism: {extracted.tone_score}/10\n- 🎯 Job Readiness: {extracted.job_readiness_score}/100\n"
                
                if extracted.suggestions:
                    neat_response += f"\n💡 **Suggestions:**\n"
                    for s in extracted.suggestions:
                        neat_response += f"- {s}\n"
                        
                agent_response = neat_response
            
        else:
            # It's a conversational answer (Type B)
            feedback_result = None

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
