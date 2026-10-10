# ArogyaMitra AI — Tech Stack, Architecture & Prototype 1 Build Plan
> Version: Phase 1 (Prototype)
> Target: AI IDE Code Generation Ready
> Author: ArogyaMitra Dev

---

## 1. Full Tech Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Primary LLM** | Groq `llama-3.3-70b-versatile` | Free tier, fast inference, handles long medical text well |
| **Secondary LLM** | Groq `llama-3.1-8b-instant` | Lightweight tasks (reminder extraction, short summaries) |
| **OCR — PDFs** | `Tesseract` (via pytesseract) | Free, handles printed text in lab reports |
| **OCR — Images** | `EasyOCR` | Handles handwritten prescriptions, better on image noise |
| **Agent Framework** | `LangGraph` | Multi-agent orchestration, state machine control |
| **Vector Store** | `ChromaDB` (local persistent) | Free, local, stores health record embeddings for RAG |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Free, lightweight, works offline |
| **Relational Store** | `SQLite` (via SQLAlchemy ORM) | Structured CRUD for records, params, reminders, reports |
| **Backend API** | `FastAPI` | Async, auto-docs, fits LangGraph integration |
| **PDF Export** | `ReportLab` | Doctor-Prep report → downloadable PDF |
| **Encryption** | `cryptography` lib (AES-256-GCM) | Encrypt uploaded health files at rest |
| **Auth (Phase 1)** | None — single local user (`local_user`) | Phase 1 scope — multi-user auth is Phase 2 |
| **Frontend** | `React + Vite + Tailwind CSS` | Your established stack |
| **Charts** | `Recharts` | Line charts for health timeline |
| **Risk Gauge** | Custom SVG component or `react-circular-progressbar` | Overall risk score display |
| **HTTP Client** | `Axios` | Frontend → FastAPI calls |
| **Token (Share Links)** | `PyJWT` | Signed expiring share tokens |
| **Time-Series (Phase 1)** | Rule-based scoring engine (custom Python) | Phase 1 — no trained model yet, threshold logic |
| **Time-Series (Phase 2)** | `Prophet` or `sklearn` `IsolationForest` | Plug in once sufficient data schema is established |
| **Environment** | `python-dotenv` | API key management |

---

## 2. Project Folder Structure

