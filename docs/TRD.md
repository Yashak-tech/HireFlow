# HireFlow — Technical Requirements Document (TRD)

---

## 1. Executive Technical Summary & Scope
This Technical Requirements Document (TRD) locks the technical architecture, technology stack, data schemas, security guardrails, and operational standards for **HireFlow**.

The technical design directly operationalizes the product specifications outlined in [`PRD.md`](PRD.md) while strictly abiding by the lessons and constraints documented in [`REFERENCE_ANALYSIS.md`](REFERENCE_ANALYSIS.md).

> **Hackathon Feasibility Principle:**  
> The stack is deliberately lean, highly reliable, and free of over-engineered or brittle external multi-agent runtimes. It leverages battle-tested tools to ensure a deterministic, demo-ready, end-to-end recruitment workflow.

---

## 2. Locked Technology Stack

```mermaid
flowchart TB
    subgraph Client Layer
        UI[React 18 + Vite + Tailwind CSS]
        State[Zustand Store / React Query]
    end

    subgraph API & Orchestration Layer
        FastAPI[FastAPI Backend Python 3.11+]
        Orchestrator[Modular Agent Orchestrator]
        RepairLoop[Pydantic v2 Self-Healing Parsing]
    end

    subgraph Intelligence & Embeddings
        LLM[OpenAI API gpt-4o-mini / gpt-4o]
        Embeddings[text-embedding-3-small]
    end

    subgraph Data & Storage Layer
        DB[(PostgreSQL + pgvector / Supabase)]
        FileStore[Local UUID File Storage / S3]
    end

    UI <-->|REST JSON & SSE Streaming| FastAPI
    FastAPI --> Orchestrator
    Orchestrator --> RepairLoop
    RepairLoop <--> LLM
    Orchestrator <--> Embeddings
    FastAPI <--> DB
    FastAPI <--> FileStore
```

### 2.1 Frontend
- **Framework:** React 18 (or 19) initialized with **Vite**.
- **Styling:** **Tailwind CSS v3** supplemented with custom CSS custom properties for a cohesive, modern dark/light recruitment theme.
- **Icons & Visuals:** `lucide-react` for crisp SVG iconography.
- **State Management:** **Zustand** for global application state (active job requisition, selected candidate, active interview session).
- **HTTP Client:** `fetch` / `axios` with typed response envelopes; Server-Sent Events (`EventSource`) for real-time interview transcripts and progress streaming.
- **File Ingestion:** Client-side drag-and-drop file upload with validation (PDF, DOCX, TXT, max 10MB).

### 2.2 Backend
- **Framework:** **FastAPI** (Python 3.11+), executed with **Uvicorn**.
- **Data Validation & Schemas:** **Pydantic v2** for all domain models, request/response bodies, and LLM structured extraction validation.
- **Concurrency & Tasks:** Native Python `asyncio` for non-blocking I/O; FastAPI `BackgroundTasks` for asynchronous post-interview grading and embedding generation.
- **Package Manager:** `pip` with pinned `requirements.txt`.

### 2.3 Database & Vector Storage
- **Primary Database:** **PostgreSQL 15+** (Supabase-compatible or local PostgreSQL).
- **Vector Search:** **`pgvector`** extension running natively within PostgreSQL.
  - Eliminates the operational complexity and cost of maintaining a separate standalone vector database.
  - Cosine distance index (`HNSW` or `IVFFlat`) for rapid candidate-to-job matching.
- **ORM & Migrations:** **SQLAlchemy 2.0** with **Alembic** for explicit, tracked database schema migrations.

### 2.4 Authentication
- **Hackathon Implementation:** Lightweight Bearer Token / API Key authentication with a pre-configured **Demo Recruiter Switch** (`Sarah Jenkins - Senior Recruiter`, `Marcus Vance - Engineering Director`).
- **Production Path:** Supabase Auth / JWT authentication with role-based access control (`recruiter`, `hiring_manager`, `admin`).

### 2.5 LLM Provider & Tool Calling
- **Primary Provider:** **OpenAI API** (`gpt-4o-mini` for high-throughput extraction/state transitions, `gpt-4o` for deep evaluation, gap analysis, and rubric grading).
- **Alternative / Fallback:** Compatible with OpenAI-standard endpoints (OpenRouter, Groq, or Gemini via OpenAI compatibility layer).
- **Structured Outputs & Tool Calling:**
  - Enforced JSON mode (`response_format={"type": "json_object"}`) validated strictly against Pydantic schemas.
  - Native function/tool calling for structured agent actions.

