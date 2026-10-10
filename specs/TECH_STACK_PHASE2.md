# ArogyaMitra AI — Phase 2 Tech Stack & Architecture
> Version: Phase 2 (ML Upgrade)
> Builds on top of Phase 1 stack — do not replace Phase 1 components
> Target: AI IDE Code Generation Ready

---

## 1. Phase 2 Stack Additions

| Layer | Phase 1 | Phase 2 Addition | Why |
|-------|---------|-----------------|-----|
| **Auth** | None (local_user) | `bcrypt` + `PyJWT` (access + refresh tokens) | Multi-user isolation |
| **Risk Engine** | Rule-based thresholds | `scikit-learn` RandomForest / GradientBoosting | Trained prediction |
| **Anomaly Detection** | None | `scikit-learn` IsolationForest | Statistical anomaly scoring |
| **Model Serialization** | None | `joblib` | Save/load .pkl model files |
| **Drug DB** | None | `DrugBank open CSV` + ChromaDB collection | Interaction knowledge base |
| **Drug Interaction LLM** | Groq llama-3.3-70b (existing) | Same — adds structured JSON prompt | Fallback for unknown pairs |
| **Data Generation** | None | `numpy` + `pandas` | Synthetic training data |
| **Mobile Camera** | None | Browser `MediaDevices API` | Camera capture on mobile |
| **Rate Limiting** | None | `slowapi` (FastAPI rate limit middleware) | Protect auth endpoints |
| **Password Hashing** | None | `passlib[bcrypt]` | Secure credential storage |
| **Migrations** | SQLAlchemy create_all | `alembic` | Controlled schema migrations |

---

## 2. Updated Requirements

Add to `requirements.txt`:
```
# Phase 2 additions
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
slowapi==0.1.9
alembic==1.13.1
joblib==1.3.2
scikit-learn==1.4.2
numpy==1.26.4
pandas==2.2.2
itertools-more==0.4.0
```

---

## 3. Updated Database Schema

### New Table: `users`
```sql
CREATE TABLE users (
    user_id             TEXT PRIMARY KEY,
    email               TEXT UNIQUE NOT NULL,
    hashed_password     TEXT NOT NULL,
    full_name           TEXT NOT NULL,
    date_of_birth       DATE,
    gender              TEXT,
    created_at          DATETIME NOT NULL,
    is_active           BOOLEAN DEFAULT TRUE,
    last_login          DATETIME,
    refresh_token_hash  TEXT
);
CREATE INDEX idx_users_email ON users(email);
```

### New Table: `ml_risk_models`
```sql
CREATE TABLE ml_risk_models (
    model_id            TEXT PRIMARY KEY,
    model_version       TEXT NOT NULL,
    model_type          TEXT NOT NULL,
    trained_at          DATETIME NOT NULL,
    feature_names       TEXT NOT NULL,   -- JSON serialized list
    training_accuracy   REAL NOT NULL,
    model_path          TEXT NOT NULL,
    is_active           BOOLEAN DEFAULT FALSE,
    notes               TEXT
);
```

