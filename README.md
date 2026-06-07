<div align="center">

#  FluentTech — AI English Learning Agent
### *A personalized English coaching system built for Saudi tech learners*
</div>

---

## 📌 Overview

**FluentTech** is an agentic AI-powered English learning coach designed specifically for Saudi students and early-career tech professionals. Unlike generic language learning apps, EduLingo focuses on **career-oriented, practical English** — helping learners prepare for technical job interviews, workplace communication, and professional presentations.

The system leverages a **multi-agent architecture** built with LangGraph, where four specialized AI agents collaborate to deliver a personalized, adaptive learning experience that remembers the learner's goals, tracks their progress, and adjusts difficulty over time.

---

## 🎯 The Problem

Many English learning tools fail tech learners because they are either too generic or too rigid. Saudi tech students specifically face these challenges:

- No clear understanding of their current English level
- Lack of speaking and conversation practice opportunities  
- No personalized feedback on grammar, vocabulary, or professional tone
- No simulation of real career scenarios like technical interviews or workplace meetings
- Learning goals that are never tracked or revisited

EduLingo solves all of this through a conversational AI coach that remembers, adapts, and grows with the learner.

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
│  PostgreSQL │   │    LANGGRAPH ENGINE    │   │    CHROMA DB      │
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

**Responsibilities:**
- CEFR level assessment (A1 → C2)
- Goal-setting conversations
- Weekly learning plan generation
- Progress tracking and reporting
- High-level routing via the Supervisor Node

---

### 2. 💬 Conversation Agent *(The Daily Coach)*
Conducts natural, adaptive text-based dialogues across everyday and technical topics. Helps learners practice explaining tech projects, APIs, and cloud systems in English. Automatically adjusts language complexity to match the learner's current level and growth.

**Practice Modes:**
- Daily conversation
- Technical project explanation
- Workplace communication
- Email writing assistance

---

### 3. 🎭 Roleplay Agent *(The Career Simulator)*
Simulates high-stakes real-world English scenarios that Saudi tech learners face in their careers. Uses both short-term and long-term memory to maintain full context throughout each simulation session.

**Scenarios include:**
- Technical job interviews (*"Tell me about yourself"*)
- Cross-functional sprint meetings
- Client update calls
- Salary expectation discussions
- Recruiter screening calls
- Project presentations

---

### 4. 📊 Feedback & Evaluation Agent *(The Intelligent Evaluator)*
Delivers instant, detailed feedback on learner responses. Powered by a RAG system that pulls grounded grammar guidelines and professional communication templates from the knowledge base.

**Evaluates across 4 core metrics:**

| Metric | Description |
|--------|-------------|
| Grammar Accuracy | Correctness of grammatical structures |
| Vocabulary Range | Appropriateness and variety of word choice |
| Clarity & Structure | Logical flow and sentence organization |
| Professional Tone | Workplace-readiness of communication style |

> Also computes an overall **Job Readiness Score (0–100)**

---

## 🧠 Memory System

EduLingo uses a two-layer memory architecture to create a truly personalized experience:

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

## 📚 RAG Knowledge Base

The Retrieval-Augmented Generation system grounds the agents' responses in structured, curated content:

| Knowledge File | Content |
|----------------|---------|
| `cefr_levels.md` | Full A1–C2 level descriptors and benchmarks |
| `grammar_rules.md` | Top 50 grammar rules with examples |
| `interview_qa.md` | 30 interview questions with model answers |
| `technical_vocab.md` | AI, Cloud, Data & Software vocabulary |
| `arabic_mistakes.md` | Common errors made by Arabic speakers |
| `email_templates.md` | Professional email structures |
| `presentation_phrases.md` | Phrases for tech presentations & meetings |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Agent Framework** | LangGraph + LangChain |
| **LLM** | OpenAI GPT-4o or mistralai/Mistral-7B-Instruct-v0.3|
| **Backend API** | FastAPI |
| **Database** | PostgreSQL |
| **Vector Store** | ChromaDB |
| **Embeddings** | OpenAI text-embedding-3-small or BAAI/bge-small-en-v1.5 |
| **Frontend** | React |
| **Authentication** | JWT |
| **Containerization** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |
| **Deployment** | Railway (Backend) · Vercel (Frontend) · Supabase (DB) |