```
arogya-mitra-ai/
│
├── backend/
│   ├── main.py                         # FastAPI app entry point
│   ├── config.py                       # Environment variables, constants, SUPPORTED_PARAMETERS
│   ├── database.py                     # SQLAlchemy setup, SQLite connection
│   │
│   ├── models/                         # OOP Entity Classes (SQLAlchemy ORM models)
│   │   ├── __init__.py
│   │   ├── health_record.py            # HealthRecord class
│   │   ├── clinical_parameter.py       # ClinicalParameter class
│   │   ├── risk_score.py               # RiskScore class
│   │   ├── reminder.py                 # Reminder class
│   │   └── doctor_report.py            # DoctorReport class
│   │
│   ├── schemas/                        # Pydantic schemas for request/response validation
│   │   ├── health_record_schema.py
│   │   ├── clinical_parameter_schema.py
│   │   ├── risk_score_schema.py
│   │   ├── reminder_schema.py
│   │   └── doctor_report_schema.py
│   │
│   ├── routers/                        # FastAPI route handlers
│   │   ├── records_router.py           # /api/records CRUD
│   │   ├── params_router.py            # /api/params
│   │   ├── reminders_router.py         # /api/reminders CRUD
│   │   ├── reports_router.py           # /api/report generate + download
│   │   └── share_router.py             # /share/{token} public endpoint
│   │
│   ├── agents/                         # LangGraph Agent Definitions
│   │   ├── __init__.py
│   │   ├── graph.py                    # LangGraph StateGraph definition (master graph)
│   │   ├── ingestion_agent.py          # Node: OCR + entity extraction
│   │   ├── trend_agent.py              # Node: risk scoring + anomaly flagging
│   │   ├── reminder_agent.py           # Node: auto-reminder creation from prescriptions
│   │   └── doctor_prep_agent.py        # Node: pre-visit summary generation
│   │
│   ├── services/                       # Business logic layer
│   │   ├── ocr_service.py              # Tesseract + EasyOCR wrapper
│   │   ├── entity_extractor.py         # Regex + Groq-powered clinical value extraction
│   │   ├── risk_engine.py              # Rule-based risk scoring logic
│   │   ├── encryption_service.py       # AES-256-GCM encrypt/decrypt file
│   │   ├── pdf_export_service.py       # ReportLab PDF generation
│   │   ├── share_service.py            # JWT token generation + validation
│   │   └── chroma_service.py           # ChromaDB store/retrieve/embed operations
│   │
│   ├── exceptions/                     # Custom exception classes
│   │   └── arogya_errors.py            # All ArogyaError subclasses
│   │
│   └── data/
│       ├── records/encrypted/          # AES-encrypted uploaded files
│       ├── chroma_db/                  # ChromaDB persistent storage
│       └── arogya_mitra.db             # SQLite database file
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── UploadPage.jsx
│   │   │   ├── TimelinePage.jsx
│   │   │   ├── RemindersPage.jsx
│   │   │   ├── DoctorReportPage.jsx
│   │   │   ├── RecordDetailPage.jsx
│   │   │   └── SharePage.jsx
│   │   ├── components/
│   │   │   ├── RiskGauge.jsx
│   │   │   ├── HealthTimeline.jsx
│   │   │   ├── RecordCard.jsx
│   │   │   ├── ReminderCard.jsx
│   │   │   ├── FileUploader.jsx
│   │   │   ├── ManualEntryForm.jsx
│   │   │   └── Navbar.jsx
│   │   ├── services/
│   │   │   └── api.js                  # Axios instance + all API call functions
│   │   └── utils/
│   │       ├── formatDate.js
│   │       ├── riskColors.js           # Map risk level → Tailwind color classes
│   │       └── parameterConfig.js      # SUPPORTED_PARAMETERS list for frontend
│   ├── index.html
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── .env                                # GROQ_API_KEY, SECRET_KEY, etc.
├── requirements.txt
├── package.json
└── README.md
```

---

## 3. LangGraph Agent Architecture

```
User uploads record
        │
        ▼
┌──────────────────┐
│  Ingestion Agent │ ← OCR (Tesseract/EasyOCR) + Entity Extractor
│  (LangGraph Node)│   Creates HealthRecord + ClinicalParameter objects
└────────┬─────────┘
         │ on_success
         ▼
┌──────────────────┐
│   Trend Agent    │ ← Reads all ClinicalParameters for user
│  (LangGraph Node)│   Runs risk_engine.py, updates RiskScore
└────────┬─────────┘
         │ in_parallel
         ▼
┌──────────────────┐
│  Reminder Agent  │ ← If record_type == PRESCRIPTION
│  (LangGraph Node)│   Extracts medicines, creates Reminder objects
└────────┬─────────┘
         │ on_user_request
         ▼
┌───────────────────────┐
│  Doctor-Prep Agent    │ ← Groq llama-3.3-70b
│  (LangGraph Node)     │   Generates DoctorReport from all data
└───────────────────────┘
```

### LangGraph State Schema:

```python
class ArogyaState(TypedDict):
    record_id: str
    user_id: str
    raw_text: str
    extracted_entities: dict
    clinical_params: list
    risk_score: float
    risk_level: str
    reminders_created: list
    doctor_report_content: str
    errors: list
    current_step: str
```

### Conditional Edges:
```
ingestion_agent → trend_agent (always)
trend_agent → reminder_agent (if record_type == PRESCRIPTION)
trend_agent → END (if not PRESCRIPTION)
reminder_agent → END
doctor_prep_agent → END (triggered separately on user request)
```

---

## 4. Database Schema (SQLite via SQLAlchemy)

