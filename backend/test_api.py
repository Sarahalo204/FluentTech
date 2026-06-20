import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def run_tests():
    # Register
    try:
        reg = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Test User",
            "email": f"test_{int(time.time())}@example.com",
            "password": "password123",
            "target_level": "B2",
            "learning_goals": ["Speak fluently", "Write emails"],
            "preferred_topics": ["Microservices", "Cloud Architecture"]
        }).json()
        learner_id = reg.get("learner_id")
        token = reg.get("access_token")
    except Exception as e:
        return

    headers = {"Authorization": f"Bearer {token}"}
    results = []

    def chat(session_id, text):
        res = requests.post(f"{BASE_URL}/api/chat", json={
            "learner_id": learner_id,
            "session_id": session_id,
            "user_input": text
        }, headers=headers).json()
        return res

    # 1. Feedback Agent
    f_res = chat("session_feedback", "Can you evaluate this text for me? 'I has building many APIs.'")
    results.append({"scenario": "Feedback Agent", "input": "Can you evaluate this text for me? 'I has building many APIs.'", "output": f_res})

    # 2. Conversation Agent
    c_res = chat("session_conv", "Hi, I want to practice English conversation about microservices.")
    results.append({"scenario": "Conversation Intro", "input": "Hi, I want to practice English...", "output": c_res})
    c_res2 = chat("session_conv", "I use docker and it make my app very fast.")
    results.append({"scenario": "Conversation Error", "input": "I use docker and it make my app very fast.", "output": c_res2})

    # 3. Learning Agent
    l_res = chat("session_learning", "Can you create a weekly learning plan for me?")
    results.append({"scenario": "Learning Plan", "input": "Can you create a weekly learning plan for me?", "output": l_res})

    # 4. Roleplay Agent
    r_res = chat("session_roleplay", "I want to do a sprint meeting roleplay.")
    results.append({"scenario": "Roleplay Turn 1", "input": "I want to do a sprint meeting roleplay.", "output": r_res})
    
    r_res2 = chat("session_roleplay", "I completed the authentication API.")
    results.append({"scenario": "Roleplay Turn 2", "input": "I completed the authentication API.", "output": r_res2})
    
    r_res3 = chat("session_roleplay", "I don't have any blockers.")
    results.append({"scenario": "Roleplay Turn 3", "input": "I don't have any blockers.", "output": r_res3})
    
    r_res4 = chat("session_roleplay", "Next sprint I will work on the payment gateway.")
    results.append({"scenario": "Roleplay Turn 4", "input": "Next sprint I will work on the payment gateway.", "output": r_res4})
    
    r_res5 = chat("session_roleplay", "Thank you Ahmed.")
    results.append({"scenario": "Roleplay Turn 5 (Debrief)", "input": "Thank you Ahmed.", "output": r_res5})

    with open("api_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_tests()
