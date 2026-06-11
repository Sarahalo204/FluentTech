"""
agents/feedback_agent.py
-------------------------
Feedback & Evaluation Agent — المقيّم الذكي.

مسؤولياته:
1. تحليل نص المستخدم على 4 معايير
2. تصحيح الأخطاء مع شرح تفصيلي
3. توليد نسخة محسّنة من النص
4. حساب Job Readiness Score
5. استخدام RAG لسحب قواعد Grammar وقوالب مهنية
6. استخراج Scores بشكل structured من رد الـ LLM

لماذا RAG مهم هنا؟
- بدون RAG: الـ LLM يعطي تصحيحات عامة من تدريبه فقط
- مع RAG: التصحيحات مبنية على قواعد CEFR محددة وأمثلة مثبتة
"""

import os
import json
import re
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.agents import AgentExecutor, create_react_agent
# from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.tools import tool
import chromadb

from agents.state import AgentState, FeedbackResult
from agents.llm_config import get_llm
from tools.progress_tool import save_feedback_result


# ─── إعداد الـ RAG ──────────────────────────────────────────────────────────

def get_rag_retriever():
    """
    يُنشئ Retriever يبحث في الـ ChromaDB.

    لماذا BAAI/bge-small-en-v1.5 للـ Embeddings؟
    - مجاني ويشتغل locally
    - رقم 1 في MTEB Leaderboard للـ Small Models
    - سريع ومناسب لحجم Knowledge Base هذا المشروع
    """
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},
        )

        chroma_client = chromadb.PersistentClient(
            path=os.getenv("CHROMA_PATH", "./rag/chroma_store")
        )

        collection = chroma_client.get_collection("edulingo_knowledge")
        return collection, embeddings

    except Exception as e:
        print(f"RAG not available: {e}")
        return None, None