### Table: `health_records`
```sql
CREATE TABLE health_records (
    record_id       TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL DEFAULT 'local_user',
    record_type     TEXT NOT NULL,
    upload_date     DATETIME NOT NULL,
    report_date     DATETIME NOT NULL,
    source_file_path TEXT,
    raw_text        TEXT,
    is_processed    BOOLEAN DEFAULT FALSE,
    is_deleted      BOOLEAN DEFAULT FALSE,
    encryption_hash TEXT,
    share_token     TEXT,
    share_expires_at DATETIME
);
```

### Table: `clinical_parameters`
```sql
CREATE TABLE clinical_parameters (
    param_id            TEXT PRIMARY KEY,
    record_id           TEXT NOT NULL,
    param_name          TEXT NOT NULL,
    value               REAL NOT NULL,
    unit                TEXT NOT NULL,
    reference_range_min REAL,
    reference_range_max REAL,
    report_date         DATETIME NOT NULL,
    status              TEXT NOT NULL,
    anomaly_score       REAL,
    FOREIGN KEY (record_id) REFERENCES health_records(record_id)
);
```

### Table: `risk_scores`
```sql
CREATE TABLE risk_scores (
    score_id            TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    computed_at         DATETIME NOT NULL,
    overall_risk        REAL NOT NULL,
    risk_level          TEXT NOT NULL,
    contributing_factors TEXT,   -- JSON serialized
    recommendations     TEXT,    -- JSON serialized list
    version             INTEGER DEFAULT 1
);
```

### Table: `reminders`
```sql
CREATE TABLE reminders (
    reminder_id             TEXT PRIMARY KEY,
    user_id                 TEXT NOT NULL,
    reminder_type           TEXT NOT NULL,
    title                   TEXT NOT NULL,
    due_date                DATETIME NOT NULL,
    recurrence              TEXT DEFAULT 'NONE',
    is_active               BOOLEAN DEFAULT TRUE,
    is_acknowledged         BOOLEAN DEFAULT FALSE,
    created_from_record_id  TEXT
);
```

### Table: `doctor_reports`
```sql
CREATE TABLE doctor_reports (
    report_id           TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    generated_at        DATETIME NOT NULL,
    report_content      TEXT NOT NULL,
    pdf_path            TEXT,
    records_included    TEXT,    -- JSON serialized list
    share_token         TEXT,
    share_expires_at    DATETIME
);
```

---

## 5. API Endpoints (FastAPI)

### Records
```
POST   /api/records/upload          Upload + trigger Ingestion Agent
GET    /api/records/                List all records
GET    /api/records/{id}            Get single record
PUT    /api/records/{id}            Update record metadata
DELETE /api/records/{id}            Soft delete
```

### Parameters
```
GET    /api/params/                         All parameters for user
GET    /api/params/{param_name}             History for one parameter (timeline data)
PUT    /api/params/{param_id}               Manual correction
```

### Risk
```
GET    /api/risk/current            Latest risk score
GET    /api/risk/history            All past risk scores
POST   /api/risk/recompute          Force recompute
```

### Reminders
```
POST   /api/reminders/              Create reminder
GET    /api/reminders/              List all active reminders
PUT    /api/reminders/{id}          Update reminder
DELETE /api/reminders/{id}          Delete reminder
PATCH  /api/reminders/{id}/ack      Acknowledge reminder
```

### Doctor Report
```
POST   /api/report/generate         Trigger Doctor-Prep Agent
GET    /api/report/latest           Get latest generated report
GET    /api/report/{id}/pdf         Download report as PDF
POST   /api/report/{id}/share       Generate share link
```

### Share (Public)
```
GET    /share/{token}               Public read-only view (validate token first)
```

---

## 6. Encryption Implementation

```python
# services/encryption_service.py

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, base64

class EncryptionService:
    def __init__(self, key: bytes):
        # key must be 32 bytes (AES-256)
        self.aesgcm = AESGCM(key)

    def encrypt_file(self, file_bytes: bytes) -> tuple[bytes, bytes]:
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = self.aesgcm.encrypt(nonce, file_bytes, None)
        return nonce, ciphertext

    def decrypt_file(self, nonce: bytes, ciphertext: bytes) -> bytes:
        return self.aesgcm.decrypt(nonce, ciphertext, None)
```

