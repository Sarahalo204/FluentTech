""""""
import re

BANNED_KEYWORDS = [
    "ignore all previous instructions", "forget your instructions",
    "nsfw", "violence", "hate speech", "you are not an ai"
]

def validate_input(user_input: str) -> dict:
    """"""
    lower_input = user_input.lower()
    
    # 1. Prompt Injection & Safety Check
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