def retrieve_context(query: str, n_results: int = 3) -> str:
    """
    يبحث في الـ Knowledge Base ويُرجع السياق الأكثر صلة.

    Args:
        query: ما يريد الـ Agent البحث عنه
        n_results: عدد النتائج المطلوبة
    """
    collection, embeddings = get_rag_retriever()

    if not collection or not embeddings:
        return "Grammar reference not available. Using general knowledge."

    try:
        query_embedding = embeddings.embed_query(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas"]
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            return "No relevant grammar rules found."

        context_parts = []
        for doc, meta in zip(documents, metadatas):
            source = meta.get("source", "Knowledge Base")
            context_parts.append(f"[{source}]\n{doc}")

        return "\n\n---\n\n".join(context_parts)

    except Exception as e:
        return f"RAG retrieval error: {str(e)}"


# ─── Built-in Grammar Rules (Fallback عند فشل RAG) ─────────────────────────

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
    """
    يبحث في قاعدة المعرفة عن قواعد Grammar أو قوالب مهنية.

    متى يستدعيها الـ Agent؟
    - قبل تصحيح خطأ Grammar معين
    - عند الحاجة لمثال على جملة مهنية صحيحة
    - للتحقق من قاعدة CEFR معينة

    Args:
        query: وصف الخطأ أو القاعدة المطلوبة
    """
    context = retrieve_context(query)

    # Fallback: لو الـ RAG فاضي، نستخدم القواعد المدمجة
    if "not available" in context or "error" in context.lower():
        query_lower = query.lower()
        for topic, rule in BUILTIN_GRAMMAR_RULES.items():
            if any(kw in query_lower for kw in topic.split()):
                return f"[Built-in Rule]\n{rule}"
        return context

    return context


@tool
def search_interview_examples(query: str) -> str:
    """
    يبحث عن أمثلة إجابات مقابلات من الـ Knowledge Base.

    Args:
        query: وصف السؤال أو الموضوع
    """
    context = retrieve_context(f"interview answer example: {query}")
    return context


FEEDBACK_TOOLS = [search_grammar_rules, search_interview_examples]


# ─── Prompt الـ Feedback Agent ───────────────────────────────────────────────

FEEDBACK_AGENT_PROMPT = PromptTemplate.from_template("""You are an expert English evaluator for Saudi tech learners preparing for careers in technology.

Learner context:
- Name: {learner_name}
- Current CEFR Level: {current_level}
- Learning goals: {learning_goals}
- Known weak areas: {weak_areas}

Conversation Summary (previous context):
{context_summary}

Available tools (use BEFORE writing feedback):
{tools}

Tool names: {tool_names}

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

Text to evaluate: {input}

Thought: What errors do I see? What grammar rules should I search for?
Action: [tool if needed]
Action Input: [query]
Observation: [result]
... 
Final Answer: [Complete evaluation in the format above]

{agent_scratchpad}""")


# ─── Score Parsing ──────────────────────────────────────────────────────────

def _parse_scores(response: str) -> dict:
    """
    يستخرج الـ Scores من رد الـ Agent بشكل أقوى.

    يدعم أنماط متعددة:
    - "Grammar Accuracy: 7/10"
    - "Grammar Accuracy: 7.5/10"
    - "Grammar: 7 / 10"
    """
    scores = {
        "grammar_score": 0.0,
        "vocabulary_score": 0.0,
        "clarity_score": 0.0,
        "tone_score": 0.0,
        "job_readiness_score": 0.0,
    }

    patterns = {
        "grammar_score": r"(?:Grammar|Grammar Accuracy)[:\s]*(\d+\.?\d*)\s*/\s*10",
        "vocabulary_score": r"(?:Vocabulary|Vocabulary Range)[:\s]*(\d+\.?\d*)\s*/\s*10",
        "clarity_score": r"(?:Clarity|Clarity & Structure|Clarity and Structure)[:\s]*(\d+\.?\d*)\s*/\s*10",
        "tone_score": r"(?:Tone|Professional Tone)[:\s]*(\d+\.?\d*)\s*/\s*10",
        "job_readiness_score": r"(?:Job Readiness|JOB_READINESS|Score)[:\s]*(\d+\.?\d*)\s*/\s*100",
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
    """
    يستخرج محتوى section معين من رد الـ Agent.

    Args:
        response: رد الـ Agent الكامل
        section: اسم الـ section (مثال: "CORRECTED_TEXT")
    """
    pattern = rf"##\s*{section}\s*\n(.*?)(?=##|\Z)"
    match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _parse_corrections(response: str) -> list:
    """يستخرج قائمة التصحيحات من رد الـ Agent."""
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
    """يستخرج قائمة الاقتراحات من رد الـ Agent."""
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


# ─── الـ Agent Node ─────────────────────────────────────────────────────────

def feedback_agent_node(state: AgentState) -> AgentState:
    """
    Feedback & Evaluation Agent Node.

    ما الذي يجعله مختلفاً؟
    1. يستخدم RAG قبل التقييم — تصحيحاته مبنية على مصادر
    2. يُنتج تقييم شامل بتنسيق محدد
    3. يحفظ النتائج في DB عبر save_feedback_result Tool
    4. Structured score parsing بـ regex
    5. يستخدم context_summary للسياق

    الـ RAG Flow:
    User Text → search_grammar_rules → Grammar Context → LLM → Structured Feedback
    """
    profile = state.get("learner_profile", {})
    user_input = state.get("user_input", "")
    context_summary = state.get("context_summary", "No previous context.")

    current_level = profile.get("current_level", "B1") if profile else "B1"

    # جلب سياق RAG مسبقاً (لتضمينه في الـ State)
    rag_context = retrieve_context(
        f"grammar rules for level {current_level} common mistakes"
    )

    try:
        llm = get_llm("feedback")

        # الـ Tools تشمل RAG Tools + Progress Tool لحفظ النتائج
        all_tools = FEEDBACK_TOOLS + [save_feedback_result]

        agent = create_react_agent(
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
