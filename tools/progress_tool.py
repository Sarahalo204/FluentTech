"""
tools/progress_tool.py
----------------------
أداة تتبع التقدم — يستخدمها Learning & Progress Agent.

تمت الترقية إلى Supabase (PostgreSQL).
"""

import json
import os
from datetime import datetime, timedelta
from langchain.tools import tool
from supabase import create_client, Client


SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def init_progress_db():
    """
    Since we use Supabase, table creation is handled via SQL script.
    This function just verifies connection.
    """
    if SUPABASE_URL:
        get_supabase()


@tool
def log_session(
    learner_id: str,
    session_id: str,
    session_type: str,
    duration_mins: int = 0
) -> str:
    """
    يُسجِّل جلسة مكتملة في قاعدة البيانات Supabase.
    """
    try:
        supabase = get_supabase()
        now = datetime.utcnow().isoformat()

        # Log session
        session_data = {
            "session_id": session_id,
            "learner_id": learner_id,
            "session_type": session_type,
            "duration_mins": duration_mins,
            "created_at": now
        }
        supabase.table("sessions").insert(session_data).execute()

        # Increment sessions_completed in profile
        profile_res = supabase.table("learner_profiles").select("sessions_completed").eq("learner_id", learner_id).execute()
        if profile_res.data:
            current_count = profile_res.data[0].get("sessions_completed", 0)
            supabase.table("learner_profiles").update({
                "sessions_completed": current_count + 1
            }).eq("learner_id", learner_id).execute()

        return json.dumps({
            "status": "success",
            "message": f"Session {session_id} logged successfully"
        })

    except Exception as e:
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    learner_id TEXT,
                    session_type TEXT,
                    duration_mins INTEGER,
                    created_at TEXT
                )
            """)
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO sessions (session_id, learner_id, session_type, duration_mins, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    session_type=excluded.session_type,
                    duration_mins=excluded.duration_mins,
                    created_at=excluded.created_at
            """, (session_id, learner_id, session_type, duration_mins, now))
            
            cursor.execute("UPDATE learner_profiles SET sessions_completed = sessions_completed + 1 WHERE learner_id = ?", (learner_id,))
            conn.commit()
            conn.close()
            return json.dumps({
                "status": "success",
                "message": f"Session {session_id} logged successfully (SQLite Fallback)"
            })
        except Exception as sqle:
            return json.dumps({"status": "error", "message": f"Supabase error: {e}. SQLite error: {sqle}"})


