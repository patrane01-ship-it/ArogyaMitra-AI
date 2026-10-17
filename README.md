# ArogyaMitra AI — Personal Health Intelligence Platform

ArogyaMitra AI is an agentic, privacy-first personal health intelligence platform designed for India, compliant with the Digital Personal Data Protection (DPDP) Act, 2023 and DPDP Rules, 2025.

---

## 🏗️ Architecture & Stack

- **Backend**: Python 3.11+ / FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2
- **Database & Cache**: PostgreSQL (with JSONB), Redis
- **Intelligence**: LangGraph multi-agent orchestration, Groq LLM inference, ChromaDB vector store, Scikit-learn
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide icons
- **Data Security**: Envelope encryption (AES-256-GCM with master KEK wrapping), append-only consent ledgers, role-based caregiver access control.

---

## ⚙️ Prerequisites & Setup

### 1. Environment Requirements
- Python 3.11 or newer
- Node.js 18+ and npm
- PostgreSQL 15+
- Redis 7+
- Tesseract OCR (with eng + hin language packs)

### 2. Configuration
Copy the sample environment file and populate values:
```bash
cp .env.example .env
```
Ensure required secrets are set (`SECRET_KEY`, `ENCRYPTION_KEY`, `GROQ_API_KEY`, `DATABASE_URL`, `REDIS_URL`).

### 3. Backend Setup
Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Database Migrations
Run Alembic migrations to update the database to the latest revision (Phase 4):
```bash
alembic upgrade head
```

---

## 🚀 Running the Services

### Start API Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation (when `DEBUG=True`): `http://localhost:8000/docs`

### Start Frontend Dev Server
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing & CI

### Run Test Suite
```bash
pytest backend/tests -v
```

### Run Static Analysis & Security Audits
```bash
# Code Quality Linter
ruff check backend/

# Security Vulnerability Scan
bandit -r backend/ -ll -ii

# Python Dependencies Audit
pip-audit

# Frontend Security Audit & Build
cd frontend
npm audit
npm run build
```
The automated GitHub Actions workflow (`.github/workflows/ci.yml`) runs all lints, security audits, and builds on push and pull requests.