Key stored in `.env` as `ENCRYPTION_KEY` (base64-encoded 32 bytes).

---

## 7. Environment Variables (`.env`)

```env
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_jwt_secret_key_here
ENCRYPTION_KEY=your_base64_32byte_aes_key_here
CHROMA_DB_PATH=./backend/data/chroma_db
SQLITE_DB_PATH=./backend/data/arogya_mitra.db
UPLOAD_DIR=./backend/data/records/encrypted
VITE_API_BASE_URL=http://localhost:8000
```

---

## 8. Prototype 1 — Build Order (Recommended for AI IDE)

Follow this order strictly — each step has testable output before moving to next:

```
Step 1: Setup
  - Initialize FastAPI app (main.py)
  - Setup SQLite with SQLAlchemy (database.py)
  - Create all 5 ORM models (models/)
  - Run Alembic migrations (or SQLAlchemy create_all)
  - Test: DB tables created, no errors

Step 2: Core Services
  - ocr_service.py (Tesseract + EasyOCR)
  - entity_extractor.py (regex patterns for 15 supported parameters)
  - encryption_service.py (AES-256-GCM)
  - Test: Upload a sample PDF, OCR extracts text, entities extracted, file encrypted

Step 3: Agent Pipeline
  - ingestion_agent.py (calls ocr_service + entity_extractor)
  - trend_agent.py (calls risk_engine)
  - reminder_agent.py (creates Reminder objects from prescriptions)
  - graph.py (wire all nodes into LangGraph StateGraph)
  - Test: Full pipeline runs on a sample record, RiskScore saved to DB

Step 4: FastAPI Routers
  - records_router.py (CRUD + upload trigger)
  - params_router.py (READ + manual correction)
  - reminders_router.py (full CRUD + ack)
  - risk endpoint
  - Test: All endpoints return correct responses via FastAPI /docs

Step 5: Doctor-Prep Agent + PDF Export
  - doctor_prep_agent.py (Groq llama-3.3-70b generates structured report)
  - pdf_export_service.py (ReportLab renders to PDF)
  - reports_router.py
  - Test: POST /api/report/generate → returns structured report, PDF downloadable

Step 6: Share Links
  - share_service.py (PyJWT)
  - share_router.py
  - Test: Generate token, access /share/{token}, verify expiry returns 410

Step 7: Frontend
  - DashboardPage (risk gauge + recent records + reminders)
  - UploadPage (drag-drop + manual entry)
  - TimelinePage (parameter selector + Recharts chart)
  - RemindersPage (CRUD UI)
  - DoctorReportPage (generate + preview + download)
  - Test: Full user flow E2E — upload → dashboard updates → report generates

Step 8: Integration & Polish
  - Connect ChromaDB (chroma_service.py) for semantic search across records
  - Add loading states + error toasts on frontend
  - Final validation pass against PHASE1_CHECKLIST.md
```

---

## 9. Frontend Design Direction

**Color Palette:**
```
Primary:     #1A6B5A  (deep teal — health/trust)
Accent:      #4ECBA0  (mint green — positive indicators)
Warning:     #F5A623  (amber — moderate risk)
Critical:    #E53E3E  (red — critical risk)
Background:  #F7FAF9  (near-white with green tint)
Surface:     #FFFFFF
Text:        #1A202C  (near-black)
Muted:       #718096
```

**Typography:**
- Display: `Inter` (700 weight) — clean, medical-adjacent authority
- Body: `Inter` (400/500) — same family, consistent
- Data/labels: `JetBrains Mono` — monospace for parameter values (e.g. "HbA1c: 6.2%")

**Signature element:** The risk score gauge on the dashboard — a large circular dial, teal-to-red gradient fill, with the risk percentage in JetBrains Mono at center. This is the first thing the user sees and the most memorable visual element of the product.

---

*End of TECH_STACK.md — Phase 1*
