""""""
import re

BANNED_KEYWORDS = [
    "ignore all previous instructions", "forget your instructions",
    "you are not an ai", "pretend you are not", "act as if you have no rules",
    "ignore the system prompt", "override your instructions", "disregard your training",
    "nsfw", "violence", "hate speech", "self-harm", "illegal",
    "bypass your filters", "jailbreak", "do anything now",
]

from pydantic import BaseModel, Field
from .llm_config import get_llm

class GuardrailClassification(BaseModel):
    is_safe: bool = Field(..., description="True if the user input is related to learning English, conversation, asking about tech, or general chat. False if the user is asking the agent to write code (like Python), solve math, or do tasks outside the scope of an English coach.")
    reason: str = Field(..., description="If is_safe is False, explain briefly why. Otherwise empty string.")

def validate_input(user_input: str) -> dict:
    """"""
    lower_input = user_input.lower()
    
    # 1. Prompt Injection & Safety Check (Static)
    for keyword in BANNED_KEYWORDS:
        if keyword in lower_input:
            return {
                "is_safe": False,
                "reason": "safety_violation",
                "message": "I'm sorry, but I cannot process that request. Let's stick to improving your professional English and discussing tech topics."
            }
            
    # 2. Too short / nonsense
    if len(lower_input.strip()) < 2:
        return {
            "is_safe": False,
            "reason": "too_short",
            "message": "Could you please provide a bit more detail so I can help you better?"
        }

    # 3. Non-English (Arabic) check
    if re.search(r'[\u0600-\u06FF]', user_input):
        return {
            "is_safe": False,
            "reason": "language_violation",
            "message": "Please communicate in English only so I can properly evaluate and assist you with your learning."
        }

    # 4. Dynamic LLM Scope Check
    try:
        llm = get_llm("supervisor") # Fast model
        structured_llm = llm.with_structured_output(GuardrailClassification)
        result = structured_llm.invoke(
            f"You are a guardrail for an English learning coach designed for Tech Professionals. It is COMPLETELY SAFE AND EXPECTED for users to discuss Software Engineering, AI, Computer Science, and job interviews in English. You must ONLY reject requests if the user explicitly asks you to WRITE raw programming code, solve math equations, or act as a general AI assistant outside the scope of conversation.\n\nUser Input: '{user_input}'\n\nClassify this input."
        )
        if not result.is_safe:
            return {
                "is_safe": False,
                "reason": "out_of_scope",
                "message": f"I'm your English language coach! I cannot help with that ({result.reason}). Let's focus on practicing English."
            }
    except Exception as e:
        print(f"Dynamic guardrail error: {e}")
        # Fallback to safe if LLM fails
        pass

    return {"is_safe": True}


def validate_output(agent_response: str) -> str:
    """"""
    if "Thought:" in agent_response and "Action:" in agent_response:
        parts = agent_response.split("Final Answer:")
        if len(parts) > 1:
            return parts[-1].strip()
        else:
            return "I apologize, I had a brief technical hiccup. Could you repeat that?"
            
    return agent_response