---

## 📁 Project Structure

```
edulingo/
│
├── agents/                     # LangGraph agent definitions
│   ├── supervisor.py           # Supervisor node + routing logic
│   ├── learning_agent.py       # Learning & Progress Agent
│   ├── conversation_agent.py   # Conversation Agent
│   ├── roleplay_agent.py       # Roleplay Agent
│   └── feedback_agent.py       # Feedback & Evaluation Agent
│
├── tools/                      # Agent tools
│   ├── profile_tool.py         # Learner profile CRUD
│   ├── progress_tool.py        # Progress tracking
│   └── exercise_tool.py        # Exercise generation
│
├── rag/                        # RAG pipeline
│   ├── knowledge_base/         # Source documents
│   ├── ingest.py               # Chunking + embedding pipeline
│   └── retriever.py            # Chroma retriever
│
├── backend/                    # FastAPI application
│   ├── main.py                 # App entry point
│   ├── routes/                 # API route handlers
│   ├── models/                 # DB models (SQLAlchemy)
│   ├── schemas/                # Pydantic schemas
│   └── auth/                   # JWT authentication
│
├── frontend/                   # React application
│   ├── src/
│   │   ├── pages/              # Chat, Profile, Dashboard
│   │   ├── components/         # Reusable UI components
│   │   └── api/                # API integration layer
│
├── db/
│   └── schema.sql              # PostgreSQL schema
│
├── docker-compose.yml          # Full stack orchestration
├── Dockerfile.backend
├── Dockerfile.frontend
├── .env.example
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- OpenAI API Key

### 1. Clone the repository
```bash
git clone https://github.com/Sarahalo204/FluentTech.git
cd FluentTech
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and add your API keys
```

```env
OPENAI_API_KEY=your_openai_key
or
huggingfacehub_api_token=your_HF_TOKEN
DATABASE_URL=postgresql://user:password@localhost:5432/edulingo
CHROMA_PATH=./rag/chroma_store
JWT_SECRET=your_secret_key

```

### 3. Run with Docker
```bash
docker-compose up --build
```

### 4. Ingest the knowledge base
```bash
docker exec edulingo-backend python rag/ingest.py
```
---

## 🗺️ CEFR Level Reference

The system uses the Common European Framework of Reference for Languages:

| Level | Label | Description |
|-------|-------|-------------|
| A1 | Beginner | Basic phrases and introductions |
| A2 | Elementary | Simple everyday communication |
| B1 | Intermediate | Can handle most travel/work situations |
| B2 | Upper Intermediate | Clear, detailed communication on complex topics |
| C1 | Advanced | Fluent, flexible, effective language use |
| C2 | Proficient | Near-native mastery and precision |

---

## 📡 API Reference

```
POST   /api/auth/register          Register a new learner
POST   /api/auth/login             Login and receive JWT token

GET    /api/learner/{id}/profile   Get full learner profile
PUT    /api/learner/{id}/profile   Update profile or goals

POST   /api/session/start          Start a new learning session
POST   /api/session/message        Send a message to the active agent
POST   /api/session/end            End session and save progress

GET    /api/progress/{id}/summary  Get weekly progress summary
GET    /api/progress/{id}/mistakes Get recurring mistakes report

POST   /api/exercise/generate      Generate a personalized exercise
POST   /api/feedback/analyze       Analyze text and return evaluation

GET    /api/health                 Health check
```

---

## 🎯 Target Users

| User | Goal |
|------|------|
| **Saudi Tech Student** | Improve English for job search & interviews |
| **Early-Career Developer** | Practice technical communication in English |
| **Bootcamp Graduate** | Build confidence for workplace English |
| **Career Coach / Instructor** | Monitor learner progress and engagement |

---