@tool
def save_feedback_result(
    learner_id: str,
    session_id: str,
    original_text: str,
    corrected_text: str,
    grammar_score: float,
    vocabulary_score: float,
    clarity_score: float,
    tone_score: float,
    job_readiness_score: float,
    mistakes: str  # JSON array string
) -> str:
    """
    يحفظ نتيجة الـ Feedback في قاعدة بيانات Supabase.
    """
    try:
        parsed_mistakes = json.loads(mistakes)
    except Exception:
        parsed_mistakes = []

    try:
        supabase = get_supabase()
        data = {
            "learner_id": learner_id,
            "session_id": session_id,
            "grammar_score": grammar_score,
            "vocabulary_score": vocabulary_score,
            "clarity_score": clarity_score,
            "job_readiness_score": job_readiness_score,
            "corrections": parsed_mistakes,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("feedback_history").insert(data).execute()

        return json.dumps({"status": "success", "message": "Feedback saved"})

    except Exception as e:
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    learner_id TEXT,
                    session_id TEXT,
                    grammar_score REAL,
                    vocabulary_score REAL,
                    clarity_score REAL,
                    job_readiness_score REAL,
                    corrections TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute("""
                INSERT INTO feedback_history (learner_id, session_id, grammar_score, vocabulary_score, clarity_score, job_readiness_score, corrections, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (learner_id, session_id, grammar_score, vocabulary_score, clarity_score, job_readiness_score, json.dumps(parsed_mistakes), datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "message": "Feedback saved (SQLite Fallback)"})
        except Exception as sqle:
            return json.dumps({"status": "error", "message": f"Supabase error: {e}. SQLite error: {sqle}"})


@tool
def get_weekly_summary(learner_id: str) -> str:
    """
    يُنشئ ملخص أسبوعي للمستخدم من Supabase.
    """
    try:
        supabase = get_supabase()
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

        # جلسات الأسبوع
        sessions_res = supabase.table("sessions").select("id", count="exact") \
            .eq("learner_id", learner_id) \
            .gte("created_at", week_ago).execute()
        
        sessions_count = sessions_res.count if sessions_res.count is not None else 0

        # درجات الأسبوع
        feedback_res = supabase.table("feedback_history").select("*") \
            .eq("learner_id", learner_id) \
            .gte("created_at", week_ago).execute()
        
        feedbacks = feedback_res.data
        
        if feedbacks:
            avg_grammar = sum(f.get("grammar_score", 0) for f in feedbacks) / len(feedbacks)
            avg_vocab = sum(f.get("vocabulary_score", 0) for f in feedbacks) / len(feedbacks)
            avg_clarity = sum(f.get("clarity_score", 0) for f in feedbacks) / len(feedbacks)
            avg_tone = 0
            avg_job_readiness = sum(f.get("job_readiness_score", 0) for f in feedbacks) / len(feedbacks)
        else:
            avg_grammar = avg_vocab = avg_clarity = avg_tone = avg_job_readiness = 0

        # استخراج الأخطاء
        all_mistakes = []
        for f in feedbacks:
            corr = f.get("corrections", [])
            if isinstance(corr, list):
                all_mistakes.extend(corr)

        # حساب التكرار
        mistake_counts = {}
        for m in all_mistakes:
            m_str = json.dumps(m) if isinstance(m, dict) else str(m)
            mistake_counts[m_str] = mistake_counts.get(m_str, 0) + 1

        recurring = [k for k, v in mistake_counts.items() if v >= 2]

        return json.dumps({
            "status": "success",
            "summary": {
                "sessions_this_week": sessions_count,
                "avg_grammar_score": round(avg_grammar, 1),
                "avg_vocabulary_score": round(avg_vocab, 1),
                "avg_clarity_score": round(avg_clarity, 1),
                "avg_tone_score": round(avg_tone, 1),
                "avg_job_readiness": round(avg_job_readiness, 1),
                "recurring_mistakes": recurring,
            }
        })

    except Exception as e:
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            # Check sessions
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE learner_id = ? AND created_at >= ?", (learner_id, week_ago))
            sessions_count = cursor.fetchone()[0]
            
            # Check feedback
            cursor.execute("SELECT * FROM feedback_history WHERE learner_id = ? AND created_at >= ?", (learner_id, week_ago))
            rows = cursor.fetchall()
            conn.close()
            
            feedbacks = [dict(r) for r in rows]
            if feedbacks:
                avg_grammar = sum(f.get("grammar_score", 0) for f in feedbacks) / len(feedbacks)
                avg_vocab = sum(f.get("vocabulary_score", 0) for f in feedbacks) / len(feedbacks)
                avg_clarity = sum(f.get("clarity_score", 0) for f in feedbacks) / len(feedbacks)
                avg_tone = 0
                avg_job_readiness = sum(f.get("job_readiness_score", 0) for f in feedbacks) / len(feedbacks)
            else:
                avg_grammar = avg_vocab = avg_clarity = avg_tone = avg_job_readiness = 0
                
            all_mistakes = []
            for f in feedbacks:
                corr_str = f.get("corrections", "[]")
                try:
                    corr = json.loads(corr_str) if isinstance(corr_str, str) else corr_str
                except Exception:
                    corr = []
                if isinstance(corr, list):
                    all_mistakes.extend(corr)
                    
            mistake_counts = {}
            for m in all_mistakes:
                m_str = json.dumps(m) if isinstance(m, dict) else str(m)
                mistake_counts[m_str] = mistake_counts.get(m_str, 0) + 1
                
            recurring = [k for k, v in mistake_counts.items() if v >= 2]
            
            return json.dumps({
                "status": "success",
                "summary": {
                    "sessions_this_week": sessions_count,
                    "avg_grammar_score": round(avg_grammar, 1),
                    "avg_vocabulary_score": round(avg_vocab, 1),
                    "avg_clarity_score": round(avg_clarity, 1),
                    "avg_tone_score": round(avg_tone, 1),
                    "avg_job_readiness": round(avg_job_readiness, 1),
                    "recurring_mistakes": recurring,
                }
            })
        except Exception as sqle:
            return json.dumps({"status": "error", "message": f"Supabase error: {e}. SQLite error: {sqle}"})


@tool
def get_recurring_mistakes(learner_id: str, limit: int = 5) -> str:
    """
    يُرجع أكثر الأخطاء تكراراً للمستخدم على مدار كل جلساته من Supabase.
    """
    try:
        supabase = get_supabase()
        
        res = supabase.table("feedback_history").select("corrections") \
            .eq("learner_id", learner_id) \
            .order("created_at", desc=True) \
            .limit(50).execute()

        all_mistakes = []
        for row in res.data:
            corr = row.get("corrections", [])
            if isinstance(corr, list):
                all_mistakes.extend(corr)

        mistake_counts = {}
        for m in all_mistakes:
            m_str = json.dumps(m) if isinstance(m, dict) else str(m)
            mistake_counts[m_str] = mistake_counts.get(m_str, 0) + 1

        top_mistakes = sorted(
            mistake_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return json.dumps({
            "status": "success",
            "recurring_mistakes": [
                {"mistake": m, "count": c} for m, c in top_mistakes
            ]
        })

    except Exception as e:
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT corrections FROM feedback_history WHERE learner_id = ? ORDER BY created_at DESC LIMIT 50", (learner_id,))
            rows = cursor.fetchall()
            conn.close()
            
            all_mistakes = []
            for row in rows:
                corr_str = row["corrections"]
                try:
                    corr = json.loads(corr_str) if isinstance(corr_str, str) else corr_str
                except Exception:
                    corr = []
                if isinstance(corr, list):
                    all_mistakes.extend(corr)
                    
            mistake_counts = {}
            for m in all_mistakes:
                m_str = json.dumps(m) if isinstance(m, dict) else str(m)
                mistake_counts[m_str] = mistake_counts.get(m_str, 0) + 1
                
            top_mistakes = sorted(
                mistake_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return json.dumps({
                "status": "success",
                "recurring_mistakes": [
                    {"mistake": m, "count": c} for m, c in top_mistakes
                ]
            })
        except Exception as sqle:
            return json.dumps({"status": "error", "message": f"Supabase error: {e}. SQLite error: {sqle}"})


@tool
def generate_next_steps(learner_id: str) -> str:
    """
    يُولِّد الخطوات القادمة المقترحة بناءً على أداء المستخدم.
    """
    try:
        summary_result = json.loads(get_weekly_summary.invoke({"learner_id": learner_id}))

        if summary_result["status"] != "success":
            return json.dumps({"status": "error", "message": "Could not generate summary"})

        summary = summary_result["summary"]
        next_steps = []

        if summary["avg_grammar_score"] < 6.0:
            next_steps.append("Practice grammar exercises focusing on tense consistency")

        if summary["avg_vocabulary_score"] < 6.0:
            next_steps.append("Study technical vocabulary list for your target domain")

        if summary["avg_job_readiness"] < 50:
            next_steps.append("Complete one job interview roleplay session this week")

        if summary["sessions_this_week"] < 3:
            next_steps.append("Try to practice at least 3 sessions per week for consistency")

        for mistake in summary["recurring_mistakes"][:2]:
            next_steps.append(f"Focus on fixing: {mistake}")

        if not next_steps:
            next_steps.append("Great progress! Try a more advanced conversation topic")

        return json.dumps({
            "status": "success",
            "next_steps": next_steps
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


PROGRESS_TOOLS = [
    log_session,
    save_feedback_result,
    get_weekly_summary,
    get_recurring_mistakes,
    generate_next_steps,
]