### New Table: `anomaly_results`
```sql
CREATE TABLE anomaly_results (
    anomaly_id              TEXT PRIMARY KEY,
    user_id                 TEXT NOT NULL,
    param_name              TEXT NOT NULL,
    computed_at             DATETIME NOT NULL,
    anomaly_score           REAL NOT NULL,
    is_anomaly              BOOLEAN NOT NULL,
    threshold               REAL DEFAULT -0.1,
    data_points_used        INTEGER NOT NULL,
    flagged_reading_date    DATETIME,
    flagged_value           REAL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### New Table: `drug_interactions`
```sql
CREATE TABLE drug_interactions (
    interaction_id      TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    drug_a              TEXT NOT NULL,
    drug_b              TEXT NOT NULL,
    severity            TEXT NOT NULL,
    interaction_description TEXT NOT NULL,
    recommendation      TEXT NOT NULL,
    source              TEXT NOT NULL,
    detected_at         DATETIME NOT NULL,
    from_record_ids     TEXT,           -- JSON serialized list
    is_dismissed        BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### Modified Tables (Alembic migrations):
```sql
-- Add to clinical_parameters
ALTER TABLE clinical_parameters ADD COLUMN isolation_forest_score REAL;
ALTER TABLE clinical_parameters ADD COLUMN is_anomaly BOOLEAN;
ALTER TABLE clinical_parameters ADD COLUMN ml_risk_contribution REAL;

-- Add to risk_scores
ALTER TABLE risk_scores ADD COLUMN model_id TEXT;
ALTER TABLE risk_scores ADD COLUMN model_version TEXT;
ALTER TABLE risk_scores ADD COLUMN ml_confidence REAL;
ALTER TABLE risk_scores ADD COLUMN scoring_method TEXT DEFAULT 'RULE_BASED';

-- Add user_id FK to all existing tables (migration required)
-- health_records, clinical_parameters, risk_scores, reminders, doctor_reports
-- Already have user_id TEXT — add FK constraint via new migration
```

---

## 4. Updated LangGraph Graph (Phase 2)

```
User uploads record
        │
        ▼
┌──────────────────┐
│  Ingestion Agent │ ← OCR + Entity Extractor (unchanged from Phase 1)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Trend Agent    │ ← UPGRADED:
│                  │   1. FeatureEngineer builds vector
│                  │   2. MLRiskEngine.predict() if active model
│                  │   3. Falls back to rule-based if no model
│                  │   4. AnomalyDetectionService runs on all params
│                  │   5. Saves RiskScore + AnomalyResults
└────────┬─────────┘
         │ if PRESCRIPTION
         ▼
┌────────────────────────┐
│  Reminder Agent        │ ← unchanged from Phase 1
└────────┬───────────────┘
         │ if PRESCRIPTION
         ▼
┌────────────────────────┐
│  Drug Interaction Agent│ ← NEW Phase 2
│                        │   1. Gets all active drugs for user
│                        │   2. Checks all pairs via ChromaDB + Groq fallback
│                        │   3. Saves DrugInteraction objects
└────────────────────────┘
         │
         ▼
      END

(Doctor-Prep Agent still triggered separately on user request — unchanged)
```

### Updated `ArogyaState` TypedDict:
```python
class ArogyaState(TypedDict):
    # Phase 1 fields (unchanged)
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
    # Phase 2 additions
    scoring_method: str               # "RULE_BASED" or "ML_MODEL"
    ml_confidence: Optional[float]
    anomaly_results: list             # list of AnomalyResult dicts
    active_drugs: list[str]           # extracted from prescription
    drug_interactions: list           # list of DrugInteraction dicts
    feature_vector: Optional[list[float]]
```

---

## 5. JWT Token Architecture

```
Tokens stored:
  - access_token: in-memory only (React state / AuthContext) — NEVER localStorage
  - refresh_token: httpOnly cookie (set by backend) — JS cannot access

Access token payload:
  {
    "sub": "user_id_uuid",
    "email": "user@example.com",
    "exp": <unix timestamp 15min from now>,
    "type": "access"
  }

Refresh token payload:
  {
    "sub": "user_id_uuid",
    "exp": <unix timestamp 7 days from now>,
    "type": "refresh"
  }

Refresh flow in React (AuthContext.jsx):
  - On app load: try POST /api/auth/refresh (httpOnly cookie sent automatically)
  - If success: set access_token in state → user is logged in
  - If 401: redirect to /login
  - Set up axios interceptor: on 401 → try refresh → retry original request
  - If refresh fails: clear auth state → redirect to /login
```

**Security notes:**
- Never store access_token in localStorage or sessionStorage — XSS risk
- refresh_token in httpOnly cookie — not accessible by JavaScript — CSRF protected via SameSite=Strict
- Backend must set cookie: `Set-Cookie: refresh_token=...; HttpOnly; SameSite=Strict; Path=/api/auth/refresh`

---

## 6. ML Training Pipeline Architecture

```
backend/ml/
├── synthetic_data_generator.py
│   - generate_dataset(n_samples=2000) -> pd.DataFrame
│   - Uses REFERENCE_RANGES from config.py
│   - Outputs: CSV with 15 feature columns + "risk_level" label
│
├── feature_engineer.py
│   - FeatureEngineer class
│   - build_feature_vector(user_id, db) -> list[float]  ← for inference
│   - build_from_dict(param_dict) -> list[float]         ← for training
│   - normalize(value, min, max) -> float
│
├── train_risk_model.py  ← RUN THIS ONCE to generate the .pkl
│   - load_dataset()
│   - feature_engineering()
│   - train_test_split(stratify=True)
│   - GridSearchCV(RandomForestClassifier, param_grid)
│   - evaluate(model, X_test, y_test) → print classification_report
│   - joblib.dump(best_model, "models/risk_model_v2.pkl")
│   - Save MLRiskModel record to DB
│
├── ml_risk_engine.py
│   - MLRiskEngine class
│   - predict(feature_vector) -> dict
│   - get_feature_importance() -> dict (for explainability)
│
└── anomaly_detection_service.py
    - AnomalyDetectionService class
    - detect_anomalies(param_name, values) -> list[AnomalyResult]
    - validate_inputs(values) -> None
```

---

## 7. Drug Interaction Knowledge Base Ingestion

One-time ingestion script: `backend/services/drug_db_service.py`

```python
class DrugDBService:
    COLLECTION_NAME = "drug_interactions"

    def ingest_from_csv(self, csv_path: str) -> int:
        """
        Reads DrugBank open CSV.
        Expected columns: drug_a, drug_b, severity, description
        Creates ChromaDB documents: "drug_a + drug_b: severity — description"
        Returns count of ingested interactions.
        """
        df = pd.read_csv(csv_path)
        documents = []
        metadatas = []
        ids = []
        for _, row in df.iterrows():
            doc = f"{row['drug_a']} interaction with {row['drug_b']}: {row['severity']} — {row['description']}"
            documents.append(doc)
            metadatas.append({
                "drug_a": row['drug_a'],
                "drug_b": row['drug_b'],
                "severity": row['severity'],
                "description": row['description']
            })
            ids.append(f"interaction_{uuid4()}")
        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return len(documents)

    def query_interaction(self, drug_a: str, drug_b: str, n_results=3) -> list[dict]:
        """
        Queries ChromaDB for interaction between drug_a and drug_b.
        Returns list of {document, metadata, distance}
        """
        query = f"{drug_a} interaction with {drug_b}"
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return self.parse_results(results)

    def is_ingested(self) -> bool:
        """Check if ingested_flag.txt exists — skip re-ingestion on startup."""
        return os.path.exists("./data/drug_db/ingested_flag.txt")

    def mark_ingested(self):
        with open("./data/drug_db/ingested_flag.txt", "w") as f:
            f.write(datetime.now().isoformat())
```

---

## 8. Mobile UI Architecture

```
Breakpoint strategy:
  Base (default) = mobile (< 640px)
  sm: 640px
  md: 768px  
  lg: 1024px

Navigation:
  Mobile (< md):  BottomNav (fixed, 4 icons)
  Desktop (>= md): Navbar (top, horizontal)

Layout grids:
  Cards:      grid-cols-1 sm:grid-cols-2 lg:grid-cols-3
  Dashboard:  flex-col md:flex-row
  Forms:      w-full md:w-[480px] mx-auto

Touch interactions:
  - Swipeable cards: custom touch event handlers
  - Pull-to-refresh: touchstart/touchmove/touchend on dashboard container
  - Camera modal: full-screen on mobile, centered modal on desktop

Camera implementation:
  navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
  → stream to <video> element
  → on capture: canvas.drawImage(video) → canvas.toBlob() → File object
  → File sent via FormData to POST /api/records/upload (same endpoint as file picker)
```

---

## 9. Rate Limiting Configuration (slowapi)

```python
# main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# auth_router.py
@router.post("/login")
@limiter.limit("5/15minutes")  # Max 5 login attempts per IP per 15 min
async def login(...): ...

@router.post("/register")
@limiter.limit("3/hour")  # Max 3 registrations per IP per hour
async def register(...): ...
```

---

## 10. Phase 2 Environment Variables (additions to .env)

```env
# Phase 2 additions
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12
DRUG_DB_CSV_PATH=./backend/data/drug_db/drugbank_open.csv
ML_MODELS_DIR=./backend/ml/models
ACTIVE_MODEL_PATH=./backend/ml/models/risk_model_v2.pkl
ANOMALY_THRESHOLD=-0.1
ANOMALY_CONTAMINATION=0.1
DRUG_INTERACTION_DISTANCE_THRESHOLD=0.35
```

---

*End of TECH_STACK_PHASE2.md*
