# FluentTech — AI English Learning Agent
### *A personalized English coaching system built for Saudi tech learners*

🚀 **Live Demo:** [https://fluent-tech.vercel.app/chat](https://fluent-tech.vercel.app/chat)

---

## Project Summary
**FluentTech** is an agentic AI-powered English learning coach designed specifically for Saudi students and early-career tech professionals. Unlike generic language learning apps, FluentTech focuses on **career-oriented, practical English** — helping learners prepare for technical job interviews, workplace communication, and professional presentations.

The system leverages a **multi-agent architecture** built with LangGraph, where four specialized AI agents collaborate to deliver a personalized, adaptive learning experience that remembers the learner's goals, tracks their progress, and adjusts difficulty over time.

---

## Requirements
- **Python 3.10+** (For the FastAPI Backend)
- **Node.js 18+** & **npm** (For the React Frontend)
- **Git** (To clone the repository)
- **Supabase Account** (URL and API Key required for PostgreSQL database and Auth)
- **OpenAI Account** (API Key required for LangGraph Agents and TTS streaming)
- *(Optional)* **Docker & Docker Compose**

---

## API Keys & Environment Variables
Before running the project, you must set up your environment variables. 
Copy the example file and add your keys:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Inside your `.env` file, include:
```env
OPENAI_API_KEY=sk_your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_api_key
JWT_SECRET=your_secret_key_for_auth
```

---

## Installation
**1. Clone the repository:**
```bash
git clone https://github.com/Sarahalo204/FluentTech.git
cd FluentTech
```

**2. Install Backend Dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

**3. Install Frontend Dependencies:**
```bash
cd ../frontend
npm install
```

---

## Run the Project

### Running Locally (Without Docker)

**Backend:**
```bash
cd backend
python server.py
```
*(Runs on http://localhost:8000)*

**Frontend:**
```bash
cd frontend
npm run dev
```
*(Runs on http://localhost:5173)*

### Running with Docker (Alternative)
```bash
docker-compose up --build
```

### Ingest the knowledge base
```bash
# If using Docker:
docker exec edulingo-backend python rag/ingest.py

# If running locally:
cd backend
python rag/ingest.py
```

---

## Known Issues
- **Microphone Support:** The Speech-to-Text (STT) functionality relies on the browser's native Web Speech API. It may not work optimally on all browsers (best supported on Google Chrome).
- **Latency:** While TTS streaming is implemented to reduce audio lag, very complex grammar evaluations by the Feedback Agent might still take a few seconds due to the deep multi-step LLM analysis.
- **Audio Autoplay:** Some mobile browsers might block the TTS audio from autoplaying until the user explicitly interacts with the page.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                             │
│              Chat  │  Profile  │  Progress Dashboard                │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                             │
│         REST API  │  Session Management  │  JWT Auth                │
└──────┬──────────────────────┬────────────────────────┬─────────────┘
       │                      │                        │
       ▼                      ▼                        ▼
┌─────────────┐   ┌───────────────────────┐   ┌───────────────────┐
│  PostgreSQL │   │    LANGGRAPH ENGINE    │   │   SUPABASE DB     │
│             │   │                       │   │   (Vector Store)  │
│  learners   │   │   ┌───────────────┐   │   │                   │
│  profiles   │   │   │  SUPERVISOR   │   │   │  CEFR Levels      │
│  sessions   │   │   │     NODE      │   │   │  Grammar Rules    │
│  feedback   │   │   └──────┬────────┘   │   │  Interview Q&A    │
│  progress   │   │          │            │   │  Tech Vocabulary  │
│             │   │    ┌─────┴──────┐     │   │  Email Templates  │
└─────────────┘   │    │  ROUTING   │     │   │  Arabic Mistakes  │
       ▲          │    └─────┬──────┘     │   └───────────────────┘
       │          │          │            │            ▲
       │          │   ┌──────┴──────┐     │            │
       │          │   ▼      ▼      ▼  ▼  │            │
       │          │  ┌──┐  ┌──┐  ┌──┐ ┌──┐│            │
       │          │  │A1│  │A2│  │A3│ │A4││            │
       │          │  └──┘  └──┘  └──┘ └──┘│            │
       │          │                        │            │
       │          └────────────────────────┘            │
       │                                                │
       └────────── Long-term Memory ◄──── RAG Pipeline ─┘
```

---

## 🤖 The Four Agents

### 1. 🧠 Learning & Progress Agent *(The Brain)*
The central orchestrator of the system. Diagnoses the learner's English proficiency using CEFR-aligned diagnostic questions, maps a personalized learning journey, and generates weekly action plans. Also tracks improvement across sessions and adjusts the learning path dynamically.

### 2. 💬 Conversation Agent *(The Daily Coach)*
Conducts natural, adaptive text-based dialogues across everyday and technical topics. Helps learners practice explaining tech projects, APIs, and cloud systems in English. Automatically adjusts language complexity to match the learner's current level and growth.

### 3. 🎭 Roleplay Agent *(The Career Simulator)*
Simulates high-stakes real-world English scenarios that Saudi tech learners face in their careers. Uses both short-term and long-term memory to maintain full context throughout each simulation session.

### 4. 📊 Feedback & Evaluation Agent *(The Intelligent Evaluator)*
Delivers instant, detailed feedback on learner responses. Powered by a RAG system that pulls grounded grammar guidelines and professional communication templates from the knowledge base.

---

## 🧠 Memory System

FluentTech uses a two-layer memory architecture to create a truly personalized experience:

```
┌─────────────────────────────────────────────────┐
│              SHORT-TERM MEMORY                  │
│           (LangGraph Session State)             │
│                                                 │
│  • Current conversation topic                   │
│  • Recent learner responses                     │
│  • In-session feedback history                  │
│  • Active roleplay context                      │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              LONG-TERM MEMORY                   │
│              (PostgreSQL DB)                    │
│                                                 │
│  • Learner profile & CEFR level                 │
│  • Learning goals & preferences                 │
│  • Recurring grammar mistakes                   │
│  • Completed sessions & tasks                   │
│  • Progress history & scores                    │
│  • Upcoming learning objectives                 │
└─────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Agent Framework** | LangGraph + LangChain |
| **LLM** | OpenAI |
| **Backend API** | FastAPI |
| **Database** | PostgreSQL |
| **Vector Store** | Supabase pgvector |
| **Frontend** | React |
| **Authentication** | Supabase Auth |
| **Containerization** | Docker + Docker Compose |
| **Deployment** | Render (Backend) · Vercel (Frontend) |

---
