""""""

import os
import json
from langchain.agents import AgentExecutor, create_react_agent
# from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from agents.state import AgentState, RoleplayScenario
from agents.llm_config import get_llm
from tools.exercise_tool import generate_interview_question, EXERCISE_TOOLS



ROLEPLAY_PERSONAS = {
    "job_interview": {
        "persona_name": "Sarah (Hiring Manager)",
        "persona": "Senior Technical Hiring Manager at a top tech company in Riyadh",
        "context": "You are conducting a technical job interview for a software/data/AI engineering position.",
        "style": "Professional but friendly. Ask follow-up questions. Challenge vague answers politely.",
        "opening": "**[Sarah (Hiring Manager)]**: Good morning! Thank you for coming in today. I'm the hiring manager here. Let's start — could you please tell me about yourself and your technical background?",
        "flow": ["introduction", "technical_skills", "past_projects", "behavioral", "questions_for_us"],
        "stage_prompts": {
            "introduction": "Ask about their background and motivation",
            "technical_skills": "Ask a technical question about their core skill",
            "past_projects": "Ask them to describe a challenging project they worked on",
            "behavioral": "Ask a behavioral question: 'Tell me about a time when...'",
            "questions_for_us": "Ask if they have any questions for the company",
        },
    },
    "sprint_meeting": {
        "persona_name": "Ahmed (Team Lead)",
        "persona": "Engineering Team Lead facilitating a sprint review meeting",
        "context": "This is a sprint review meeting. The learner is presenting their work to the team.",
        "style": "Direct, focused on delivery and blockers. Ask about timelines and dependencies.",
        "opening": "**[Ahmed (Team Lead)]**: Okay team, let's get started. Can you give us a quick update on your tasks from this sprint?",
        "flow": ["status_update", "blockers", "next_sprint", "team_feedback"],
        "stage_prompts": {
            "status_update": "Ask what they completed this sprint",
            "blockers": "Ask about any blockers or challenges",
            "next_sprint": "Discuss priorities for the next sprint",
            "team_feedback": "Give brief feedback on their update",
        },
    },
    "client_call": {
        "persona_name": "Mr. Smith (Client)",
        "persona": "A client (non-technical business stakeholder) checking on project progress",
        "context": "The learner is updating a client on their project. The client is not technical.",
        "style": "Ask for simple explanations. Show concern about timeline and budget. Be politely demanding.",
        "opening": "**[Mr. Smith (Client)]**: Hi, thanks for joining the call. I wanted to get an update on where things stand with our project. Can you walk me through what's been done?",
        "flow": ["project_status", "timeline_check", "concerns", "next_steps"],
        "stage_prompts": {
            "project_status": "Ask for a high-level project status",
            "timeline_check": "Express concern about timeline — 'Are we on track?'",
            "concerns": "Raise a specific concern about a feature or deliverable",
            "next_steps": "Ask for clear next steps and a timeline",
        },
    },
    "recruiter_screening": {
        "persona_name": "Jessica (Recruiter)",
        "persona": "HR Recruiter doing an initial phone screening for a tech role",
        "context": "This is a 15-minute initial screening call to assess basic fit.",
        "style": "Friendly but efficient. Cover salary, availability, and basic background.",
        "opening": "**[Jessica (Recruiter)]**: Hi! Thanks for taking my call. I'm reaching out about the position you applied for. Is this still a good time to chat for about 15 minutes?",
        "flow": ["availability", "salary_expectations", "background", "motivation", "next_steps"],
        "stage_prompts": {
            "availability": "Ask about their availability and notice period",
            "salary_expectations": "Ask about salary expectations",
            "background": "Quick overview of their background",
            "motivation": "Why are they interested in this role?",
            "next_steps": "Explain the next steps in the hiring process",
        },
    },
    "project_presentation": {
        "persona_name": "Dr. Khalid (Lead Reviewer)",
        "persona": "Panel of technical reviewers evaluating a capstone/final project",
        "context": "The learner is presenting their AI/software project to a panel.",
        "style": "Ask technical questions. Challenge design decisions. Be evaluative but constructive.",
        "opening": "**[Dr. Khalid (Lead Reviewer)]**: Welcome! Please go ahead and start with an overview of your project — the problem you're solving and your approach.",
        "flow": ["overview", "technical_deep_dive", "challenges", "results", "future_work"],
        "stage_prompts": {
            "overview": "Ask for a project overview",
            "technical_deep_dive": "Ask about the technical implementation details",
            "challenges": "Ask about the biggest challenge they faced",
            "results": "Ask about results, metrics, or evaluation",
            "future_work": "Ask what they would do differently or next",
        },
    },
    "salary_discussion": {
        "persona_name": "Nadia (HR Director)",
        "persona": "Hiring Manager discussing compensation package",
        "context": "The job offer is on the table. Now discussing the salary and benefits.",
        "style": "Professional negotiation. Don't reveal the top budget immediately. Ask for their expectations.",
        "opening": "**[Nadia (HR Director)]**: Congratulations — we'd like to move forward with you. Let's talk about the compensation. What are your salary expectations for this role?",
        "flow": ["expectations", "negotiation", "benefits", "final_offer"],
        "stage_prompts": {
            "expectations": "Ask for their salary expectations",
            "negotiation": "Counter-offer or negotiate terms",
            "benefits": "Discuss benefits, remote work, learning budget",
            "final_offer": "Present the final offer package",
        },
    },
}


