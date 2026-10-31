# Apex Support AI — Intelligent Student Support Agent
### Autonomous Multi-Tool Agentic AI System with Production Security & Human Governance
**Agentic AI Engineering — Assignments 1 & 2 (Unified Continuous System)**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![FAISS Vector Store](https://img.shields.io/badge/Vector%20Store-FAISS-green.svg)](https://github.com/facebookresearch/faiss)
[![Streamlit UI](https://img.shields.io/badge/Frontend-Streamlit-red.svg)](https://streamlit.io/)
[![Security PBKDF2](https://img.shields.io/badge/Security-PBKDF2--HMAC--SHA256-blueviolet.svg)]()
[![Full Test Suite](https://img.shields.io/badge/Pytest-39%2F39%20Passed%20(100%25)-brightgreen.svg)]()
[![Benchmark Pass Rate](https://img.shields.io/badge/Assignment%201%20Eval-100%25%20(9%2F9%20Pass)-brightgreen.svg)]()

---

## 1. Executive Summary & Architecture Overview

**Apex Support AI** is a production-grade Agentic AI application combining **Assignment 1** (Autonomous Multi-Tool Agent, FAISS RAG, Long-Term Memory, and Observability) and **Assignment 2** (PBKDF2 Authentication, Default-Deny Authorization, Human-in-the-Loop Approval Workflows, and Immutable Audit Logging) into **one unified codebase and single Streamlit interface**.

Higher education institutions handle tens of thousands of sensitive queries regarding tuition fees, scholarships, payment gateway failures, and academic policies. Traditional chatbots either hallucinate policies, fail to access transactional student records, or dangerously expose student data without access control.

Apex Support AI solves these challenges with an autonomous, observable, and hardened multi-tier architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STREAMLIT ENTERPRISE UI                           │
│  💬 Chat Concierge  │ 📊 Telemetry  │ 🧠 Memory  │ 📚 RAG  │ 🔐 Login  │ ⚖️ Approvals │ 🛡️ Audit  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                         [Authenticated Session Identity]
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LANGGRAPH ORCHESTRATION ENGINE                        │
│                                                                             │
│  [1. Intent Analyzer] ──► Resolves Session Identity (Never Chat Text)       │
│           │                                                                 │
│           ├──► [2a. Tool Executor] ────► Security Gate: Owner Access Check  │
│           │                                   │                             │
│           │                                   ├── Allowed: Run Tool DB      │
│           │                                   └── Denied: Block & Log Audit │
│           │                                                                 │
│           ├──► [2b. Policy RAG] ───────► FAISS Semantic Search (Handbook)   │
│           │                                                                 │
│           └──► [2c. Memory Retriever] ──► SQLite Persistent Profile Memory  │
│                                                                             │
│  [3. Context Selector] ────► Filters relevant chunks & tool results         │
│  [4. LLM Synthesizer]  ────► Groq / OpenAI / Local Grounded Synthesis       │
│  [5. Trace Logger]     ────► SQLite Telemetry + Append-Only Audit Trail     │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
     ┌─────────────────────────────────┴─────────────────────────────────┐
     ▼                                                                   ▼
┌──────────────────────────────────┐               ┌──────────────────────────────────┐
│      SQLITE DATABASE (WAL)       │               │       FAISS VECTOR STORE         │
│ • students                       │               │ • all-MiniLM-L6-v2 Embeddings    │
│ • fee_records                    │               │ • Student Handbook PDF Chunks    │
│ • scholarships                   │               │ • Chunk IDs & Page Numbers       │
│ • support_tickets                │               └──────────────────────────────────┘
│ • user_credentials (PBKDF2)      │
│ • approval_requests (Pending/Ex) │
│ • audit_logs (Append-Only)       │
│ • long_term_memories             │
│ • conversation_logs              │
└──────────────────────────────────┘
```

---

## 2. Assignment 1 Capabilities

Apex Support AI fully implements and preserves all Assignment 1 specifications:

1. **LangGraph StateGraph Engine:**
   - Multi-node cyclic state machine: `intent_analyzer` ➔ `tool_executor` ➔ `rag_retriever` ➔ `memory_retriever` ➔ `context_selector` ➔ `llm_generator` ➔ `trace_logger`.
   - Autonomous routing: Direct Answer, Tool Invocation, RAG Retrieval, Composite Multi-Source, and Clarification.
2. **Four Core Functional Tools:**
   - `student_record_lookup`: Academic profile, department, and demographic records.
   - `fee_status_checker`: Real-time tuition fees, amount paid, balance, status, and deadlines.
   - `scholarship_status_checker`: Grant applications, award sums, and compliance criteria.
   - `create_support_ticket`: Ticket ticketing engine generating IDs (`TICK-YYYY-XXXX`).
3. **Grounded FAISS RAG Pipeline:**
   - Vector indexing over a 2-page synthetic Student Policy Handbook PDF using `sentence-transformers/all-MiniLM-L6-v2`.
   - Displays document title, chunk IDs, page numbers, and similarity distances in real time.
4. **Long-Term Memory with Privacy Filter:**
   - Persists non-sensitive profile attributes (preferred name, degree major, career aspirations) across sessions.
   - Strictly filters sensitive credentials (passwords, OTPs, PINs, card numbers) with logged audit events.
5. **Real-Time Observability & Telemetry:**
   - Real-time step status display during agent thinking.
   - Interactive monitoring dashboard showing actual latency (ms), input/output token usage, tool invocation breakdown, and benchmark accuracy.

---

## 3. Assignment 2 Security & Production Features

Assignment 2 hardens the system with enterprise security, role-based governance, and immutable audit trails:

### Priority 1 — Authentication (PBKDF2-HMAC-SHA256)
- **Password Security:** Hashes passwords using `hashlib.pbkdf2_hmac("sha256", password, salt, 100_000)` with a unique 16-byte random hex salt. Stored as `pbkdf2_sha256$100000$<salt>$<hash>`. Plain SHA-256 alone is strictly forbidden.
- **Three Institutional Roles:**
  - `STUDENT`: Enrolled student persona restricted to their own academic records.
  - `SUPPORT_STAFF`: Help desk staff with elevated cross-student view and approval review rights.
  - `ADMINISTRATOR`: Academic Dean with full administrative, review, and audit privileges.
- **Session Identity Resolution:** The agent **never** resolves identity from chat prompt text. The verified caller identity is resolved strictly from the authenticated session context (`caller_user`).

### Priority 2 — Authorization & Default-Deny Data Isolation
- **Owner-Based Isolation:** Students can only access their own fee records, scholarships, support tickets, and long-term memories.
- **Cross-Student Denial:** If student `STU1001` asks for the records of `STU1002`, access is blocked at the backend/tool level with an `Access Denied` status and an immutable `DENY` audit event.
- **Elevated Clearance:** Support Staff and Administrators possess authorized permissions to inspect any student's record for support assistance.

### Priority 3 — Approval Workflow for Sensitive Mutations (Course Change)
- **Pending Review State:** When a student requests a course/programme change (via Tool 5: `request_course_change`), the request enters `PENDING` status. The student's academic record is **not** modified prematurely.
- **Human-in-the-Loop Governance:** Only authorized reviewers (`SUPPORT_STAFF` or `ADMINISTRATOR`) can approve or reject pending requests.
- **Rejected Non-Execution:** If rejected, the request is marked `REJECTED` and the student record is never altered.
- **Exactly-Once Execution Guard:** If approved, the student record is updated to the new programme, and subsequent approval attempts on the finalized request are strictly refused (`ValueError`).

### Priority 4 — Append-Only Institutional Audit Trail
- **Immutable Table:** Stored in SQLite `audit_logs` table (`event_id`, `timestamp`, `actor_username`, `actor_role`, `action`, `target_resource`, `decision`, `reason`, `details`, `ip_address`).
- **Automatic Secret Redaction:** Regex-based credential sanitization masks OTPs (`[REDACTED_OTP]`), passwords (`[REDACTED_PASSWORD]`), and API keys before insertion.
- **Tamper Resistance:** No API or student role allows editing or deleting audit rows.

### Priority 5 — Streamlit UI Additions
- **`🔐 Login / Profile`:** Interactive login form with PBKDF2 password verification, active profile card, role badge, session security indicators, and 1-click persona switcher.
- **`⚖️ Approval Center`:** Review console displaying pending course-change requests, student reasons, and "Approve" / "Reject" controls with reviewer notes.
- **`🛡️ Audit Logs`:** Searchable audit trail table with decision filters (`ALLOW`, `DENY`, `PENDING`), role filters, and full event inspection.

---

## 4. Synthetic Demo Credentials

The database is pre-seeded with synthetic credentials hashed using PBKDF2-HMAC-SHA256 (100,000 iterations):

| Username | Password | Full Name | Role | Linked ID | Permissions |
|---|---|---|---|---|---|
| `stu1001` | `Student#1001!` | Rahul Sharma | `STUDENT` | `STU1001` | Own records only |
| `stu1002` | `Student#1002!` | Priya Patel | `STUDENT` | `STU1002` | Own records only |
| `stu1003` | `Student#1003!` | Amit Kumar | `STUDENT` | `STU1003` | Own records only |
| `stu1004` | `Student#1004!` | Sneha Reddy | `STUDENT` | `STU1004` | Own records only |
| `stu1005` | `Student#1005!` | Vikram Singh | `STUDENT` | `STU1005` | Own records only |
| `support1` | `Staff#2026!` | Anita Roy | `SUPPORT_STAFF` | None | Elevated cross-student lookup, Review approvals |
| `admin1` | `Admin#2026!` | Dr. K. Mehta (Dean) | `ADMINISTRATOR` | None | Full clearance, Review approvals, Audit admin |

---

## 5. Automated Test Suite Verification (39/39 Passed)

All 39 automated tests pass with 100% success rate:

```powershell
pytest tests/ -v
```

### Assignment 1 Test Coverage (26 Tests):
- `tests/test_tools.py` (7 tests): Valid/invalid student lookup, fee records, scholarships, ticket creation, and validation guards.
- `tests/test_rag.py` (5 tests): PDF parsing, text chunking, FAISS index similarity, policy search, and out-of-handbook detection.
- `tests/test_memory.py` (5 tests): Attribute extraction, persistent SQLite storage across sessions, deduplication, and sensitive OTP rejection.
- `tests/test_orchestrator.py` (9 tests): LangGraph direct math, fee tool, scholarship tool, RAG payment failure, out-of-handbook, support ticket, multi-session memory, OTP rejection, and trace persistence.

### Assignment 2 Test Coverage (13 Tests):
- `test_password_hashing_pbkdf2`: Validates PBKDF2-HMAC-SHA256 with 100k iterations and salt (plain SHA-256 alone rejected).
- `test_authentication_service`: Validates credential verification, wrong-password rejection, and role resolution.
- `test_authorization_own_record_access`: Validates student access to own fee, scholarship, and profile.
- `test_authorization_cross_student_access_denied`: Strictly blocks student STU1001 from querying STU1002 data.
- `test_staff_and_admin_cross_student_access`: Validates elevated access for Support Staff and Dean Administrator.
- `test_course_change_request_pending_state`: Validates that course-change requests enter `PENDING` and do not alter the database prematurely.
- `test_course_change_rejection_does_not_execute`: Validates that rejected requests transition to `REJECTED` and leave the student record unchanged.
- `test_course_change_approval_executes_exactly_once`: Validates approved mutation and duplicate execution blocking.
- `test_student_cannot_approve_request`: Validates that unauthorized students cannot approve requests (`PermissionError`).
- `test_sensitive_credential_masking`: Validates that passwords, OTPs, and API keys are redacted before audit recording.
- `test_audit_trail_logging_and_query`: Validates immutable audit event recording and query retrieval.
- `test_agent_e2e_own_fee_with_authenticated_session`: End-to-end agent query answering own fee with session context.
- `test_agent_e2e_cross_student_access_denial`: End-to-end agent blocking cross-student fee inquiry with `Access Denied`.

---

## 6. Project Directory Structure

```
Agentic_AI/
├── agent/                         # LangGraph Orchestration Engine
│   ├── __init__.py
│   ├── nodes.py                   # Intent analyzer, tool executor, RAG, memory, LLM nodes
│   ├── orchestrator.py            # StateGraph builder and run_agent entrypoint
│   └── state.py                   # TypedDict AgentState schema with caller_user
├── approvals/                     # Assignment 2 Approval Workflow
│   ├── __init__.py
│   └── approval_manager.py        # Course change requests, review decisions, exactly-once guard
├── app/                           # Streamlit Enterprise Frontend
│   ├── components/
│   │   ├── custom_styles.py       # Enterprise dark theme CSS tokens
│   │   └── sidebar.py             # Persistent navigation and active profile switcher
│   ├── views/
│   │   ├── chat_view.py           # Multi-tool agent concierge with live status
│   │   ├── monitoring_view.py     # Latency, token, and tool telemetry charts
│   │   ├── memory_view.py         # Long-term memory manager and privacy audit
│   │   ├── knowledge_view.py      # FAISS handbook document inspector
│   │   ├── login_view.py          # PBKDF2 authentication and profile switcher
│   │   ├── approval_view.py       # Institutional Approval Center (Reviewer console)
│   │   └── audit_view.py          # Append-only institutional audit trail
│   └── main.py                    # Streamlit application routing
├── config/
│   ├── __init__.py
│   └── settings.py                # Environment configurations and paths
├── database/
│   ├── __init__.py
│   ├── db.py                      # SQLAlchemy engine and sessionmaker
│   ├── models.py                  # Student, FeeRecord, Scholarship, Ticket, UserCredential, ApprovalRequest, AuditLog
│   └── seed.py                    # Database initialization and PBKDF2 credential seeding
├── evaluation/
│   ├── __init__.py
│   ├── benchmark_data.py          # 9 official Assignment 1 benchmark scenarios
│   └── evaluator.py               # Automated evaluation runner with CSV export
├── memory/
│   ├── __init__.py
│   ├── memory_extractor.py        # Privacy filter and attribute extraction
│   └── memory_manager.py          # SQLite long_term_memories persistence
├── rag/
│   ├── __init__.py
│   ├── handbook_generator.py      # Synthetic 2-page Student Handbook PDF
│   └── retriever.py               # FAISS vector store and similarity retrieval
├── security/                      # Assignment 2 Security Layer
│   ├── __init__.py
│   ├── authn.py                   # PBKDF2 password hashing and user authentication
│   ├── authz.py                   # Default-deny authorization and owner isolation
│   └── audit.py                   # Append-only audit logger and secret masking
├── tests/                         # Pytest Automated Test Suite
│   ├── test_assignment2.py        # 13 Assignment 2 security tests
│   ├── test_memory.py             # 5 Memory and privacy tests
│   ├── test_orchestrator.py       # 9 Orchestration scenario tests
│   ├── test_rag.py                # 5 FAISS and chunking tests
│   └── test_tools.py              # 7 Database tool tests
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git ignore rules (no keys, databases, or caches)
├── requirements.txt               # Locked dependencies
└── README.md                      # Comprehensive system documentation
```

---

## 7. Setup & Execution Guide

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12 installed.
- Git installed.

### 2. Environment Setup
```powershell
# Clone the repository
git clone https://github.com/rawalhim72-ops/Agentic_AI.git
cd Agentic_AI

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. API Key Configuration
Create a `.env` file in the root directory (or use `.env.example` as a template):
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
```
*(Note: If no API key is provided, the agent automatically runs in grounded deterministic fallback mode, using local tools and RAG without failing.)*

### 4. Database Seeding & FAISS Indexing
```powershell
python database/seed.py
python rag/handbook_generator.py
```

### 5. Running the Application
Launch the Streamlit enterprise dashboard:
```powershell
streamlit run app/main.py
```
Open your browser at `http://localhost:8501`.

---

## 8. Exact Verification Commands

### Run Full Test Suite (Assignments 1 & 2):
```powershell
pytest tests/ -v
```
*Expected Result: `39 passed in ~35s`*

### Run Assignment 2 Security Tests Only:
```powershell
pytest tests/test_assignment2.py -v
```
*Expected Result: `13 passed in ~3s`*

### Run Assignment 1 Evaluation Benchmark:
```powershell
python evaluation/evaluator.py
```
*Expected Result: `Benchmark Accuracy: 100.0% (9/9 Scenarios Passed)`*

---

## 9. Git Push Instructions

Ensure the repository is clean with no secrets or private caches committed:

```powershell
# 1. Verify git status
git status

# 2. Stage all project code and tests
git add .

# 3. Commit changes
git commit -m "Complete Assignment 2: Authentication, Authorization, Approval Workflow, and Audit Trail"

# 4. Link remote and push to main
git remote add origin https://github.com/rawalhim72-ops/Agentic_AI.git
git branch -M main
git push -u origin main
```

---

*Apex Support AI — Developed for Agentic AI Engineering (Assignments 1 & 2).*