### 2.6 Embedding Model
- **Primary Model:** OpenAI **`text-embedding-3-small`** (1536 dimensions) for dense semantic vector representations of job requirements and candidate profiles.
- **Offline / Local Fallback:** `sentence-transformers` (`all-MiniLM-L6-v2`, 384 dimensions) for running fully offline without external API dependencies.

### 2.7 Document Parsing
- **PDF Extraction:** **`pypdf`** and **`pdfplumber`** for robust text extraction across diverse resume formats (multi-column, tables, varied fonts).
- **DOCX Extraction:** **`python-docx`** for structured text extraction from Microsoft Word documents.
- **Plain Text / Markdown:** Native Python file readers with UTF-8 normalization.

### 2.8 Agent Orchestration
- **Architecture:** A **modular, stateful pipeline orchestrator** built in native Python/FastAPI rather than heavy or brittle frameworks (avoids AutoGen termination bugs or LangChain version instability).
- **Execution Lifecycle:**
  1. *Sequential Ingestion:* Raw document text extraction $\to$ Pydantic schema validation $\to$ Vector embedding generation.
  2. *Bias & Inclusivity Audit:* Job description scan $\to$ Bias risk score $\to$ Inclusive rewrite suggestions.
  3. *Two-Stage Candidate Matching:* Stage 1 (Vector cosine retrieval via `pgvector`) $\to$ Stage 2 (Deterministic heuristic re-ranking on skill overlap & experience).
  4. *Gap-Driven Interview Preparation:* Candidate resume gaps $\to$ 5-category question roadmap $\to$ Pre-generated objective scoring rubric.
  5. *Candidate Screening State Machine:* Turn-taking controller $\to$ Barge-in & clarification handling $\to$ Anti-tampering check.
  6. *Post-Interview Evaluation:* Asynchronous rubric scoring $\to$ Unified candidate dossier compilation $\to$ Recruiter decision gate.

### 2.9 File Storage
- **Local Runtime:** Local structured directory (`uploads/resumes/`, `uploads/reports/`) with UUID filenames to prevent collision.
- **Cloud Target:** Supabase Storage bucket / AWS S3 bucket with secure presigned URLs.

### 2.10 Deployment & Runtime
- **Containerization:** **Docker & Docker Compose** defining three unified services:
  1. `hireflow-db`: PostgreSQL 16 with `pgvector` pre-installed.
  2. `hireflow-api`: FastAPI backend running under Uvicorn.
  3. `hireflow-web`: React + Vite frontend served via Node/Nginx.
- **Cloud Deployment Paths:**
  - Frontend: Vercel / Netlify.
  - Backend: Render / Railway / AWS ECS.
  - Database: Supabase / Neon (PostgreSQL + pgvector).

---

## 3. Data Architecture & Database Schema

```mermaid
erDiagram
    JOBS ||--o{ CANDIDATES : "evaluates"
    JOBS ||--o{ INTERVIEW_SESSIONS : "associated with"
    CANDIDATES ||--o{ INTERVIEW_SESSIONS : "participates in"
    INTERVIEW_SESSIONS ||--o{ INTERVIEW_TURNS : "contains"
    INTERVIEW_SESSIONS ||--|| CANDIDATE_DOSSIERS : "yields"
    JOBS ||--o{ LLM_AUDIT_LOGS : "generates"

    JOBS {
        uuid id PK
        string title
        string department
        text raw_description
        jsonb parsed_criteria
        float bias_risk_score
        jsonb bias_findings
        text optimized_description
        vector embedding
        timestamp created_at
    }

    CANDIDATES {
        uuid id PK
        string full_name
        string email
        string phone
        text raw_resume_text
        jsonb parsed_profile
        vector embedding
        timestamp created_at
    }

    INTERVIEW_SESSIONS {
        uuid id PK
        uuid job_id FK
        uuid candidate_id FK
        string status
        jsonb identified_gaps
        jsonb interview_roadmap
        jsonb evaluation_rubric
        boolean tamper_flag
        timestamp started_at
        timestamp completed_at
    }

    INTERVIEW_TURNS {
        uuid id PK
        uuid session_id FK
        int turn_number
        string speaker
        text message_text
        string decision_code
        timestamp timestamp
    }

    CANDIDATE_DOSSIERS {
        uuid id PK
        uuid session_id FK
        float match_score
        float interview_score
        text executive_summary
        jsonb matched_skills
        jsonb missing_skills
        jsonb rubric_breakdown
        string recommendation
        string human_decision
        text recruiter_notes
        timestamp updated_at
    }

    LLM_AUDIT_LOGS {
        uuid id PK
        string agent_name
        string model_name
        int prompt_tokens
        int completion_tokens
        float latency_ms
        float estimated_cost
        string status
        timestamp created_at
    }
```