from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

ROLEPLAY_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are playing the role of: {persona_name} - {persona}

Scenario context: {context}
Your interaction style: {style}

CRITICAL RULES:
1. Stay in character EXCEPT during the final debrief stage.
2. KEEP YOUR QUESTIONS VERY SHORT AND CONCISE. Maximum 2 sentences. Ask ONLY ONE question at a time. Do not write long paragraphs.
3. ALWAYS start your response with "**[{persona_name}]**: " so the user knows exactly who is speaking to them.
4. React realistically to what the learner says before asking your next question. Embody the persona deeply. Do not just blindly ask the next question from the list.
5. Do NOT break character to give an English lesson. HOWEVER, if the user makes a grammar or vocabulary mistake, you MUST provide a very brief, polite inline correction on a new line before your in-character response. (e.g. "\n*[Correction: I completed all my projects]*\n**[Sarah (Hiring Manager)]**: Anyway, tell me more about...")
6. If the learner gives a weak answer, probe deeper.
7. When the stage is 'debrief', you MUST break character and output ONLY the Out-of-Character (OOC) Debrief containing:
   - What they did well
   - What to improve
   - 2-3 specific language tips

Stage guidance for current stage:
{stage_guidance}

Learner profile:
- Level: {current_level}
- Goals: {learning_goals}

Conversation Summary (context from earlier):
{context_summary}

Scenario progress:
- Current stage: {current_stage} ({stage_index}/{total_stages})
- Remaining stages: {remaining_stages}
- Is this the final stage? {is_final_stage}

When to use tools:
- generate_interview_question: To get structured questions for interview scenarios
- generate_vocabulary_exercise: ONLY at the end for debrief vocabulary

