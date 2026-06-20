import json
import time
import os

from agents import run_agent
from agents.state import create_initial_state

def run_tests():
    learner_id = "test_user_123"
    results = []
    
    print("Running Tests for FluentTech Agents...\n")

    # 1. Test Feedback Agent
    print("Testing Feedback Agent...")
    res1 = run_agent(
        user_input="I wants to check my writing. I am software engineer and I has build a lot of api.",
        learner_id=learner_id
    )
    # Force route to feedback agent? If we just say "Can you evaluate my writing?", it will route to feedback agent.
    # Wait, run_agent routes based on supervisor. Let's do a 2-step for feedback.
    res1_trigger = run_agent("Can you evaluate this text for me? 'I has building many APIs.'", learner_id)
    results.append({
        "agent": "Feedback Agent",
        "scenario": "Text Evaluation",
        "user_input": "Can you evaluate this text for me? 'I has building many APIs.'",
        "agent_used": res1_trigger.get("agent_used"),
        "response": res1_trigger.get("response")
    })

    # 2. Test Conversation Agent
    print("Testing Conversation Agent...")
    res2_state = None
    res2 = run_agent("Hi, I want to practice English conversation about microservices.", learner_id)
    res2_state = res2.get("updated_state")
    results.append({
        "agent": "Conversation Agent",
        "scenario": "Technical Chat (Initial)",
        "user_input": "Hi, I want to practice English conversation about microservices.",
        "agent_used": res2.get("agent_used"),
        "response": res2.get("response")
    })
    
    # Send a message with grammar error to test inline correction
    res3 = run_agent("I use docker and it make my app very fast.", learner_id, existing_state=res2_state)
    results.append({
        "agent": "Conversation Agent",
        "scenario": "Technical Chat (Error Correction)",
        "user_input": "I use docker and it make my app very fast.",
        "agent_used": res3.get("agent_used"),
        "response": res3.get("response")
    })

    # 3. Test Learning Agent
    print("Testing Learning Agent...")
    res4 = run_agent("Can you create a weekly learning plan for me?", learner_id)
    results.append({
        "agent": "Learning Agent",
        "scenario": "Generate Weekly Plan",
        "user_input": "Can you create a weekly learning plan for me?",
        "agent_used": res4.get("agent_used"),
        "response": res4.get("response")
    })

    # 4. Test Roleplay Agent
    print("Testing Roleplay Agent (Sprint Meeting)...")
    rp_state = None
    # Trigger
    rp1 = run_agent("I want to do a sprint meeting roleplay.", learner_id)
    rp_state = rp1.get("updated_state")
    results.append({
        "agent": "Roleplay Agent",
        "scenario": "Sprint Meeting (Turn 1 - Opening)",
        "user_input": "I want to do a sprint meeting roleplay.",
        "agent_used": rp1.get("agent_used"),
        "response": rp1.get("response")
    })
    
    # Turn 2: status_update -> blockers
    rp2 = run_agent("I completed the authentication API.", learner_id, existing_state=rp_state)
    rp_state = rp2.get("updated_state")
    results.append({
        "agent": "Roleplay Agent",
        "scenario": "Sprint Meeting (Turn 2 - Status Update)",
        "user_input": "I completed the authentication API.",
        "agent_used": rp2.get("agent_used"),
        "response": rp2.get("response")
    })

    # Turn 3: blockers -> next_sprint
    rp3 = run_agent("I don't have any blockers.", learner_id, existing_state=rp_state)
    rp_state = rp3.get("updated_state")
    results.append({
        "agent": "Roleplay Agent",
        "scenario": "Sprint Meeting (Turn 3 - Blockers)",
        "user_input": "I don't have any blockers.",
        "agent_used": rp3.get("agent_used"),
        "response": rp3.get("response")
    })
    
    # Turn 4: next_sprint -> team_feedback
    rp4 = run_agent("Next sprint I will work on the payment gateway.", learner_id, existing_state=rp_state)
    rp_state = rp4.get("updated_state")
    results.append({
        "agent": "Roleplay Agent",
        "scenario": "Sprint Meeting (Turn 4 - Next Sprint)",
        "user_input": "Next sprint I will work on the payment gateway.",
        "agent_used": rp4.get("agent_used"),
        "response": rp4.get("response")
    })

    # Turn 5: team_feedback -> Debrief!
    rp5 = run_agent("Thank you Ahmed.", learner_id, existing_state=rp_state)
    rp_state = rp5.get("updated_state")
    results.append({
        "agent": "Roleplay Agent",
        "scenario": "Sprint Meeting (Turn 5 - Debrief!)",
        "user_input": "Thank you Ahmed.",
        "agent_used": rp5.get("agent_used"),
        "response": rp5.get("response")
    })

    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("Tests completed. Results saved to test_results.json")

if __name__ == "__main__":
    run_tests()