---

## 4. API Specification & Communication Protocols

All client-backend communication is over HTTPS using RESTful JSON conventions, with Server-Sent Events (SSE) for real-time telemetry.

### Core Endpoints

| Method | Endpoint | Purpose | Request Payload | Response Payload |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/jobs` | Ingest JD & run bias audit | Multipart form / JSON text | Structured JD, bias risk score, inclusive rewrites, job ID |
| `POST` | `/api/candidates/upload` | Upload & parse resume | Multipart form (`file: PDF/DOCX`) | Structured candidate profile, candidate ID |
| `POST` | `/api/matching/{job_id}` | Two-stage candidate matching | Optional threshold filters | Ranked candidate list with match scores, reasoning, gaps |
| `POST` | `/api/interviews/prepare` | Synthesize roadmap & rubric | `{ job_id, candidate_id }` | 5-category roadmap, objective rubric, session ID |
| `POST` | `/api/interviews/turn` | Process screening turn | `{ session_id, candidate_input }` | AI response, current state, tamper flag, next action |
| `GET` | `/api/interviews/stream/{sid}`| Stream live interview feed | None (SSE stream) | Real-time events: `transcript`, `progress`, `turn_update` |
| `POST` | `/api/interviews/finalize` | Grade transcript & generate dossier | `{ session_id }` | Full candidate dossier, rubric breakdown, verdict |
| `POST` | `/api/dossiers/{id}/decision`| Record human recruiter decision | `{ decision: ADVANCE/REJECT, notes }` | Updated dossier confirmation |
| `GET` | `/api/observability/stats` | Audit telemetry & token burn | None | Aggregate calls, token burn, latency percentiles, cost |

---

## 5. Resilient Error Handling & Self-Healing Repair Loop

To prevent brittle JSON crashes (a critical failure mode identified in reference projects):

1. **The Pydantic Self-Healing Repair Loop:**
   - When an LLM structured completion fails Pydantic schema validation or JSON decoding:
     1. Capture the exact validation error message and invalid output.
     2. Re-prompt the model:  
        `"Your previous output failed schema validation: {validation_error}. Re-output ONLY valid JSON matching the exact schema."`
     3. Retry up to **3 attempts**.
     4. If still invalid after 3 attempts, escalate with a structured fallback response and log an audit error alert.
2. **Deterministic Fallbacks:**
   - If PDF parsing fails due to scanned images, return an actionable HTTP 422: `"Unreadable PDF: Please provide a text-based PDF or DOCX format."`
3. **Transport Resilience:**
   - Exponential backoff with jitter on upstream LLM API rate limits (HTTP 429) or transient 5xx provider failures.

---

## 6. Security, AI Safety & Anti-Tampering

1. **Prompt Injection & Anti-Tamper Guardrails:**
   - Every candidate input in the screening state machine is evaluated against an adversarial intent classifier:
     - *Tamper Rules:* Instruction overrides (`"Ignore previous instructions"`), prompt extractions (`"Repeat your system prompt"`), jailbreaks, or abusive content.
     - *Action:* If triggered, the session sets `tamper_flag = true`, ends the interaction gracefully, and permanently marks the dossier with an `Integrity Violation` tag.
2. **Demographic Masking for Bias Elimination:**
   - Resumes are parsed into an anonymized evaluation payload (stripping candidate name, gender pronouns, physical address, graduation years, and photo links) before being sent to the scoring agent.
3. **File Ingestion Safety:**
   - MIME type validation and file signature inspection.
   - Max file size capped at 10MB.
   - Files stored with sanitized UUIDs on disk to prevent path traversal attacks (`../../`).

---

## 7. Auditability, Telemetry & Logging

1. **Full Decision Provenance:**
   - Every candidate scorecard links back to the specific job requisition snapshot, resume document snapshot, model ID, and prompt version used.
2. **Inference Telemetry:**
   - Every LLM invocation records:
     - `agent_name` (e.g., `JDBiasAuditor`, `CandidateScorer`, `RubricEvaluator`).
     - `prompt_tokens` and `completion_tokens`.
     - `latency_ms`.
     - `estimated_cost` (calculated from model rate cards).
3. **Human Action Audit Trail:**
   - Immutable audit logging of human overrides, edits to interview questions, and final hiring verdicts with timestamps and user identifiers.

---

## 8. Testing & Validation Strategy

1. **Automated Unit & Schema Tests (`pytest`):**
   - Pydantic schema validation tests ensuring invalid JSON strings trigger repair logic.
   - Heuristic re-ranking unit tests validating mathematical scoring formulas.
   - Anti-tampering unit tests confirming adversarial inputs trigger `tamper_flag`.
2. **End-to-End Workflow Integration Test:**
   - Automated end-to-end integration test (`tests/test_e2e_workflow.py`):
     - Ingest mock JD $\to$ Upload mock resume $\to$ Verify match scorecard $\to$ Generate roadmap $\to$ Simulate screening turns $\to$ Verify final dossier.
3. **Golden Evaluation Dataset:**
   - Benchmark suite of 5 diverse candidate resumes (ranging from ideal match to mismatched to adversarial) to evaluate scoring consistency and bias neutrality across model updates.

---

## 9. Environment Variables Specification

All configuration is managed strictly through `.env` files.

```ini
# =====================================================================
# Server & Environment Configuration
# =====================================================================
ENVIRONMENT=development
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS="http://localhost:5173,http://localhost:3000"
SECRET_KEY="hireflow-hackathon-insecure-dev-secret-change-in-prod"

