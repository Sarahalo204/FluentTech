import uuid
import json
import os
import jwt
import hashlib
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

from dotenv import load_dotenv
load_dotenv()

from tools.profile_tool import create_learner_profile, get_learner_profile, init_db, update_learner_level, get_supabase, update_learning_goals, update_preferred_topics, get_learner_by_email
from tools.progress_tool import get_weekly_summary, get_recurring_mistakes, generate_next_steps, log_session, init_progress_db
from tools.exercise_tool import generate_interview_question, generate_grammar_exercise, generate_vocabulary_exercise, generate_email_writing_task
from agents import run_agent
from agents.state import create_initial_state
from agents.guardrails import validate_input, validate_output

from langchain.globals import set_debug, set_verbose
set_debug(True)
set_verbose(True)

app = FastAPI(title="EduLingo API")

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-prod")
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

def get_password_hash(password: str) -> str:
    # Use simple SHA256 hashing for compatibility
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def save_long_term_memory(learner_id: str, session_id: str, state: Any):
    """Saves the LangGraph state to Supabase at the end of the session."""
    try:
        supabase = get_supabase()
        # Clean state for JSON serialization if needed
        data = {
            "learner_id": learner_id,
            "session_id": session_id,
            "agent_state": state,
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("session_memory").upsert(data).execute()
    except Exception as e:
        print(f"Error saving long-term memory to Supabase: {e}")
        # SQLite Fallback
        try:
            import sqlite3
            conn = sqlite3.connect("edulingo.db")
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_memory (
                    learner_id TEXT,
                    session_id TEXT PRIMARY KEY,
                    agent_state TEXT NOT NULL,
                    updated_at TEXT
                )
            """)
            cursor.execute("""
                INSERT INTO session_memory (learner_id, session_id, agent_state, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    agent_state=excluded.agent_state,
                    updated_at=excluded.updated_at
            """, (learner_id, session_id, json.dumps(state), datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            print("[+] Saved session memory to SQLite successfully.")
        except Exception as sqle:
            print(f"Error saving long-term memory to SQLite: {sqle}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for agent sessions (LangGraph State)
sessions: Dict[str, Any] = {}

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    target_level: str
    learning_goals: List[str]
    preferred_topics: List[str]

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdateLevelRequest(BaseModel):
    learner_id: str
    new_level: str

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    target_level: Optional[str] = None
    learning_goals: Optional[List[str]] = None
    preferred_topics: Optional[List[str]] = None

class ChatRequest(BaseModel):
    learner_id: str
    session_id: str
    user_input: str
    session_type: Optional[str] = None # conversation, roleplay, feedback

class ExerciseRequest(BaseModel):
    learner_id: str
    exercise_type: str # 'interview', 'grammar', 'vocabulary', 'email'
    topic_or_weakness: Optional[str] = None

@app.post("/auth/register")
async def register(req: RegisterRequest):
    # Check if user already exists
    existing_user = get_learner_by_email(req.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_id = f"usr_{uuid.uuid4().hex[:8]}"
    hashed_pw = get_password_hash(req.password)
    
    res_str = create_learner_profile.invoke({
        "learner_id": new_id,
        "name": req.name,
        "email": req.email,
        "password_hash": hashed_pw,
        "target_level": req.target_level,
        "learning_goals": json.dumps(req.learning_goals),
        "preferred_topics": json.dumps(req.preferred_topics)
    })
    res = json.loads(res_str)
    
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    
    token = create_access_token({"sub": new_id})
    return {
        "learner_id": new_id,
        "name": req.name,
        "level": "A1",
        "access_token": token
    }

@app.post("/auth/login")
async def login(req: LoginRequest):
    user = get_learner_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if not user.get("password_hash") or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user["learner_id"]})
    return {
        "learner_id": user["learner_id"],
        "name": user["name"],
        "level": user.get("current_level", "A1"),
        "access_token": token
    }

@app.post("/auth/update_level")
def update_level(req: UpdateLevelRequest, token_learner_id: str = Depends(verify_token)):
    if req.learner_id != token_learner_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    res = json.loads(update_learner_level.invoke({
        "learner_id": req.learner_id,
        "new_level": req.new_level
    }))
    if res["status"] == "error":
        raise HTTPException(status_code=400, detail=res["message"])
    return {"status": "success", "level": req.new_level}

@app.get("/api/profile/{learner_id}")
def get_profile(learner_id: str, token_learner_id: str = Depends(verify_token)):
    if learner_id != token_learner_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    res = json.loads(get_learner_profile.invoke({"learner_id": learner_id}))
    if res["status"] == "error":
        raise HTTPException(status_code=404, detail="User not found")
    return res["profile"]

@app.put("/api/profile/{learner_id}")
def update_profile(learner_id: str, req: ProfileUpdateRequest, token_learner_id: str = Depends(verify_token)):
    if learner_id != token_learner_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # For name and target_level we use Supabase with SQLite fallback.
    try:
        update_data = {}
        if req.name is not None:
            update_data["name"] = req.name
        if req.target_level is not None:
            update_data["target_level"] = req.target_level
            
        if update_data:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            try:
                supabase = get_supabase()
                supabase.table("learner_profiles").update(update_data).eq("learner_id", learner_id).execute()
            except Exception as e:
                # SQLite fallback
                import sqlite3
                conn = sqlite3.connect("edulingo.db")
                cursor = conn.cursor()
                
                query_parts = []
                params = []
                for k, v in update_data.items():
                    query_parts.append(f"{k} = ?")
                    params.append(v)
                
                params.append(learner_id)
                query = "UPDATE learner_profiles SET " + ", ".join(query_parts) + " WHERE learner_id = ?"
                
                cursor.execute(query, tuple(params))
                conn.commit()
                conn.close()
                print(f"Fallback to SQLite update_profile: {e}")
            
        if req.learning_goals is not None:
            update_learning_goals.invoke({"learner_id": learner_id, "goals": json.dumps(req.learning_goals)})
            
        if req.preferred_topics is not None:
            update_preferred_topics.invoke({"learner_id": learner_id, "topics": json.dumps(req.preferred_topics)})
            
        return {"status": "success", "message": "Profile updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat(req: ChatRequest, token_learner_id: str = Depends(verify_token)):
    if req.learner_id != token_learner_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    profile_res = json.loads(get_learner_profile.invoke({"learner_id": req.learner_id}))
    if profile_res["status"] == "error":
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = profile_res["profile"]
    
    if req.session_id not in sessions:
        sessions[req.session_id] = create_initial_state(req.learner_id, req.user_input, profile)
        
    state = sessions[req.session_id]
    
    # --- Guardrails: Input Validation ---
    validation_result = validate_input(req.user_input)
    if not validation_result["is_safe"]:
        return {
            "response": validation_result["message"],
            "agent_used": "guardrail_rejected",
            "feedback": None
        }
    
    try:
        result = run_agent(
            user_input=req.user_input,
            learner_id=req.learner_id,
            existing_state=state
        )
        
        sessions[req.session_id] = result.get("updated_state")
        
        agent_used = result.get("agent_used", "Unknown")
        log_session.invoke({
            "learner_id": req.learner_id,
            "session_id": req.session_id,
            "session_type": str(agent_used),
            "duration_mins": 1
        })
        
        # Save Long-term memory to Supabase DB (Task 10)
        save_long_term_memory(req.learner_id, req.session_id, sessions[req.session_id])
        
        # --- Guardrails: Output Validation ---
        final_response = validate_output(result.get("response", "Error processing request."))
        
        return {
            "response": final_response,
            "agent_used": agent_used,
            "feedback": result.get("feedback")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/exercises")
def generate_exercise(req: ExerciseRequest, token_learner_id: str = Depends(verify_token)):
    if req.learner_id != token_learner_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    profile_res = json.loads(get_learner_profile.invoke({"learner_id": req.learner_id}))
    if profile_res["status"] == "error":
        raise HTTPException(status_code=404, detail="User not found")
        
    level = profile_res["profile"].get("current_level", "B1")
    topic = req.topic_or_weakness or "general"
    
    try:
        if req.exercise_type == "interview":
            res = generate_interview_question.invoke({"current_level": level, "topic": topic})
        elif req.exercise_type == "grammar":
            res = generate_grammar_exercise.invoke({"current_level": level, "weak_area": topic})
        elif req.exercise_type == "vocabulary":
            res = generate_vocabulary_exercise.invoke({"current_level": level, "topic": topic})
        elif req.exercise_type == "email":
            res = generate_email_writing_task.invoke({"current_level": level, "scenario": topic})
        else:
            raise HTTPException(status_code=400, detail="Invalid exercise type")
            
        data = json.loads(res)
        if data.get("status") == "error":
            raise HTTPException(status_code=500, detail=data.get("message"))
            
        return data["exercise"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{learner_id}")
def get_progress(learner_id: str, token_learner_id: str = Depends(verify_token)):
    if learner_id != token_learner_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    profile_res = json.loads(get_learner_profile.invoke({"learner_id": learner_id}))
    if profile_res["status"] == "error":
        raise HTTPException(status_code=404, detail="User not found")
        
    level = profile_res["profile"].get("current_level", "A1")
    
    summary = json.loads(get_weekly_summary.invoke({"learner_id": learner_id}))
    mistakes = json.loads(get_recurring_mistakes.invoke({"learner_id": learner_id, "limit": 3}))
    steps = json.loads(generate_next_steps.invoke({"learner_id": learner_id}))
    
    avg_grammar = summary.get("summary", {}).get("avg_grammar_score", 0) * 10
    avg_vocab = summary.get("summary", {}).get("avg_vocabulary_score", 0) * 10
    avg_clarity = summary.get("summary", {}).get("avg_clarity_score", 0) * 10
    
    chart_data = [
        {"week": "W1", "grammar": 50, "vocab": 55, "overall": 52},
        {"week": "W2", "grammar": 65, "vocab": 60, "overall": 62},
        {"week": "W3", "grammar": 70, "vocab": 75, "overall": 72},
        {"week": "Current", "grammar": avg_grammar, "vocab": avg_vocab, "overall": avg_clarity}
    ]
    
    errors = [{"mistake": m, "count": 2} for m in mistakes.get("recurring_mistakes", [])]
    
    return {
        "level": level,
        "sessionsCompleted": summary.get("summary", {}).get("sessions_this_week", 0) + profile_res["profile"].get("sessions_completed", 0),
        "chartData": chart_data,
        "errors": errors if errors else [{"mistake": "No recurring mistakes yet!", "count": 0}],
        "nextSteps": steps.get("next_steps", ["Keep practicing to generate insights!"])
    }

if __name__ == "__main__":
    import uvicorn
    init_db()
    init_progress_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
