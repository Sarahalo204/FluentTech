""""""

import json
import os
from datetime import datetime
from typing import Optional
from langchain.tools import tool
from supabase import create_client, Client


SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

VALID_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

def init_db():
    """
    Since we use Supabase, table creation is handled via SQL script.
    This function just verifies connection.
    """
    if SUPABASE_URL:
        # Just check if we can connect
        get_supabase()


@tool
def create_learner_profile(
    learner_id: str,
    name: str,
    email: str = "",
    password_hash: str = "",
    target_level: str = "B2",
    learning_goals: str = "[]",
    preferred_topics: str = "[]"
) -> str:
    """Create a new learner profile in the database."""
    if not learner_id or not learner_id.strip():
        return json.dumps({"status": "error", "message": "learner_id is required"})
    if not name or not name.strip():
        return json.dumps({"status": "error", "message": "name is required"})
    if target_level not in VALID_LEVELS:
        return json.dumps({"status": "error", "message": f"Invalid level. Must be one of: {VALID_LEVELS}"})

    try:
        goals = json.loads(learning_goals)
        topics = json.loads(preferred_topics)
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "learning_goals and preferred_topics must be valid JSON arrays"})

    try:
        supabase = get_supabase()
        now = datetime.utcnow().isoformat()
        
        data = {
            "learner_id": learner_id,
            "name": name.strip(),
            "email": email.strip() if email else None,
            "password_hash": password_hash if password_hash else None,
            "target_level": target_level,
            "learning_goals": goals,
            "preferred_topics": topics,
            "created_at": now,
            "updated_at": now
        }
        
        # Upsert operation
        response = supabase.table("learner_profiles").upsert(data).execute()
        
        return json.dumps({
            "status": "success",
            "message": f"Profile created for {name.strip()}",
            "learner_id": learner_id
        })

    except Exception as e:
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learner_profiles (
                    learner_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    current_level TEXT DEFAULT 'A1',
                    target_level TEXT DEFAULT 'B2',
                    learning_goals TEXT DEFAULT '[]',
                    weak_areas TEXT DEFAULT '[]',
                    preferred_topics TEXT DEFAULT '[]',
                    sessions_completed INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO learner_profiles 
                (learner_id, name, email, password_hash, target_level, learning_goals, preferred_topics, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learner_id) DO UPDATE SET
                    name=excluded.name,
                    email=excluded.email,
                    password_hash=excluded.password_hash,
                    target_level=excluded.target_level,
                    learning_goals=excluded.learning_goals,
                    preferred_topics=excluded.preferred_topics,
                    updated_at=excluded.updated_at
            """, (
                learner_id, name.strip(), email.strip() if email else None, password_hash if password_hash else None,
                target_level, json.dumps(goals), json.dumps(topics),
                now, now
            ))
            conn.commit()
            conn.close()
            return json.dumps({
                "status": "success",
                "message": f"Profile created for {name.strip()} (SQLite Fallback)",
                "learner_id": learner_id
            })
        except Exception as sqle:
            return json.dumps({"status": "error", "message": f"Supabase error: {e}. SQLite error: {sqle}"})


def get_learner_by_email(email: str) -> Optional[dict]:
    """"""
    try:
        supabase = get_supabase()
        response = supabase.table("learner_profiles").select("*").eq("email", email.strip()).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Fallback to SQLite get_learner_by_email: {e}")
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learner_profiles WHERE email = ?", (email.strip(),))
            row = cursor.fetchone()
            conn.close()
            if row:
                return dict(row)
            return None
        except Exception as sqle:
            print(f"SQLite error get_learner_by_email: {sqle}")
            return None

@tool
def get_learner_profile(learner_id: str) -> str:
    """Get the learner's profile from the database."""
    try:
        supabase = get_supabase()
        response = supabase.table("learner_profiles").select("*").eq("learner_id", learner_id).execute()
        
        if not response.data or len(response.data) == 0:
            return json.dumps({
                "status": "not_found",
                "message": f"No profile found for learner_id: {learner_id}"
            })

        profile = response.data[0]
        return json.dumps({"status": "success", "profile": profile})

    except Exception as e:
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learner_profiles WHERE learner_id = ?", (learner_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                return json.dumps({
                    "status": "not_found",
                    "message": f"No profile found for learner_id: {learner_id} (SQLite Fallback)"
                })
            profile = dict(row)
            for col in ["learning_goals", "weak_areas", "preferred_topics"]:
                if col in profile and isinstance(profile[col], str):
                    try:
                        profile[col] = json.loads(profile[col])
                    except Exception:
                        profile[col] = []
            return json.dumps({"status": "success", "profile": profile})
        except Exception as sqle:
            return json.dumps({"status": "error", "message": f"Supabase error: {e}. SQLite error: {sqle}"})


