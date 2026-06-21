""""""

import os
import sys
import json
import uuid
import argparse
import traceback
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()



class C:
    """Terminal colors"""
    PASS = "\033[92m"
    FAIL = "\033[91m"
    INFO = "\033[94m"
    WARN = "\033[93m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    CYAN = "\033[96m"



results = {"passed": 0, "failed": 0, "errors": []}


def header(title: str):
    print(f"\n{'='*70}")
    print(f"{C.BOLD}{C.CYAN}  {title}{C.RESET}")
    print(f"{'='*70}\n")


def test_result(test_name: str, passed: bool, detail: str = ""):
    if passed:
        results["passed"] += 1
        print(f"  {C.PASS}✅ PASS{C.RESET} — {test_name}")
    else:
        results["failed"] += 1
        results["errors"].append(test_name)
        print(f"  {C.FAIL}❌ FAIL{C.RESET} — {test_name}")
    if detail:
        print(f"         {C.DIM}{detail}{C.RESET}")


def test_section(name: str):
    print(f"\n  {C.INFO}{'─'*50}{C.RESET}")
    print(f"  {C.BOLD}{name}{C.RESET}")
    print(f"  {C.INFO}{'─'*50}{C.RESET}")


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

def test_tools():
    header("TEST 1: TOOLS — اختبار الأدوات")

    # ──────────────── Profile Tools ────────────────
    test_section("Profile Tools (tools/profile_tool.py)")

    from tools.profile_tool import (
        init_db, create_learner_profile, get_learner_profile,
        update_learner_level, add_weak_area, update_learning_goals,
    )

    # 1.1 init_db
    try:
        init_db()
        test_result("init_db() — إنشاء جدول learner_profiles", True)
    except Exception as e:
        test_result("init_db()", False, str(e))

    # 1.2 create_learner_profile
    test_id = f"test_{uuid.uuid4().hex[:6]}"
    try:
        result = create_learner_profile.invoke({
            "learner_id": test_id,
            "name": "Test Learner",
            "target_level": "B2",
            "learning_goals": json.dumps(["job interview", "technical writing"]),
            "preferred_topics": json.dumps(["AI", "cloud"]),
        })
        data = json.loads(result)
        passed = data["status"] == "success"
        test_result("create_learner_profile() — إنشاء بروفايل جديد", passed, f"ID: {test_id}")
    except Exception as e:
        test_result("create_learner_profile()", False, str(e))

    # 1.3 get_learner_profile
    try:
        result = get_learner_profile.invoke({"learner_id": test_id})
        data = json.loads(result)
        passed = data["status"] == "success" and data["profile"]["name"] == "Test Learner"
        test_result("get_learner_profile() — جلب البروفايل", passed,
                     f"Name: {data.get('profile', {}).get('name', 'N/A')}")
    except Exception as e:
        test_result("get_learner_profile()", False, str(e))

    # 1.4 update_learner_level
    try:
        result = update_learner_level.invoke({
            "learner_id": test_id,
            "new_level": "B1",
        })
        data = json.loads(result)
        passed = data["status"] == "success" and data["new_level"] == "B1"
        test_result("update_learner_level() — تحديث المستوى لـ B1", passed)
    except Exception as e:
        test_result("update_learner_level()", False, str(e))

    # 1.5 update_learner_level — invalid level
    try:
        result = update_learner_level.invoke({
            "learner_id": test_id,
            "new_level": "Z9",
        })
        data = json.loads(result)
        passed = data["status"] == "error"
        test_result("update_learner_level('Z9') — رفض مستوى غير صحيح", passed)
    except Exception as e:
        test_result("update_learner_level('Z9')", False, str(e))

    # 1.6 add_weak_area
    try:
        result = add_weak_area.invoke({
            "learner_id": test_id,
            "weakness": "past tense",
        })
        data = json.loads(result)
        passed = data["status"] == "success" and "past tense" in data["weak_areas"]
        test_result("add_weak_area() — إضافة نقطة ضعف", passed,
                     f"Weak areas: {data.get('weak_areas', [])}")
    except Exception as e:
        test_result("add_weak_area()", False, str(e))

    # 1.7 add_weak_area — duplicate check
    try:
        result = add_weak_area.invoke({
            "learner_id": test_id,
            "weakness": "past tense",
        })
        data = json.loads(result)
        count = data.get("weak_areas", []).count("past tense")
        passed = count == 1
        test_result("add_weak_area() — عدم تكرار نقطة ضعف موجودة", passed,
                     f"Count of 'past tense': {count}")
    except Exception as e:
        test_result("add_weak_area() duplicate", False, str(e))

    # 1.8 update_learning_goals
    try:
        new_goals = json.dumps(["IELTS preparation", "business email"])
        result = update_learning_goals.invoke({
            "learner_id": test_id,
            "goals": new_goals,
        })
        data = json.loads(result)
        passed = data["status"] == "success"
        test_result("update_learning_goals() — تحديث الأهداف", passed,
                     f"Goals: {data.get('goals', [])}")
    except Exception as e:
        test_result("update_learning_goals()", False, str(e))

    # 1.9 update_learning_goals — invalid JSON
    try:
        result = update_learning_goals.invoke({
            "learner_id": test_id,
            "goals": "not valid json",
        })
        data = json.loads(result)
        passed = data["status"] == "error"
        test_result("update_learning_goals('invalid') — رفض JSON غير صحيح", passed)
    except Exception as e:
        test_result("update_learning_goals('invalid')", False, str(e))

    # ──────────────── Progress Tools ────────────────
    test_section("Progress Tools (tools/progress_tool.py)")

    from tools.progress_tool import (
        init_progress_db, log_session, save_feedback_result,
        get_weekly_summary, get_recurring_mistakes, generate_next_steps,
    )

    # 1.10 init_progress_db
    try:
        init_progress_db()
        test_result("init_progress_db() — إنشاء جداول التقدم", True)
    except Exception as e:
        test_result("init_progress_db()", False, str(e))

    # 1.11 log_session
    session_id = f"session_{uuid.uuid4().hex[:6]}"
    try:
        result = log_session.invoke({
            "learner_id": test_id,
            "session_id": session_id,
            "session_type": "conversation",
            "duration_mins": 15,
        })
        data = json.loads(result)
        passed = data["status"] == "success"
        test_result("log_session() — تسجيل جلسة", passed, f"Session: {session_id}")
    except Exception as e:
        test_result("log_session()", False, str(e))

    # 1.12 save_feedback_result
    try:
        result = save_feedback_result.invoke({
            "learner_id": test_id,
            "session_id": session_id,
            "original_text": "I have went to office yesterday",
            "corrected_text": "I went to the office yesterday",
            "grammar_score": 5.0,
            "vocabulary_score": 6.0,
            "clarity_score": 7.0,
            "tone_score": 6.5,
            "job_readiness_score": 45.0,
            "mistakes": json.dumps(["past tense error", "missing article"]),
        })
        data = json.loads(result)
        passed = data["status"] == "success"
        test_result("save_feedback_result() — حفظ نتيجة Feedback", passed)
    except Exception as e:
        test_result("save_feedback_result()", False, str(e))

    # 1.13 get_weekly_summary
    try:
        result = get_weekly_summary.invoke({"learner_id": test_id})
        data = json.loads(result)
        passed = data["status"] == "success" and "summary" in data
        summary = data.get("summary", {})
        test_result("get_weekly_summary() — ملخص أسبوعي", passed,
                     f"Sessions: {summary.get('sessions_this_week', 0)}, "
                     f"Avg Grammar: {summary.get('avg_grammar_score', 0)}")
    except Exception as e:
        test_result("get_weekly_summary()", False, str(e))

    # 1.14 get_recurring_mistakes
    try:
        result = get_recurring_mistakes.invoke({
            "learner_id": test_id,
            "limit": 5,
        })
        data = json.loads(result)
        passed = data["status"] == "success"
        test_result("get_recurring_mistakes() — أخطاء متكررة", passed,
                     f"Mistakes: {data.get('recurring_mistakes', [])}")
    except Exception as e:
        test_result("get_recurring_mistakes()", False, str(e))

    # 1.15 generate_next_steps
    try:
        result = generate_next_steps.invoke({"learner_id": test_id})
        data = json.loads(result)
        passed = data["status"] == "success" and len(data.get("next_steps", [])) > 0
        test_result("generate_next_steps() — خطوات مقترحة", passed,
                     f"Steps: {data.get('next_steps', [])[:2]}")
    except Exception as e:
        test_result("generate_next_steps()", False, str(e))

    # ──────────────── Exercise Tools ────────────────
    test_section("Exercise Tools (tools/exercise_tool.py)")

    from tools.exercise_tool import (
        generate_interview_question, generate_grammar_exercise,
        generate_vocabulary_exercise, generate_email_writing_task,
    )

    for level in ["A1", "B1", "B2", "C1"]:
        try:
            result = generate_interview_question.invoke({
                "current_level": level,
                "topic": "general",
            })
            data = json.loads(result)
            passed = (data["status"] == "success" and
                      data["exercise"]["type"] == "interview_question" and
                      len(data["exercise"]["question"]) > 0)
            test_result(f"generate_interview_question(level={level})", passed,
                         f"Q: {data['exercise']['question'][:60]}...")
        except Exception as e:
            test_result(f"generate_interview_question(level={level})", False, str(e))

    # 1.17 generate_grammar_exercise
    for level in ["A1", "B1", "B2"]:
        try:
            result = generate_grammar_exercise.invoke({
                "current_level": level,
                "weak_area": "tenses",
            })
            data = json.loads(result)
            passed = (data["status"] == "success" and
                      "question" in data["exercise"] and
                      "answer" in data["exercise"])
            test_result(f"generate_grammar_exercise(level={level})", passed,
                         f"Type: {data['exercise']['type']}")
        except Exception as e:
            test_result(f"generate_grammar_exercise(level={level})", False, str(e))

    # 1.18 generate_vocabulary_exercise
    for topic in ["AI", "cloud", "software", "data"]:
        try:
            result = generate_vocabulary_exercise.invoke({
                "current_level": "B1",
                "topic": topic,
            })
            data = json.loads(result)
            passed = (data["status"] == "success" and
                      len(data["exercise"]["words"]) > 0)
            test_result(f"generate_vocabulary_exercise(topic={topic})", passed,
                         f"Words: {data['exercise']['words'][:3]}")
        except Exception as e:
            test_result(f"generate_vocabulary_exercise(topic={topic})", False, str(e))

    # 1.19 generate_email_writing_task
    for scenario in ["project_update", "meeting_request", "follow_up"]:
        try:
            result = generate_email_writing_task.invoke({
                "current_level": "B2",
                "scenario": scenario,
            })
            data = json.loads(result)
            passed = (data["status"] == "success" and
                      data["exercise"]["type"] == "email_writing" and
                      len(data["exercise"]["task"]) > 0)
            test_result(f"generate_email_writing_task(scenario={scenario})", passed)
        except Exception as e:
            test_result(f"generate_email_writing_task(scenario={scenario})", False, str(e))


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

def test_agents():
    header("TEST 2: AGENTS — اختبار كل Agent مباشرة")

    from agents.state import AgentState, create_initial_state
    from agents.supervisor import supervisor_node, route_to_agent
    from agents.learning_agent import learning_agent_node
    from agents.conversation_agent import conversation_agent_node
    from agents.roleplay_agent import roleplay_agent_node
    from agents.feedback_agent import feedback_agent_node

    # ──────────────── State ────────────────
    test_section("State (agents/state.py)")

    # 2.1 create_initial_state
    try:
        state = create_initial_state(
            learner_id="test_001",
            user_input="Hello, I want to learn English",
        )
        passed = (
            state["user_input"] == "Hello, I want to learn English" and
            len(state["messages"]) == 1 and
            state["messages"][0]["role"] == "user" and
            state["next_agent"] is None and
            state["assessment_complete"] == False and
            state["session_ended"] == False
        )
        test_result("create_initial_state() — State أولي صحيح", passed,
                     f"Keys: {list(state.keys())}")
    except Exception as e:
        test_result("create_initial_state()", False, str(e))

    # 2.2 create_initial_state with profile
    try:
        profile = {
            "learner_id": "test_002",
            "name": "Ahmad",
            "current_level": "B1",
            "target_level": "B2",
            "learning_goals": ["job interview"],
            "weak_areas": ["grammar"],
            "preferred_topics": ["AI"],
            "sessions_completed": 5,
        }
        state = create_initial_state(
            learner_id="test_002",
            user_input="Hi",
            learner_profile=profile,
        )
        passed = (
            state["learner_profile"]["name"] == "Ahmad" and
            state["assessment_complete"] == True
        )
        test_result("create_initial_state(with_profile) — بروفايل موجود", passed,
                     f"assessment_complete: {state['assessment_complete']}")
    except Exception as e:
        test_result("create_initial_state(with_profile)", False, str(e))

    # ──────────────── Supervisor ────────────────
    test_section("Supervisor Agent (agents/supervisor.py)")

    try:
        state = create_initial_state(
            learner_id="test_003",
            user_input="Hello",
        )
        result = supervisor_node(state)
        next_agent = result.get("next_agent")
        reason = result.get("routing_reason", "")
        passed = next_agent in [
            "learning_agent", "conversation_agent",
            "roleplay_agent", "feedback_agent", "end"
        ]
        test_result("supervisor_node(new_user) — توجيه مستخدم جديد", passed,
                     f"→ {next_agent} | Reason: {reason[:80]}")
    except Exception as e:
        test_result("supervisor_node(new_user)", False, str(e))

    try:
        state = create_initial_state(
            learner_id="test_004",
            user_input="Hello",
        )
        state["current_session_type"] = "learning_agent"
        state["messages"].append({"role": "assistant", "content": "Hi! Let me assess your level."})
        result = supervisor_node(state)
        passed = result["next_agent"] == "end"
        test_result("supervisor_node(turn_guard) — إيقاف بعد رد Agent", passed,
                     f"→ {result['next_agent']} | {result.get('routing_reason', '')[:60]}")
    except Exception as e:
        test_result("supervisor_node(turn_guard)", False, str(e))

    # 2.5 route_to_agent
    try:
        state = {"next_agent": "roleplay_agent"}
        route = route_to_agent(state)
        passed = route == "roleplay_agent"
        test_result("route_to_agent() — routing function", passed, f"Route: {route}")
    except Exception as e:
        test_result("route_to_agent()", False, str(e))

    # 2.6 route_to_agent — fallback
    try:
        state = {"next_agent": None}
        route = route_to_agent(state)
        passed = route == "learning_agent"
        test_result("route_to_agent(None) — fallback لـ learning_agent", passed, f"Route: {route}")
    except Exception as e:
        test_result("route_to_agent(fallback)", False, str(e))

    # ──────────────── Learning Agent ────────────────
    test_section("Learning Agent (agents/learning_agent.py)")

    # 2.7 learning_agent_node
    try:
        state = create_initial_state(
            learner_id="test_005",
            user_input="I want to improve my English for job interviews",
        )
        result = learning_agent_node(state)

        messages = result.get("messages", [])
        has_assistant_reply = any(m["role"] == "assistant" for m in messages)
        correct_type = result.get("current_session_type") == "learning_agent"
        questions_tracked = "assessment_questions_asked" in result

        passed = has_assistant_reply and correct_type
        last_msg = messages[-1]["content"][:100] if messages else "N/A"
        test_result("learning_agent_node() — رد على رسالة تعليمية", passed,
                     f"Response: {last_msg}...")
        test_result("learning_agent_node() — session_type صحيح", correct_type,
                     f"Type: {result.get('current_session_type')}")
        test_result("learning_agent_node() — تتبع أسئلة التشخيص", questions_tracked,
                     f"Questions asked: {result.get('assessment_questions_asked', 'N/A')}")
    except Exception as e:
        test_result("learning_agent_node()", False, f"{str(e)}\n{traceback.format_exc()}")

    # ──────────────── Conversation Agent ────────────────
    test_section("Conversation Agent (agents/conversation_agent.py)")

    # 2.8 conversation_agent_node
    try:
        profile = {
            "learner_id": "test_006",
            "name": "Sara",
            "current_level": "B1",
            "target_level": "B2",
            "learning_goals": ["daily conversation"],
            "weak_areas": ["vocabulary"],
            "preferred_topics": ["AI", "software"],
            "sessions_completed": 3,
        }
        state = create_initial_state(
            learner_id="test_006",
            user_input="Let's talk about artificial intelligence and its impact on jobs",
            learner_profile=profile,
        )
        result = conversation_agent_node(state)

        messages = result.get("messages", [])
        has_reply = any(m["role"] == "assistant" for m in messages)
        correct_type = result.get("current_session_type") == "conversation_agent"

        last_msg = messages[-1]["content"][:100] if messages else "N/A"
        test_result("conversation_agent_node() — محادثة تقنية", has_reply,
                     f"Response: {last_msg}...")
        test_result("conversation_agent_node() — session_type صحيح", correct_type)
        test_result("conversation_agent_node() — تتبع الأخطاء", "session_mistakes" in result,
                     f"Mistakes: {result.get('session_mistakes', [])}")
    except Exception as e:
        test_result("conversation_agent_node()", False, f"{str(e)}\n{traceback.format_exc()}")

    # 2.9 extract_current_topic
    try:
        from agents.conversation_agent import extract_current_topic
        messages = [
            {"role": "user", "content": "I want to learn about machine learning"},
            {"role": "assistant", "content": "Great! Let's discuss AI concepts."},
        ]
        topic = extract_current_topic(messages)
        passed = "AI" in topic or "Machine" in topic
        test_result("extract_current_topic() — اكتشاف الموضوع", passed,
                     f"Topic: {topic}")

        topic_empty = extract_current_topic([])
        test_result("extract_current_topic([]) — قائمة فارغة", topic_empty == "general conversation")
    except Exception as e:
        test_result("extract_current_topic()", False, str(e))

    # ──────────────── Roleplay Agent ────────────────
    test_section("Roleplay Agent (agents/roleplay_agent.py)")

    # 2.10 roleplay_agent_node — job interview
    try:
        profile = {
            "learner_id": "test_007",
            "name": "Mohammed",
            "current_level": "B2",
            "target_level": "C1",
            "learning_goals": ["job interview"],
            "weak_areas": ["fluency"],
            "preferred_topics": ["software"],
            "sessions_completed": 7,
        }
        state = create_initial_state(
            learner_id="test_007",
            user_input="I want to practice a job interview",
            learner_profile=profile,
        )
        result = roleplay_agent_node(state)

        messages = result.get("messages", [])
        has_reply = any(m["role"] == "assistant" for m in messages)
        correct_type = result.get("current_session_type") == "roleplay_agent"
        scenario_set = result.get("roleplay_scenario") is not None

        last_msg = messages[-1]["content"][:100] if messages else "N/A"
        test_result("roleplay_agent_node(interview) — بدء مقابلة", has_reply,
                     f"Response: {last_msg}...")
        test_result("roleplay_agent_node() — session_type صحيح", correct_type)
        test_result("roleplay_agent_node() — تحديد السيناريو", scenario_set,
                     f"Scenario: {result.get('roleplay_scenario')}")
    except Exception as e:
        test_result("roleplay_agent_node(interview)", False, f"{str(e)}\n{traceback.format_exc()}")

    # 2.11 determine_scenario
    try:
        from agents.roleplay_agent import determine_scenario
        test_cases = [
            ("I want a job interview practice", "job_interview"),
            ("Let's do a sprint meeting simulation", "sprint_meeting"),
            ("Practice with a client call", "client_call"),
            ("Negotiate my salary", "salary_discussion"),
            ("Present my project", "project_presentation"),
            ("recruiter screening call", "recruiter_screening"),
        ]
        for input_text, expected in test_cases:
            mock_state = {"roleplay_scenario": None}
            result = determine_scenario(input_text, mock_state)
            passed = result == expected
            test_result(f"determine_scenario('{input_text[:30]}...')", passed,
                         f"Expected: {expected}, Got: {result}")
    except Exception as e:
        test_result("determine_scenario()", False, str(e))

    # ──────────────── Feedback Agent ────────────────
    test_section("Feedback Agent (agents/feedback_agent.py)")

    # 2.12 feedback_agent_node
    try:
        profile = {
            "learner_id": "test_008",
            "name": "Nora",
            "current_level": "B1",
            "target_level": "B2",
            "learning_goals": ["professional email"],
            "weak_areas": ["grammar", "articles"],
            "preferred_topics": ["data"],
            "sessions_completed": 4,
        }
        state = create_initial_state(
            learner_id="test_008",
            user_input="I have went to the meeting yesterday and I discuss about the new project with my team. We was very excited about it.",
            learner_profile=profile,
        )
        result = feedback_agent_node(state)

        messages = result.get("messages", [])
        has_reply = any(m["role"] == "assistant" for m in messages)
        correct_type = result.get("current_session_type") == "feedback_agent"
        has_feedback = result.get("last_feedback") is not None

        last_msg = messages[-1]["content"][:150] if messages else "N/A"
        test_result("feedback_agent_node() — تحليل نص بأخطاء", has_reply,
                     f"Response: {last_msg}...")
        test_result("feedback_agent_node() — session_type صحيح", correct_type)
        test_result("feedback_agent_node() — إنتاج FeedbackResult", has_feedback)

        if has_feedback:
            fb = result["last_feedback"]
            test_result("feedback_agent_node() — FeedbackResult يحتوي original_text",
                         fb.get("original_text") is not None)
            test_result("feedback_agent_node() — FeedbackResult يحتوي scores",
                         all(k in fb for k in ["grammar_score", "vocabulary_score",
                                               "clarity_score", "tone_score"]))
        test_result("feedback_agent_node() — RAG context موجود",
                     result.get("rag_context") is not None,
                     f"RAG: {str(result.get('rag_context', ''))[:80]}...")
    except Exception as e:
        test_result("feedback_agent_node()", False, f"{str(e)}\n{traceback.format_exc()}")

    # 2.13 RAG Functions
    test_section("RAG Functions (agents/feedback_agent.py)")
    try:
        from agents.feedback_agent import retrieve_context, search_grammar_rules
        context = retrieve_context("subject-verb agreement rules")
        passed = isinstance(context, str) and len(context) > 0
        test_result("retrieve_context() — بحث في Knowledge Base", passed,
                     f"Result: {context[:80]}...")
    except Exception as e:
        test_result("retrieve_context()", False, str(e))


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

def test_pipeline():
    header("TEST 3: FULL PIPELINE — الـ Graph الكامل")

    from agents import run_agent, create_graph
    from agents.state import create_initial_state
    from tools.profile_tool import init_db
    from tools.progress_tool import init_progress_db

    init_db()
    init_progress_db()

    # ──────────────── Graph Structure ────────────────
    test_section("Graph Structure")

    # 3.1 create_graph
    try:
        graph = create_graph()
        passed = graph is not None
        test_result("create_graph() — بناء الـ Graph", passed)
    except Exception as e:
        test_result("create_graph()", False, str(e))

    # ──────────────── Pipeline: New User ────────────────
    test_section("Pipeline: مستخدم جديد")

    learner_id = f"pipeline_{uuid.uuid4().hex[:6]}"

    try:
        result = run_agent(
            user_input="Hello, I want to start learning English for my tech career",
            learner_id=learner_id,
        )
        passed = (
            result.get("response") is not None and
            len(result["response"]) > 0 and
            result.get("agent_used") is not None and
            result.get("updated_state") is not None
        )
        test_result("run_agent(new_user) — أول رسالة", passed,
                     f"Agent: {result.get('agent_used')} | "
                     f"Routing: {result.get('routing_reason', '')[:60]}")
        print(f"\n  {C.DIM}  📝 Response: {result['response'][:120]}...{C.RESET}")

        state_1 = result.get("updated_state")
    except Exception as e:
        test_result("run_agent(new_user)", False, f"{str(e)}\n{traceback.format_exc()}")
        state_1 = None

    if state_1:
        try:
            result = run_agent(
                user_input="My level is intermediate and I want to prepare for job interviews",
                learner_id=learner_id,
                existing_state=state_1,
            )
            passed = (
                result.get("response") is not None and
                len(result.get("updated_state", {}).get("messages", [])) > len(
                    state_1.get("messages", []))
            )
            test_result("run_agent(follow_up) — متابعة المحادثة", passed,
                         f"Agent: {result.get('agent_used')} | "
                         f"Messages count: {len(result.get('updated_state', {}).get('messages', []))}")
            print(f"\n  {C.DIM}  📝 Response: {result['response'][:120]}...{C.RESET}")

            state_2 = result.get("updated_state")
        except Exception as e:
            test_result("run_agent(follow_up)", False, str(e))
            state_2 = None
    else:
        state_2 = None

    # ──────────────── Pipeline: Conversation ────────────────
    test_section("Pipeline: Conversation Agent")

    try:
        profile = {
            "learner_id": "pipe_conv",
            "name": "Test User",
            "current_level": "B1",
            "target_level": "B2",
            "learning_goals": ["conversation"],
            "weak_areas": ["vocabulary"],
            "preferred_topics": ["AI"],
            "sessions_completed": 2,
        }
        state = create_initial_state("pipe_conv", "Let's discuss cloud computing", profile)
        result = run_agent(
            user_input="Let's discuss cloud computing and DevOps",
            learner_id="pipe_conv",
            existing_state=state,
        )
        passed = result.get("response") is not None and result.get("agent_used") is not None
        test_result("run_agent(conversation) — محادثة تقنية", passed,
                     f"Agent: {result.get('agent_used')}")
        print(f"\n  {C.DIM}  📝 Response: {result['response'][:120]}...{C.RESET}")
    except Exception as e:
        test_result("run_agent(conversation)", False, str(e))

    # ──────────────── Pipeline: Roleplay ────────────────
    test_section("Pipeline: Roleplay Agent")

    # 3.5 roleplay
    try:
        profile = {
            "learner_id": "pipe_role",
            "name": "Ali",
            "current_level": "B2",
            "target_level": "C1",
            "learning_goals": ["job interview"],
            "weak_areas": ["fluency"],
            "preferred_topics": ["software"],
            "sessions_completed": 5,
        }
        state = create_initial_state("pipe_role", "start interview", profile)
        result = run_agent(
            user_input="I want to practice a job interview simulation",
            learner_id="pipe_role",
            existing_state=state,
        )
        passed = result.get("response") is not None
        test_result("run_agent(roleplay) — محاكاة مقابلة", passed,
                     f"Agent: {result.get('agent_used')}")
        print(f"\n  {C.DIM}  📝 Response: {result['response'][:120]}...{C.RESET}")
    except Exception as e:
        test_result("run_agent(roleplay)", False, str(e))

    # ──────────────── Pipeline: Feedback ────────────────
    test_section("Pipeline: Feedback Agent")

    # 3.6 feedback
    try:
        profile = {
            "learner_id": "pipe_feed",
            "name": "Fatima",
            "current_level": "B1",
            "target_level": "B2",
            "learning_goals": ["writing"],
            "weak_areas": ["grammar"],
            "preferred_topics": ["data"],
            "sessions_completed": 3,
        }
        state = create_initial_state("pipe_feed", "check text", profile)
        result = run_agent(
            user_input="Please check this text: I have went to Dubai last week and I meet with my manager. He say the project are going good.",
            learner_id="pipe_feed",
            existing_state=state,
        )
        passed = result.get("response") is not None
        has_feedback = result.get("feedback") is not None
        test_result("run_agent(feedback) — تقييم نص", passed,
                     f"Agent: {result.get('agent_used')}")
        test_result("run_agent(feedback) — نتيجة Feedback موجودة", has_feedback)
        print(f"\n  {C.DIM}  📝 Response: {result['response'][:150]}...{C.RESET}")

        if has_feedback:
            fb = result["feedback"]
            print(f"  {C.DIM}  📊 Grammar: {fb.get('grammar_score')}/10 | "
                  f"Vocab: {fb.get('vocabulary_score')}/10 | "
                  f"Readiness: {fb.get('job_readiness_score')}/100{C.RESET}")
    except Exception as e:
        test_result("run_agent(feedback)", False, str(e))

    # ──────────────── Pipeline: Error Handling ────────────────
    test_section("Pipeline: Error Handling")

    try:
        result = run_agent(
            user_input="",
            learner_id="pipe_empty",
        )
        passed = result.get("response") is not None
        test_result("run_agent('') — رسالة فارغة", passed,
                     f"Agent: {result.get('agent_used')}")
    except Exception as e:
        test_result("run_agent('')", False, str(e))

    # 3.8 end session
    try:
        result = run_agent(
            user_input="bye, goodbye, I want to stop",
            learner_id="pipe_end",
        )
        passed = result.get("response") is not None
        test_result("run_agent('bye') — إنهاء الجلسة", passed,
                     f"Agent: {result.get('agent_used')}")
    except Exception as e:
        test_result("run_agent('bye')", False, str(e))


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

def print_summary():
    """"""
    total = results["passed"] + results["failed"]
    print(f"\n{'='*70}")
    print(f"{C.BOLD}  📊 TEST SUMMARY{C.RESET}")
    print(f"{'='*70}")
    print(f"  Total:  {total}")
    print(f"  {C.PASS}Passed: {results['passed']}{C.RESET}")
    print(f"  {C.FAIL}Failed: {results['failed']}{C.RESET}")

    if results["errors"]:
        print(f"\n  {C.FAIL}Failed Tests:{C.RESET}")
        for err in results["errors"]:
            print(f"    ✗ {err}")

    rate = (results["passed"] / total * 100) if total > 0 else 0
    color = C.PASS if rate >= 80 else C.WARN if rate >= 50 else C.FAIL
    print(f"\n  {color}{C.BOLD}Pass Rate: {rate:.0f}%{C.RESET}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    # Ensure stdout and stderr support UTF-8 encoding on Windows console
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="FluentTech — Test Suite — اختبار شامل للـ Agents والـ Tools"
    )
    parser.add_argument("--tools", action="store_true", help="اختبار الـ Tools فقط")
    parser.add_argument("--agents", action="store_true", help="اختبار الـ Agents فقط")
    parser.add_argument("--pipeline", action="store_true", help="اختبار الـ Pipeline الكامل فقط")
    args = parser.parse_args()

    print(f"\n{C.BOLD}{C.CYAN}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   🧪  FluentTech — Comprehensive Test Suite                ║")
    print("║   📅  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "                                ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    run_all = not (args.tools or args.agents or args.pipeline)

    if run_all or args.tools:
        test_tools()

    if run_all or args.agents:
        test_agents()

    if run_all or args.pipeline:
        test_pipeline()

    print_summary()