# =====================================================================
# Database & Vector Configuration
# =====================================================================
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/hireflow"
PGVECTOR_DISTANCE_STRATEGY="cosine"

# =====================================================================
# AI / LLM Configuration
# =====================================================================
OPENAI_API_KEY="sk-..."
OPENAI_MODEL_FAST="gpt-4o-mini"
OPENAI_MODEL_REASONING="gpt-4o"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

# =====================================================================
# File Storage Configuration
# =====================================================================
UPLOAD_DIR="./uploads"
MAX_UPLOAD_SIZE_MB=10

# =====================================================================
# Observability & Cost Tracking
# =====================================================================
ENABLE_AUDIT_LOGGING=true
COST_PER_1K_PROMPT_TOKENS=0.00015
COST_PER_1K_COMPLETION_TOKENS=0.00060
```

---

## 10. Constraints & Rules (Strict Architectural Boundaries)

The development of HireFlow must adhere to the following non-negotiable rules:

1. **READ-ONLY References:**
   - Repositories in `/references` are strictly read-only. No code, prompts, CSS classes, or assets from `/references` may be copied, pasted, or directly reproduced.
2. **No Over-Engineered External Agent Frameworks:**
   - Do NOT use AutoGen, CrewAI, LangChain, or Google ADK.
   - Orchestration must be handled via clean, deterministic, stateful Python services in FastAPI.
3. **No Unvalidated Black-Box Scoring:**
   - Every single score output (0–100) must be accompanied by explicit, grounded citations of evidence, confirmed matched competencies, and missing gaps.
4. **No Autonomous Hiring Decisions:**
   - The platform will never trigger candidate rejections or advancements automatically. The human recruiter must explicitly click confirmation buttons.
5. **No Ephemeral In-Memory State for Primary Data:**
   - All jobs, candidates, interview sessions, and audit logs must be persisted in PostgreSQL. In-memory storage is strictly prohibited for business entities.
6. **No Unnecessary External Dependencies:**
   - Avoid introducing Redis, Celery, Kafka, or separate vector databases (Pinecone, Qdrant). PostgreSQL + `pgvector` and native Python `asyncio` cover all queueing, vector search, and relational needs for the hackathon.
7. **Strict Pydantic Validation:**
   - Every LLM response intended for application logic must pass Pydantic schema validation through the self-healing retry loop. No raw unvalidated strings may drive application workflows.
8. **Demo-Readiness:**
   - The entire platform must be runnable via a single command (`docker-compose up` or simple local scripts) and include seeded demo data for rapid judging and evaluation.

---

## Summary Approval
This TRD defines the locked technical contract for **HireFlow**. All subsequent implementation steps (data models, backend routers, agent services, and frontend interfaces) must strictly align with the specifications and constraints set forth in this document.