@tool
def update_learner_level(learner_id: str, new_level: str) -> str:
    """Update the learner's CEFR level."""
    if new_level not in VALID_LEVELS:
        return json.dumps({
            "status": "error",
            "message": f"Invalid level '{new_level}'. Must be one of: {VALID_LEVELS}"
        })

    try:
        supabase = get_supabase()
        data = {
            "current_level": new_level,
            "updated_at": datetime.utcnow().isoformat()
        }
        response = supabase.table("learner_profiles").update(data).eq("learner_id", learner_id).execute()

        if not response.data:
            return json.dumps({"status": "error", "message": f"Learner {learner_id} not found"})

        return json.dumps({
            "status": "success",
            "message": f"Level updated to {new_level}",
            "new_level": new_level
        })

    except Exception as e:
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE learner_profiles SET current_level = ?, updated_at = ? WHERE learner_id = ?",
                           (new_level, datetime.utcnow().isoformat(), learner_id))
            changes = conn.total_changes
            conn.commit()
            conn.close()
            if changes == 0:
                return json.dumps({"status": "error", "message": f"Learner {learner_id} not found (SQLite Fallback)"})
            return json.dumps({
                "status": "success",
                "message": f"Level updated to {new_level} (SQLite Fallback)",
                "new_level": new_level
            })
        except Exception as sqle:
            return json.dumps({"status": "error", "message": f"Supabase error: {e}. SQLite error: {sqle}"})


