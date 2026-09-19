# HireFlow

## AI Recruitment Intelligence Agent

> **HireFlow** is an auditable, agentic AI recruitment copilot that transforms hiring workflows from reactive resume screening to proactive, structured, evidence-grounded candidate evaluation with strict **Human-in-the-Loop governance**.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4+-646CFF.svg)](https://vitejs.dev/)
[![Backend Tests](https://img.shields.io/badge/backend%20tests-70%2F70%20passed-brightgreen.svg)]()
[![Frontend Build](https://img.shields.io/badge/frontend-production%20build%20passing-brightgreen.svg)]()

---

## Problem

Modern talent acquisition teams face acute operational and analytical challenges:

- **Resume Screening is Time-Consuming**: Recruiters spend hours scanning hundreds of resumes per requisition, leading to recruiter fatigue and overlooked high-potential talent.
- **Candidate Information is Scattered**: Qualifications, work histories, verified skills, and interview feedback are siloed across disconnected tools and unstructured documents.
- **Matching is Inconsistent**: Keyword-matching algorithms fail to capture semantic domain equivalence, seniority context, and transferable skills.
- **Interviews Lack Gap-Focus**: Standard interview loops ask generic questions instead of systematically probing specific candidate requirement gaps or unverifiable claims.
- **Evaluations Lack Verifiable Evidence**: Subjective impressions often dominate hiring discussions without transparent provenance linking candidate claims to primary source records.

---

## Solution

HireFlow provides an end-to-end recruitment intelligence platform that assists recruiters across the entire hiring lifecycle:

- **Job Description Intelligence**: Automatically decomposes complex job requisitions into structured atomic requirements, assigns priority weights, and flags DEI bias risks.
- **Resume Intelligence**: Parses unstructured PDF/DOCX/TXT resumes into structured career profiles, skills, and anonymized candidate summaries.
- **Evidence & Provenance**: Grounds all candidate claims with exact verbatim quotations and provenance pointers to primary source documents.
- **Candidate Matching**: Computes hybrid 2-stage match scores combining semantic vector embeddings and weighted requirement coverage.
- **Requirement Gap Analysis**: Automatically highlights requirement gaps and unverifiable claims for every applicant.
- **Adaptive Screening Interviews**: Dynamically synthesizes personalized interview question plans and adaptive follow-up probes tailored to candidate gaps.
- **Multi-Dimensional Interview Evaluation**: Evaluates interview responses across Technical Depth, Communication Clarity, and Problem Solving with rubric-backed scoring.
- **Human Decision Gate**: Enforces a recruiter-controlled decision workflow (Advance, Hold, Reject) with rationale logging.
- **Audit & Telemetry**: Records every matching computation, AI evaluation, and human decision in a tamper-evident audit ledger.

> **IMPORTANT:**  
> **HireFlow is decision-support software.**  
> The AI provides analysis, match calculations, gap probes, and scoring recommendations, but **never autonomously makes final hiring decisions**. All progression, rejection, and offer decisions require explicit human authorization.

---

## Key Features

### 1. Job Description Intelligence
Transforms raw job descriptions into structured requisitions with classified atomic requirements (skill, experience, education, domain), required vs. preferred criteria, priority weights, and automated DEI bias detection with inclusive language suggestions.

### 2. Resume Intelligence
Ingests PDF, DOCX, and TXT files, extracting candidate contact details, work history, education, verified skills, and career milestones. Generates anonymized candidate summaries (stripping PII, gender markers, and graduation years) to minimize cognitive screening bias.

### 3. Evidence & Provenance
Eliminates AI hallucinations by linking every matched skill or requirement directly to exact, verbatim source text from the candidate's resume or interview transcript.

### 4. Candidate Matching
Executes a multi-factor hybrid matching engine combining dense vector embeddings (`text-embedding-3-small` / cosine similarity) and weighted atomic requirement fulfillment, yielding an overall 0–100 match score and categorized breakdown.

### 5. Adaptive Interview Intelligence
Generates targeted 45-minute structured interview roadmaps with role-specific core questions and intelligent follow-up gap probes dynamically chosen based on missing candidate qualifications.

### 6. Interview Evaluation
Analyzes interview responses against structured rubrics, computing composite scores across Technical Depth (40%), Communication Clarity (30%), and Problem Solving (30%), accompanied by synthesized strengths and improvement areas.

### 7. Human Decision Gate
Provides an interactive review workflow where hiring managers and recruiters record their final decision (`advance`, `hold`, `reject`) along with structured human rationale.

### 8. Audit & Telemetry
Maintains a tamper-evident, append-only audit trail capturing system events, match calculations, interview assessments, human decisions, and prompt safety checks with cryptographic run hashes.

### 9. Dashboard KPIs
Presents real-time recruitment analytics including Active Requisitions, Total Candidates Screened, Average Match Quality, Stage Conversion Rates, and Diversity/Bias metrics.

### 10. Demo Data
Includes a one-click seed mechanism that populates realistic requisitions, diverse candidates, hybrid match scores, interview transcripts, and rubric evaluations for instant evaluation.

---

## How It Works

```
┌────────────────────────────────┐
│        Job Description         │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐       ┌────────────────────────────────┐
│      Document Intelligence     │◄──────┤        Candidate Resumes       │
│  (Atomic Criteria Extraction)  │       │     (PDF / DOCX / Text)        │
└────────────────┬───────────────┘       └────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│      Evidence & Provenance     │
│   (Verbatim Grounding Anchor)  │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│       Candidate Matching       │
│   (Vector + Weighted Skills)   │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│   Adaptive Screening Interview │
│    (Targeted Gap Probing)      │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│      Interview Evaluation      │
│  (Rubric Scoring & Strengths)  │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│      Human Decision Gate       │
│   (Recruiter Advance / Reject) │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│          Audit Trail           │
│     (Tamper-Evident Ledger)    │
└────────────────────────────────┘
```

---

## Architecture

HireFlow is structured as a modern decoupled full-stack architecture:

- **Frontend**: Single-Page Application (SPA) built with **React 18**, **Vite**, and **Tailwind CSS**, featuring responsive glassmorphic cards, candidate detail modals, live interview workspaces, and audit dashboards.
- **Backend**: Asynchronous RESTful API service built with **Python 3.11+** and **FastAPI**, featuring modular routers, Pydantic data contracts, and dependency injection.
- **Database & Persistence**: Built on **PostgreSQL / Supabase** with `pgvector` for vector storage, featuring automatic SQLite asynchronous fallback (`aiosqlite`) for zero-dependency local development and testing.
- **AI & LLM Services**: Integrated with **OpenAI GPT-4o / GPT-4o-mini** and LiteLLM, backed by deterministic rule-based heuristic fallbacks ensuring uninterrupted operation even without live API credentials.
- **Embeddings & Vector Matching**: Uses OpenAI `text-embedding-3-small` with local cosine similarity fallback for semantic resume-to-job matching.
- **Document Processing**: Robust multi-format parsing pipeline supporting PDF (`pypdf`), Word (`python-docx`), and raw text files.

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18.3, Vite 5.4, Tailwind CSS, Lucide React, Axios |
| **Backend** | Python 3.11+, FastAPI 0.115+, Uvicorn, Pydantic v2 |
| **Database & ORM** | PostgreSQL (Supabase) with pgvector, SQLite (`aiosqlite`), SQLAlchemy 2.0 Async |
| **AI / LLM Layer** | OpenAI GPT-4o / GPT-4o-mini, LiteLLM (with deterministic heuristic fallback) |
| **Embeddings** | OpenAI `text-embedding-3-small` (with local vector math fallback) |
| **Document Processing** | `pypdf`, `python-docx` |
| **Testing** | `pytest`, `pytest-asyncio`, `httpx` |
| **Security & Auth** | JWT Authentication, Tenant Isolation (`org_id` scoping), Password Hashing |

---

## Project Structure

```
HireFlow/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI screening controller, planner, evaluator, match engine
│   │   ├── core/            # Config, database engine, security & authentication
│   │   ├── models/          # SQLAlchemy async models (Job, Candidate, Resume, Interview, Audit)
│   │   ├── routers/         # FastAPI API endpoints (jobs, candidates, interviews, audit, stats, demo)
│   │   ├── schemas/         # Pydantic request and response schemas
│   │   └── services/        # Resume extraction, JD intelligence, LLM provider, audit logging
│   ├── scripts/             # Demo seeding and database utility scripts
│   ├── tests/               # 70 automated unit and integration tests
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # UI Views (Jobs, Candidates, InterviewWorkspace, AuditDashboard, etc.)
│   │   ├── App.jsx          # Root application shell, navigation, and persona context
│   │   └── index.css        # Core styling and Tailwind tokens
│   ├── package.json         # Frontend dependencies and scripts
│   └── vite.config.js       # Vite bundler configuration and API proxy
├── docs/                    # Architecture documentation (PRD, TRD, APP_FLOW, SCHEMA)
├── .env.example             # Safe environment variable configuration template
└── README.md                # Project documentation
```

---

## Getting Started

### Prerequisites

- **Python**: Version 3.11 or higher
- **Node.js**: Version 18.0 or higher
- **npm**: Version 9.0 or higher
- **Git**: Installed and configured

### Clone the Repository

```bash
git clone https://github.com/Yashak-tech/HireFlow.git
cd HireFlow
```

---

### Backend Setup

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp ../.env.example ../.env

# 5. Start the FastAPI development server
uvicorn app.main:app --reload --port 8000
```

The backend server will start at `http://localhost:8000`.
- **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### Frontend Setup

```bash
# 1. In a new terminal, navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start the Vite development server
npm run dev
```

The frontend application will be live at `http://localhost:5173`.

---

### Environment Variables

Configure your local `.env` file based on `.env.example`:

```env
# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
SECRET_KEY=your_secure_secret_key_here

# Database (Leave blank or use default for automatic SQLite async fallback)
DATABASE_URL=sqlite+aiosqlite:///./hireflow.db

# AI / LLM Configuration (Optional: Heuristic fallback is used if omitted)
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

---

## Demo Walkthrough

1. **Select Persona**: Switch between **Sarah Jenkins** (Senior Technical Recruiter) and **Marcus Vance** (Hiring Manager) via the top navigation bar.
2. **Seed Demo Data**: Click the **"⚡ Seed Demo Data"** button in the top navigation bar to populate realistic jobs, diverse applicants, match scores, and interview records.
3. **Explore Requisitions**: Navigate to **Jobs** to inspect decomposed atomic requirements, importance weights, and DEI bias check scores.
4. **Review Candidates**: Open the **Candidates** pipeline to view parsed profiles, verified skills, and bias-masked summaries.
5. **Inspect Hybrid Match & Evidence**: Click on a candidate to view the 0–100 match score breakdown with grounded verbatim evidence quotes.
6. **Conduct Adaptive Interview**: Open the **Interview** tab to review the structured 45-minute interview roadmap and simulate candidate gap probing.
7. **Examine Rubric Evaluations**: Review multi-dimensional scoring across Technical Depth, Communication, and Problem Solving with synthesized strengths.
8. **Make Human Decision**: Record an authorized human decision (**Advance**, **Hold**, or **Reject**) with mandatory recruiter rationale.
9. **Audit Trail**: Open the **Audit & Compliance** dashboard to view tamper-evident records of all system and human events.

---

## Demo Credentials

> Demo credentials and authentication tokens should be provided separately for hackathon evaluation. The local development environment includes pre-configured authenticated session personas for seamless testing.

---

## API Overview

HireFlow exposes a structured RESTful API under `/api`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and database connectivity |
| `POST` | `/api/auth/login` | Authenticate user and issue JWT access token |
| `GET` | `/api/auth/me` | Retrieve current authenticated user persona |
| `GET` | `/api/jobs` | List active job requisitions for the organization |
| `POST` | `/api/jobs` | Create and decompose a new job description |
| `GET` | `/api/jobs/{id}` | Retrieve job details and atomic criteria |
| `GET` | `/api/candidates` | List candidate profiles and pipeline statuses |
| `POST` | `/api/candidates/upload` | Upload and parse resume (PDF, DOCX, TXT) |
| `GET` | `/api/candidates/{id}` | Get candidate details with grounded evidence |
| `POST` | `/api/candidates/{id}/match` | Calculate hybrid match against a specific job |
| `GET` | `/api/interviews` | List interview sessions and statuses |
| `POST` | `/api/interviews/generate` | Generate adaptive interview roadmap and questions |
| `POST` | `/api/interviews/{id}/evaluate` | Generate multi-dimensional rubric evaluation |
| `POST` | `/api/interviews/{id}/decision` | Record recruiter Human-in-the-Loop hiring decision |
| `GET` | `/api/stats/overview` | Retrieve dashboard KPI analytics |
| `GET` | `/api/audit/logs` | Fetch filtered, tamper-evident audit ledger |
| `POST` | `/api/demo/seed` | Seed realistic demo dataset (development only) |

---

## Testing & Verification

The codebase has undergone comprehensive automated testing across all architectural phases:

- **Backend Test Suite**: `70 / 70 tests passing` (`pytest`)
- **Frontend Build**: Production build passing (`vite build`) with 0 errors

To run the automated test suite locally:

```bash
cd backend
python -m pytest
```

---

## Human-in-the-Loop Safety

HireFlow is designed around explicit human governance principles:

1. **AI is Exclusively Advisory**: AI agents generate candidate match scores, identify requirement gaps, and propose interview questions, but **cannot autonomously hire or reject applicants**.
2. **Explicit Decision Gate**: Advancement or rejection in the recruitment pipeline requires a verified human recruiter action with mandatory decision rationale.
3. **Verifiable Provenance**: Recruiters can independently verify every AI assertion by viewing the highlighted source quotes from primary candidate records.

---

## Security & Compliance

- **Environment-Driven Secrets**: Zero hardcoded credentials or API keys; all sensitive parameters are managed through environment variables.
- **Multi-Tenant Isolation**: Database queries enforce strict organizational partitioning via `org_id` scoping.
- **PII & Bias Mitigation**: Automated redaction of candidate demographic markers during initial screening stages.
- **Production Guardrails**: Demo seeding and mutating debug endpoints are guarded and disabled in production environments.
- **Audit Logging**: Immutable audit logging of all match calculations, AI assessments, and human actions.

---

## Hackathon

HireFlow was conceptualized, designed, and engineered for the **Agentic AI Hackathon**, demonstrating practical, reliable, and ethical multi-agent AI workflows in enterprise recruitment.

---

## License

This project is open source and available under the [MIT License](LICENSE).