Conversation so far:
{conversation_history}"""),
    ("human", "Learner's response: {input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


def determine_scenario(user_input: str, state: AgentState) -> str:
    """"""
    existing = state.get("roleplay_scenario")
    if existing:
        return existing

    try:
        from agents.llm_config import get_llm
        from pydantic import BaseModel, Field
        from typing import Literal

        class ScenarioClassification(BaseModel):
            scenario: Literal[
                "project_presentation", 
                "job_interview", 
                "sprint_meeting", 
                "client_call", 
                "recruiter_screening", 
                "salary_discussion"
            ] = Field(description="The roleplay scenario that best matches the user's intent.")
            
        llm = get_llm("roleplay").with_structured_output(ScenarioClassification)
        result = llm.invoke(f"Classify the user's requested roleplay scenario based on their input: '{user_input}'")
        return result.scenario
    except Exception as e:
        print(f"Error in determine_scenario: {e}")
        return "job_interview"  # Fallback


def roleplay_agent_node(state: AgentState) -> AgentState:
    """"""
    profile = state.get("learner_profile", {})
    user_input = state.get("user_input", "")
    messages = state.get("messages", [])
    context_summary = state.get("context_summary", "No previous context.")

    scenario_key = determine_scenario(user_input, state)
    scenario = ROLEPLAY_PERSONAS.get(scenario_key, ROLEPLAY_PERSONAS["job_interview"])

    current_level = profile.get("current_level", "B1") if profile else "B1"

    is_first_message = state.get("roleplay_scenario") is None

    conversation_history = "\n".join([
        f"  {m['role'].upper()}: {m['content'][:800]}"
        for m in state.get("messages", [])[-6:]
    ])

    flow = scenario["flow"]
    
    # Properly track stage_index in state so it doesn't get messed up by earlier conversation
    stage_index = state.get("roleplay_stage_index", 0)

    if not is_first_message:
        stage_index += 1

    if stage_index < len(flow):
        current_stage = flow[stage_index]
        remaining_stages = flow[stage_index + 1:]
        is_final_stage = False
        stage_guidance = scenario.get("stage_prompts", {}).get(
            current_stage, "Ask a short question relevant to this stage."
        )
    else:
        current_stage = "debrief"
        remaining_stages = []
        is_final_stage = True
        stage_guidance = "THE SCENARIO IS OVER. You MUST break character now and output ONLY the Out-of-Character (OOC) Debrief containing their strengths, weaknesses, and language tips. DO NOT ask any more interview questions."

    try:
        llm = get_llm("roleplay")

        if is_final_stage:
            # FORCE a break from the persona to ensure it doesn't keep asking questions
            debrief_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a Senior Silicon Valley Language Coach. The learner has just completed a '{scenario_name}' roleplay.
You MUST provide an Out-of-Character (OOC) Debrief evaluating their English skills and interview performance.
Do NOT ask any more interview questions. Do NOT act like {persona_name}.

Format your response exactly like this:
### 📊 Roleplay Debrief
**🌟 What you did well:**
- [Point 1]
- [Point 2]

**📈 Areas for improvement:**
- [Point 1]
- [Point 2]

**💡 Specific Language Tips:**
- [Tip 1]
- [Tip 2]

Conversation history to evaluate:
{conversation_history}"""),
                ("human", "Please provide my debrief.")
            ])
            chain = debrief_prompt | llm
            result = chain.invoke({
                "scenario_name": scenario_key.replace('_', ' ').title(),
                "persona_name": scenario["persona_name"],
                "conversation_history": conversation_history
            })
            agent_response = getattr(result, "content", result)
            
            # Save debrief to database
            try:
                from tools.progress_tool import save_feedback_result
                import json
                learner_id = profile.get("learner_id", "unknown") if profile else "unknown"
                session_id = state.get("session_id", "unknown_session")
                save_feedback_result.invoke({
                    "learner_id": learner_id,
                    "session_id": session_id,
                    "original_text": f"Roleplay Debrief: {scenario_key.replace('_', ' ').title()}",
                    "corrected_text": agent_response,
                    "grammar_score": 0,
                    "vocabulary_score": 0,
                    "clarity_score": 0,
                    "tone_score": 0,
                    "job_readiness_score": 0,
                    "mistakes": json.dumps([])
                })
            except Exception as e:
                print(f"Warning: Could not save debrief to DB: {e}")
        else:
            from langchain.agents import create_tool_calling_agent
            agent = create_tool_calling_agent(
                llm=llm,
                tools=EXERCISE_TOOLS,
                prompt=ROLEPLAY_AGENT_PROMPT,
            )

            executor = AgentExecutor(
                agent=agent,
                tools=EXERCISE_TOOLS,
                verbose=True,
                max_iterations=3,
                handle_parsing_errors=True,
            )

            actual_input = (
                scenario["opening"] + "\n\n[The learner has arrived. Start the scenario.]"
                if is_first_message
                else user_input
            )

            result = executor.invoke({
                "input": actual_input,
                "persona_name": scenario["persona_name"],
                "persona": scenario["persona"],
                "context": scenario["context"],
                "style": scenario["style"],
                "current_level": current_level,
                "learning_goals": profile.get("learning_goals", []) if profile else [],
                "context_summary": context_summary,
                "current_stage": current_stage,
                "stage_index": stage_index + 1,
                "total_stages": len(flow),
                "remaining_stages": remaining_stages,
                "is_final_stage": is_final_stage,
                "stage_guidance": stage_guidance,
                "conversation_history": conversation_history,
            })
            agent_response = result.get("output", scenario["opening"])

    except Exception as e:
        print(f"ERROR in roleplay_agent: {e}")
        agent_response = (
            scenario["opening"] if is_first_message
            else "I see. Could you tell me more about that?"
        )

    messages = list(state.get("messages", []))
    messages.append({"role": "assistant", "content": agent_response})

    return {
        **state,
        "messages": messages,
        "current_session_type": "roleplay_agent" if not is_final_stage else None,
        "roleplay_scenario": scenario_key if not is_final_stage else None,
        "roleplay_stage_index": stage_index if not is_final_stage else 0,
        "current_topic": f"Roleplay: {scenario_key.replace('_', ' ').title()}" if not is_final_stage else None,
        "messages_since_last_summary": state.get("messages_since_last_summary", 0) + 1,
        "next_agent": None,
    }