@tool
def add_weak_area(learner_id: str, weakness: str) -> str:
    """Add a new weak area to the learner's profile."""
    if not weakness or not weakness.strip():
        return json.dumps({"status": "error", "message": "weakness is required"})

    try:
        supabase = get_supabase()
        response = supabase.table("learner_profiles").select("weak_areas").eq("learner_id", learner_id).execute()

        if not response.data:
            return json.dumps({"status": "error", "message": "Learner not found"})

        weak_areas = response.data[0].get("weak_areas", [])
        if not isinstance(weak_areas, list):
            weak_areas = []

        weakness_clean = weakness.strip().lower()
        existing_lower = [str(w).lower() for w in weak_areas]
        
        if weakness_clean not in existing_lower:
            weak_areas.append(weakness.strip())
            update_data = {
                "weak_areas": weak_areas,
                "updated_at": datetime.utcnow().isoformat()
            }
            supabase.table("learner_profiles").update(update_data).eq("learner_id", learner_id).execute()

        return json.dumps({
            "status": "success",
            "weak_areas": weak_areas
        })

    except Exception as e:
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            cursor = conn.cursor()
            cursor.execute("SELECT weak_areas FROM learner_profiles WHERE learner_id = ?", (learner_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return json.dumps({"status": "error", "message": "Learner not found (SQLite Fallback)"})
            
            weak_areas_str = row[0]
            try:
                weak_areas = json.loads(weak_areas_str) if weak_areas_str else []
            except Exception:
                weak_areas = []
            
            if not isinstance(weak_areas, list):
                weak_areas = []
                
            weakness_clean = weakness.strip().lower()
            existing_lower = [str(w).lower() for w in weak_areas]
            
            if weakness_clean not in existing_lower:
                weak_areas.append(weakness.strip())
                cursor.execute("UPDATE learner_profiles SET weak_areas = ?, updated_at = ? WHERE learner_id = ?",
                               (json.dumps(weak_areas), datetime.utcnow().isoformat(), learner_id))
                conn.commit()
            conn.close()
            return json.dumps({
                "status": "success",
                "weak_areas": weak_areas
            })
        except Exception as sqle:
            return json.dumps({"status": "error", "message": f"Supabase error: {e}. SQLite error: {sqle}"})


@tool
def update_learning_goals(learner_id: str, goals: str) -> str:
    """Update the learner's learning goals."""
    try:
        parsed_goals = json.loads(goals)
        if not isinstance(parsed_goals, list):
            return json.dumps({"status": "error", "message": "goals must be a JSON array"})
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON format for goals"})

    try:
        supabase = get_supabase()
        data = {
            "learning_goals": parsed_goals,
            "updated_at": datetime.utcnow().isoformat()
        }
        response = supabase.table("learner_profiles").update(data).eq("learner_id", learner_id).execute()

        if not response.data:
            return json.dumps({"status": "error", "message": f"Learner {learner_id} not found"})

        return json.dumps({
            "status": "success",
            "message": "Goals updated successfully",
            "goals": parsed_goals
        })

    except Exception as e:
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE learner_profiles SET learning_goals = ?, updated_at = ? WHERE learner_id = ?",
                           (json.dumps(parsed_goals), datetime.utcnow().isoformat(), learner_id))
            changes = conn.total_changes
            conn.commit()
            conn.close()
            if changes == 0:
                return json.dumps({"status": "error", "message": f"Learner {learner_id} not found (SQLite Fallback)"})
            return json.dumps({
                "status": "success",
                "message": "Goals updated successfully (SQLite Fallback)",
                "goals": parsed_goals
            })
        except Exception as sqle:
            return json.dumps({"status": "error", "message": f"Supabase error: {e}. SQLite error: {sqle}"})


@tool
def update_preferred_topics(learner_id: str, topics: str) -> str:
    """Update the learner's preferred topics."""
    try:
        parsed = json.loads(topics)
        if not isinstance(parsed, list):
            return json.dumps({"status": "error", "message": "topics must be a JSON array"})
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON format for topics"})

    try:
        supabase = get_supabase()
        data = {
            "preferred_topics": parsed,
            "updated_at": datetime.utcnow().isoformat()
        }
        response = supabase.table("learner_profiles").update(data).eq("learner_id", learner_id).execute()

        if not response.data:
            return json.dumps({"status": "error", "message": f"Learner {learner_id} not found"})

        return json.dumps({
            "status": "success",
            "message": "Preferred topics updated",
            "topics": parsed
        })

    except Exception as e:
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE learner_profiles SET preferred_topics = ?, updated_at = ? WHERE learner_id = ?",
                           (json.dumps(parsed), datetime.utcnow().isoformat(), learner_id))
            changes = conn.total_changes
            conn.commit()
            conn.close()
            if changes == 0:
                return json.dumps({"status": "error", "message": f"Learner {learner_id} not found (SQLite Fallback)"})
            return json.dumps({
                "status": "success",
                "message": "Preferred topics updated (SQLite Fallback)",
                "topics": parsed
            })
        except Exception as sqle:
            return json.dumps({"status": "error", "message": f"Supabase error: {e}. SQLite error: {sqle}"})


@tool
def get_session_history(learner_id: str, limit: int = 5) -> str:
    """Get the learner's session history."""
    try:
        supabase = get_supabase()
        response = supabase.table("sessions").select("session_id, session_type, duration_mins, created_at") \
            .eq("learner_id", learner_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()

        sessions = response.data
        return json.dumps({
            "status": "success",
            "sessions": sessions,
            "total_returned": len(sessions)
        })

    except Exception as e:
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, session_type, duration_mins, created_at FROM sessions WHERE learner_id = ? ORDER BY created_at DESC LIMIT ?",
                           (learner_id, limit))
            rows = cursor.fetchall()
            conn.close()
            sessions = [dict(row) for row in rows]
            return json.dumps({
                "status": "success",
                "sessions": sessions,
                "total_returned": len(sessions)
            })
        except Exception as sqle:
            return json.dumps({"status": "error", "message": f"Supabase error: {e}. SQLite error: {sqle}"})


PROFILE_TOOLS = [
    create_learner_profile,
    get_learner_profile,
    update_learner_level,
    add_weak_area,
    update_learning_goals,
    update_preferred_topics,
    get_session_history,
]
