""""""

import json
import random
from langchain.tools import tool



INTERVIEW_QUESTIONS_BY_LEVEL = {
    "A1": [
        "What is your name?",
        "Where are you from?",
        "What do you study?",
    ],
    "A2": [
        "Tell me about yourself.",
        "What are your hobbies?",
        "Why do you want this job?",
    ],
    "B1": [
        "Describe your most recent project.",
        "What are your strengths and weaknesses?",
        "Where do you see yourself in 5 years?",
    ],
    "B2": [
        "Tell me about a challenging technical problem you solved.",
        "How do you handle working under pressure?",
        "Describe your experience with agile methodologies.",
    ],
    "C1": [
        "How would you architect a scalable microservices system?",
        "Describe a time you led a cross-functional team through a difficult project.",
        "How do you approach technical debt in a production system?",
    ],
    "C2": [
        "Walk me through your decision-making process when evaluating trade-offs in system design.",
        "How do you mentor junior engineers while maintaining delivery speed?",
        "Describe how you would drive organizational change around engineering practices.",
    ],
}

GRAMMAR_EXERCISES_BY_LEVEL = {
    "A1": [
        {
            "type": "fill_blank",
            "question": "I ___ a student. (am/is/are)",
            "answer": "am",
            "explanation": "Use 'am' with 'I' as the subject."
        },
        {
            "type": "fill_blank",
            "question": "She ___ to school every day. (go/goes/going)",
            "answer": "goes",
            "explanation": "Add 's' to the verb for third person singular (he/she/it)."
        },
    ],
    "B1": [
        {
            "type": "fill_blank",
            "question": "By the time I arrived, they ___ already left. (have/had/has)",
            "answer": "had",
            "explanation": "Past Perfect (had + past participle) describes an action completed before another past action."
        },
        {
            "type": "correction",
            "question": "Fix this sentence: 'I have went to Dubai last year.'",
            "answer": "I went to Dubai last year.",
            "explanation": "Use Simple Past (went) for completed actions with a specific time reference."
        },
    ],
    "B2": [
        {
            "type": "correction",
            "question": "Fix: 'The project which we worked hardly on was successful.'",
            "answer": "The project that we worked hard on was successful.",
            "explanation": "'Hard' is the correct adverb here. 'Hardly' means 'almost not at all'."
        },
    ],
}

VOCABULARY_TOPICS = {
    "AI": ["neural network", "training data", "inference", "fine-tuning",
           "embeddings", "transformer", "prompt engineering", "hallucination"],
    "cloud": ["deployment", "containerization", "orchestration", "auto-scaling",
              "load balancer", "serverless", "CDN", "latency"],
    "software": ["refactoring", "technical debt", "CI/CD", "version control",
                 "code review", "debugging", "unit testing", "API endpoint"],
    "data": ["pipeline", "ETL", "normalization", "schema", "query optimization",
             "data warehouse", "feature engineering", "model evaluation"],
}



@tool
def generate_interview_question(
    current_level: str = "B1",
    topic: str = "general"
) -> str:
    """Generate a job interview question suitable for the learner."""
    level = current_level if current_level in INTERVIEW_QUESTIONS_BY_LEVEL else "B1"
    questions = INTERVIEW_QUESTIONS_BY_LEVEL[level]

    selected = random.choice(questions)

    return json.dumps({
        "status": "success",
        "exercise": {
            "type": "interview_question",
            "level": level,
            "question": selected,
            "instructions": (
                "Please answer this interview question in English. "
                "Take your time to structure your response. "
                "I will provide detailed feedback after your answer."
            )
        }
    })


@tool
def generate_grammar_exercise(
    current_level: str = "B1",
    weak_area: str = ""
) -> str:
    """Generate a grammar exercise suitable for the learner."""
    exercises = GRAMMAR_EXERCISES_BY_LEVEL.get(current_level, GRAMMAR_EXERCISES_BY_LEVEL["B1"])
    selected = random.choice(exercises)

    return json.dumps({
        "status": "success",
        "exercise": {
            "type": selected["type"],
            "level": current_level,
            "question": selected["question"],
            "hint": "Think carefully before answering.",
            "answer": selected["answer"],
            "explanation": selected["explanation"]
        }
    })


@tool
def generate_vocabulary_exercise(
    current_level: str = "B1",
    topic: str = "AI"
) -> str:
    """Generate a vocabulary exercise suitable for the learner."""
    vocab_list = VOCABULARY_TOPICS.get(topic, VOCABULARY_TOPICS["software"])

    selected_words = random.sample(vocab_list, min(5, len(vocab_list)))

    return json.dumps({
        "status": "success",
        "exercise": {
            "type": "vocabulary",
            "level": current_level,
            "topic": topic,
            "words": selected_words,
            "instructions": (
                f"For each of these {topic} terms, "
                "try to use it in a sentence that explains what it means: "
                f"{', '.join(selected_words)}"
            )
        }
    })


@tool
def generate_email_writing_task(
    current_level: str = "B1",
    scenario: str = "project_update"
) -> str:
    """Generate an email writing task suitable for the learner."""
    scenarios = {
        "project_update": {
            "context": "You are a developer who just completed a major feature.",
            "task": "Write an email to your manager updating them on the project status, "
                    "mentioning what was completed, any blockers, and next steps.",
            "key_phrases": ["I am writing to update you on", "We have successfully",
                           "One challenge we encountered", "The next steps are"]
        },
        "meeting_request": {
            "context": "You want to schedule a technical review meeting.",
            "task": "Write an email to your team requesting a 1-hour technical review meeting "
                    "for next week, including the agenda.",
            "key_phrases": ["I would like to schedule", "The purpose of this meeting",
                           "Please let me know your availability", "The agenda will include"]
        },
        "follow_up": {
            "context": "You had a job interview 3 days ago and have not heard back.",
            "task": "Write a professional follow-up email to the recruiter "
                    "expressing continued interest in the position.",
            "key_phrases": ["I wanted to follow up on", "I remain very interested",
                           "Please feel free to contact me", "Thank you for your time"]
        },
    }

    selected = scenarios.get(scenario, scenarios["project_update"])

    return json.dumps({
        "status": "success",
        "exercise": {
            "type": "email_writing",
            "level": current_level,
            "context": selected["context"],
            "task": selected["task"],
            "suggested_phrases": selected["key_phrases"],
            "instructions": "Write a professional email of 150-200 words. "
                           "I will provide feedback on structure, grammar, and tone."
        }
    })


EXERCISE_TOOLS = [
    generate_interview_question,
    generate_grammar_exercise,
    generate_vocabulary_exercise,
    generate_email_writing_task,
]
