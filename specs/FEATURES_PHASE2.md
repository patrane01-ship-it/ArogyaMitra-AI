# ArogyaMitra AI — Phase 2 Features & Implementation Specification
> Version: Phase 2 (ML Upgrade)
> Prerequisite: Phase 1 complete and all 156 checklist items passing
> Target: AI IDE Code Generation Ready
> Author: ArogyaMitra Dev

---

## 1. Phase 2 Overview

Phase 2 upgrades ArogyaMitra from a rule-based prototype into a genuinely predictive ML platform. The 5 major upgrades are:

| Upgrade | What changes from Phase 1 |
|---------|--------------------------|
| **Trained Risk Prediction Model** | Replaces rule-based threshold scoring with a trained sklearn classifier |
| **Isolation Forest Anomaly Detection** | Replaces simple HIGH/CRITICAL flag with statistical anomaly scoring per parameter time-series |
| **Multi-User Auth (JWT)** | Replaces single `local_user` with full registration, login, and per-user data isolation |
| **Mobile-Optimized UI** | Rebuilds frontend with mobile-first Tailwind breakpoints, camera-upload for prescriptions |
| **Drug Interaction Checker** | New agent + embedding-based lookup against a structured drug database |

---

## 2. New & Upgraded OOP Entities

All Phase 1 entities remain. Phase 2 adds or extends the following:

---

### 2.1 `User` Class (NEW)

```
Class: User
Responsibility: Represents a registered user — replaces hardcoded 'local_user'

Attributes:
  - user_id: str (UUID4, auto-generated)
  - email: str (unique, validated)
  - hashed_password: str (bcrypt hash — NEVER store plain text)
  - full_name: str
  - date_of_birth: Optional[date]
  - gender: Optional[Enum["MALE", "FEMALE", "OTHER", "PREFER_NOT_TO_SAY"]]
  - created_at: datetime
  - is_active: bool (default True)
  - last_login: Optional[datetime]
  - refresh_token_hash: Optional[str] (for JWT refresh flow)

Methods:
  - validate(): email must be valid format, full_name min 2 chars, date_of_birth must be in past
  - set_password(plain_password: str): hashes with bcrypt, sets hashed_password
  - verify_password(plain_password: str) -> bool: bcrypt comparison
  - to_dict(): excludes hashed_password and refresh_token_hash
  - from_dict(): class method
  - compute_age() -> Optional[int]: returns age in years from date_of_birth
```

**CRUD Operations for User:**
| Operation | Endpoint | Description |
|-----------|----------|-------------|
| CREATE | `POST /api/auth/register` | New user registration |
| READ | `GET /api/auth/me` | Get current authenticated user profile |
| UPDATE | `PUT /api/auth/me` | Update full_name, date_of_birth, gender |
| DELETE | `DELETE /api/auth/me` | Soft deactivate (`is_active=False`) |
| LOGIN | `POST /api/auth/login` | Returns access_token + refresh_token |
| REFRESH | `POST /api/auth/refresh` | Returns new access_token using refresh_token |
| LOGOUT | `POST /api/auth/logout` | Invalidates refresh_token_hash |

**Validation Rules:**
- `email` must match regex `^[\w\.-]+@[\w\.-]+\.\w{2,}$` — raise `InvalidEmailError`
- `password` (at registration) min 8 chars, at least 1 number, 1 uppercase — raise `WeakPasswordError`
- `full_name` min 2 characters — raise `InvalidNameError`
- `date_of_birth` must be in the past — raise `FutureDateOfBirthError`
- Duplicate email on register — raise `EmailAlreadyExistsError`
- Login with wrong password — raise `InvalidCredentialsError` (never specify which field is wrong)

---

### 2.2 `MLRiskModel` Class (NEW)

```
Class: MLRiskModel
Responsibility: Wraps the trained sklearn risk prediction model with metadata

Attributes:
  - model_id: str (UUID4)
  - model_version: str (e.g. "2.0.0")
  - model_type: str (e.g. "RandomForestClassifier")
  - trained_at: datetime
  - feature_names: list[str] (ordered list of input features the model expects)
  - training_accuracy: float
  - model_path: str (path to serialized .pkl file)
  - is_active: bool (only one model is active at a time)
  - notes: str (e.g. "trained on synthetic dataset v1 — 2000 samples")

Methods:
  - validate(): training_accuracy must be between 0.0 and 1.0, feature_names must not be empty
  - load() -> sklearn model object: loads and returns the model from model_path
  - predict(feature_vector: list[float]) -> dict: returns {risk_score, risk_level, confidence}
  - to_dict() / from_dict()
```

**CRUD Operations for MLRiskModel:**
| Operation | Endpoint | Description |
|-----------|----------|-------------|
| CREATE | `POST /api/admin/models/upload` | Upload new trained model (.pkl + metadata) |
| READ | `GET /api/admin/models/active` | Get currently active model |
| READ ALL | `GET /api/admin/models/` | List all model versions |
| ACTIVATE | `PATCH /api/admin/models/{id}/activate` | Set a model as active (deactivates previous) |
| DELETE | `DELETE /api/admin/models/{id}` | Soft delete (cannot delete active model) |

---

### 2.3 `AnomalyResult` Class (NEW)

```
Class: AnomalyResult
Responsibility: Stores the Isolation Forest anomaly detection result for a ClinicalParameter time-series

Attributes:
  - anomaly_id: str (UUID4)
  - user_id: str
  - param_name: str
  - computed_at: datetime
  - anomaly_score: float (-1.0 to 0.0 — more negative = more anomalous in sklearn IF)
  - is_anomaly: bool (True if anomaly_score < threshold)
  - threshold: float (default -0.1, configurable)
  - data_points_used: int (number of readings the model was trained/scored on)
  - flagged_reading_date: Optional[datetime] (the specific reading that triggered the flag)
  - flagged_value: Optional[float]

Methods:
  - validate(): anomaly_score must be between -1.0 and 0.0
  - to_dict() / from_dict()
```

---

### 2.4 `DrugInteraction` Class (NEW)

```
Class: DrugInteraction
Responsibility: Stores a detected potential interaction between two or more drugs

Attributes:
  - interaction_id: str (UUID4)
  - user_id: str
  - drug_a: str (normalized drug name)
  - drug_b: str
  - severity: Enum["MINOR", "MODERATE", "MAJOR", "CONTRAINDICATED"]
  - interaction_description: str (plain-English explanation)
  - recommendation: str (what to do — e.g. "Consult your doctor before combining")
  - source: str (e.g. "DrugBank embeddings" or "Groq-generated")
  - detected_at: datetime
  - from_record_ids: list[str] (records where these drugs were found)

Methods:
  - validate(): drug_a and drug_b must not be same string, severity must be valid Enum
  - to_dict() / from_dict()
```

**CRUD Operations for DrugInteraction:**
| Operation | Endpoint | Description |
|-----------|----------|-------------|
| CREATE | Auto — created by Drug Interaction Agent | Not user-facing |
| READ ALL | `GET /api/interactions/` | Get all detected interactions for current user |
| READ | `GET /api/interactions/{id}` | Single interaction detail |
| DISMISS | `PATCH /api/interactions/{id}/dismiss` | User acknowledges and dismisses warning |
| DELETE | Cascades when source records are deleted | — |

---

### 2.5 `ClinicalParameter` — Phase 2 Extensions

Add these attributes to the existing `ClinicalParameter` class:

```
New attributes (add to Phase 1 class):
  - isolation_forest_score: Optional[float] (set by anomaly detection service)
  - is_anomaly: Optional[bool]
  - ml_risk_contribution: Optional[float] (weight assigned by ML model for this param)
```

---

### 2.6 `RiskScore` — Phase 2 Extensions

```
New attributes:
  - model_id: Optional[str] (FK to MLRiskModel — null if rule-based Phase 1 score)
  - model_version: Optional[str]
  - ml_confidence: Optional[float] (model's confidence in the prediction)
  - scoring_method: Enum["RULE_BASED", "ML_MODEL"] (tracks which engine was used)
```

Upgrade `compute_risk_level()` to use ML model output when `MLRiskModel.is_active == True`, fall back to Phase 1 rule-based logic when no model is active or model load fails.

---

## 3. Phase 2 Feature Modules

---

### Feature 1: Multi-User Authentication System

**Description:** Full JWT-based auth flow. Every API endpoint except `/api/auth/register` and `/api/auth/login` is protected. All data is scoped per `user_id` from token.

**JWT Flow:**
```
Registration:
  POST /api/auth/register → creates User, returns {user_id, email}

Login:
  POST /api/auth/login → validates credentials
  → returns {
      access_token: JWT (expires 15 minutes),
      refresh_token: JWT (expires 7 days),
      token_type: "bearer"
    }
  → refresh_token_hash stored in DB

Authenticated requests:
  Authorization: Bearer <access_token> header required
  FastAPI dependency: get_current_user(token) → validates JWT, returns User

Refresh:
  POST /api/auth/refresh with {refresh_token}
  → validates refresh_token_hash against DB
  → returns new access_token

Logout:
  POST /api/auth/logout
  → sets refresh_token_hash = None in DB
  → client discards both tokens
```

**FastAPI Dependency:**
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise InvalidTokenError
    except JWTError:
        raise InvalidTokenError
    user = db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
    if user is None:
        raise UserNotFoundError
    return user
```

**Validation Rules:**
- Access token expiry: 15 minutes — return `401 Unauthorized` with `{"error": "TokenExpiredError"}`
- Invalid/tampered token — return `401 Unauthorized` with `{"error": "InvalidTokenError"}`
- Inactive user (`is_active=False`) — return `403 Forbidden`
- All data queries must filter by `user_id == current_user.user_id` — never return another user's data
- Rate limit login endpoint: max 5 failed attempts per IP per 15 minutes — return `429 Too Many Requests`

---

### Feature 2: Trained ML Risk Prediction Model

**Description:** Replaces the Phase 1 rule-based threshold engine with a trained `RandomForestClassifier` (or `GradientBoostingClassifier`) that predicts risk level from a structured feature vector of clinical parameters.

**Training Data Strategy (Phase 2):**
```
Since real patient data is unavailable for training, use a synthetic dataset:

1. Define reference ranges for all 15 supported parameters
2. Generate 2000+ synthetic patient profiles using numpy:
   - 40% "LOW risk" profiles (all params within range)
   - 35% "MODERATE risk" profiles (1-2 params mildly elevated)
   - 20% "HIGH risk" profiles (2-3 params significantly elevated)
   - 5% "CRITICAL risk" profiles (multiple severely elevated params)
3. Add gaussian noise to simulate real-world variation
4. Label using Phase 1 rule-based engine (bootstrap ground truth)
5. Train classifier, evaluate on 20% holdout set
6. Target: accuracy > 82%, F1 > 0.80 on all 4 classes
```

**Feature Engineering:**
```python
class FeatureEngineer:
    SUPPORTED_PARAMS = [
        'hba1c', 'fasting_blood_sugar', 'total_cholesterol', 'ldl',
        'hdl', 'triglycerides', 'hemoglobin', 'creatinine', 'egfr',
        'bp_systolic', 'bp_diastolic', 'tsh', 'vitamin_d',
        'vitamin_b12', 'uric_acid'
    ]

    def build_feature_vector(self, user_id: str, db: Session) -> list[float]:
        # For each supported param, get most recent value
        # If param not available: impute with reference_range midpoint
        # Normalize each value: (value - range_min) / (range_max - range_min)
        # Output: ordered list of 15 normalized floats
        ...

    def validate_feature_vector(self, vector: list[float]) -> bool:
        # Must have exactly 15 elements
        # No NaN or infinite values
        # Each element between -0.5 and 3.0 (allowing out-of-range values)
        ...
```

**Model Training Script:** `backend/ml/train_risk_model.py`
```
Steps:
1. Generate synthetic dataset (synthetic_data_generator.py)
2. Feature engineering on all samples
3. Train/test split (80/20, stratified)
4. Hyperparameter tuning: GridSearchCV on n_estimators, max_depth
5. Evaluate: accuracy, F1 (macro), confusion matrix, classification report
6. Save model: joblib.dump(model, 'models/risk_model_v2.pkl')
7. Save feature names + metadata to MLRiskModel DB record
8. Print evaluation report to stdout
```

**Inference in Trend Agent:**
```python
class MLRiskEngine:
    def __init__(self, model: MLRiskModel):
        self.model = model.load()
        self.model_meta = model

    def predict(self, feature_vector: list[float]) -> dict:
        proba = self.model.predict_proba([feature_vector])[0]
        predicted_class = self.model.classes_[proba.argmax()]
        confidence = proba.max()
        return {
            "risk_level": predicted_class,
            "overall_risk": float(proba[2] + proba[3]),  # HIGH + CRITICAL probability
            "confidence": float(confidence),
            "class_probabilities": dict(zip(self.model.classes_, proba.tolist()))
        }
```

**Validation Rules:**
- Feature vector must have exactly 15 elements — raise `InvalidFeatureVectorError`
- If model file missing at `model_path` — fall back to Phase 1 rule-based engine, log warning
- Model accuracy must be logged and stored in `MLRiskModel.training_accuracy`
- Confidence < 0.55 → append warning to RiskScore: "Low model confidence — result may be imprecise"

---

### Feature 3: Isolation Forest Anomaly Detection

**Description:** Replaces simple HIGH/CRITICAL threshold flagging with statistically-grounded anomaly detection on each clinical parameter's time-series.

**How It Works:**
```
For each ClinicalParameter where user has >= 3 historical readings:
  1. Extract all historical values for that param as a time-series array
  2. Fit sklearn IsolationForest on the array
     (contamination=0.1, random_state=42)
  3. Score each data point → anomaly_score (between -1.0 and 0.0)
  4. Flag points where anomaly_score < threshold (default -0.1)
  5. Save AnomalyResult to DB
  6. Update ClinicalParameter.isolation_forest_score + is_anomaly
```

**Implementation Class:**
```python
class AnomalyDetectionService:
    def __init__(self, threshold: float = -0.1, contamination: float = 0.1):
        self.threshold = threshold
        self.contamination = contamination

    def detect_anomalies(self, param_name: str, values: list[float]) -> list[AnomalyResult]:
        if len(values) < 3:
            raise InsufficientDataForAnomalyError(
                f"Need >= 3 readings for {param_name}, got {len(values)}"
            )
        model = IsolationForest(contamination=self.contamination, random_state=42)
        scores = model.fit_predict(np.array(values).reshape(-1, 1))
        anomaly_scores = model.score_samples(np.array(values).reshape(-1, 1))
        results = []
        for i, score in enumerate(anomaly_scores):
            results.append(AnomalyResult(
                param_name=param_name,
                anomaly_score=float(score),
                is_anomaly=bool(score < self.threshold),
                data_points_used=len(values),
            ))
        return results

    def validate_inputs(self, values: list[float]) -> None:
        if any(v is None or np.isnan(v) for v in values):
            raise InvalidParameterValueError("NaN values in time-series")
        if len(set(values)) == 1:
            raise InsufficientVarianceError("All values identical — anomaly detection not meaningful")
```

**UI Integration:**
- Anomaly-flagged data points render as pulsing red dots on the timeline chart
- Tooltip on hover: "Statistical anomaly detected — this reading deviates significantly from your personal baseline"
- Anomaly count badge on Dashboard: "3 anomalies detected across your records"

**Validation Rules:**
- Minimum 3 readings required per parameter for IF to run — show "Collecting baseline — 2 more readings needed" otherwise
- `contamination` must be between 0.01 and 0.5 — raise `InvalidContaminationError`
- `anomaly_score` must be between -1.0 and 0.0 — raise validation error on DB save
- Re-run anomaly detection every time a new reading is added for that parameter

---

### Feature 4: Drug Interaction Checker

**Description:** After every PRESCRIPTION record is processed, a new Drug Interaction Agent checks all currently active medications for potential interactions using embedding-based similarity search against a structured drug knowledge base.

**Drug Knowledge Base (Phase 2):**
```
Source: Open-source drug interaction datasets
  - DrugBank open data (CSV format, free tier)
  - OpenFDA API (free, no key needed for basic queries)
  - Fallback: Groq-generated interaction summaries for common drug pairs

Storage:
  - Import known interactions into ChromaDB collection: "drug_interactions"
  - Each document: "Drug A + Drug B: [severity] — [description]"
  - Embed with sentence-transformers all-MiniLM-L6-v2
```

**Drug Interaction Agent Logic:**
```python
class DrugInteractionAgent:
    def run(self, user_id: str, active_drugs: list[str]) -> list[DrugInteraction]:
        interactions = []
        pairs = list(itertools.combinations(active_drugs, 2))
        
        for drug_a, drug_b in pairs:
            # 1. Query ChromaDB for known interactions
            query = f"{drug_a} interaction with {drug_b}"
            results = chroma_service.query("drug_interactions", query, n_results=3)
            
            if results and results[0]["distance"] < 0.35:
                # High-confidence ChromaDB hit
                interaction = self.parse_chroma_result(results[0], drug_a, drug_b, user_id)
            else:
                # Fallback: ask Groq
                interaction = self.query_groq_for_interaction(drug_a, drug_b, user_id)
            
            if interaction and interaction.severity != "NONE":
                interactions.append(interaction)
        
        return interactions

    def validate_drug_name(self, name: str) -> str:
        # Normalize: lowercase, strip dosage info, match to known drug vocabulary
        # Raise UnrecognizedDrugError if not matchable
        ...
```

**UI Integration:**
- A "Drug Interactions" card on Dashboard — shows count of detected interactions
- `/interactions` page with severity-color-coded cards (red=MAJOR, orange=MODERATE, yellow=MINOR)
- Dismiss button per interaction (doesn't delete — sets `is_dismissed=True` for UX)
- MAJOR/CONTRAINDICATED interactions trigger a non-dismissable banner until user acknowledges

**Validation Rules:**
- Cannot check interactions for fewer than 2 active drugs — return empty list silently
- `drug_a` and `drug_b` must not be the same drug — raise `SameDrugInteractionError`
- ChromaDB distance threshold: 0.35 — above this, always use Groq fallback, never guess
- `severity` must be valid Enum value — raise `InvalidSeverityError`
- Groq fallback must be prompted to return structured JSON — validate before saving:
  ```json
  {"drug_a": "...", "drug_b": "...", "severity": "MODERATE", "description": "...", "recommendation": "..."}
  ```

---

### Feature 5: Mobile-Optimized UI

**Description:** Full mobile-first rebuild of all 7 pages. Key additions: camera capture for prescription uploads, bottom navigation bar for mobile, touch-friendly component sizing.

**Tailwind Breakpoint Strategy:**
```
Mobile-first (default styles = mobile):
  - sm: 640px (large phones, landscape)
  - md: 768px (tablets)
  - lg: 1024px (desktop)

All layout decisions made mobile-first:
  - Grid: grid-cols-1 → md:grid-cols-2 → lg:grid-cols-3
  - Text: text-sm → md:text-base → lg:text-lg
  - Cards: full-width on mobile, constrained on desktop
```

**New Mobile Components:**
```
CameraCapture.jsx
  - Uses browser MediaDevices API (navigator.mediaDevices.getUserMedia)
  - Shows live camera preview in a modal
  - Captures frame as base64 → sends to upload endpoint
  - Falls back to file picker if camera not available
  - Validate: captured image must be >= 200x200px before sending

BottomNav.jsx (mobile only — hidden on md+)
  - 4 tabs: Dashboard, Upload, Reminders, Report
  - Active tab indicated by mint color + icon fill
  - Fixed to bottom of screen (position: fixed, bottom-0)
  - Safe area padding for iOS notch

PullToRefresh.jsx
  - Wraps DashboardPage content
  - On pull-down: re-fetches risk score + recent records
  - Shows a spinner during refresh

SwipeableReminderCard.jsx
  - Swipe left → reveal Delete action
  - Swipe right → reveal Acknowledge action
  - Uses touch event handlers (onTouchStart, onTouchMove, onTouchEnd)
```

**Mobile-Specific Validation:**
- Camera capture: alert if browser denies camera permission — show "Use file upload instead" fallback
- File picker on mobile: accept="image/*,application/pdf" — do not restrict to specific camera
- Touch targets: all interactive elements min 44x44px (accessibility + mobile usability)
- Form inputs: use correct `inputMode` attribute (e.g. `inputMode="decimal"` for value fields)

---

## 4. Phase 2 New Exceptions

Add to `arogya_errors.py`:

```python
# Auth errors
class InvalidEmailError(ArogyaError): pass
class WeakPasswordError(ArogyaError): pass
class InvalidNameError(ArogyaError): pass
class FutureDateOfBirthError(ArogyaError): pass
class EmailAlreadyExistsError(ArogyaError): pass
class InvalidCredentialsError(ArogyaError): pass
class InvalidTokenError(ArogyaError): pass
class TokenExpiredError(ArogyaError): pass
class UserNotFoundError(ArogyaError): pass

# ML errors
class InvalidFeatureVectorError(ArogyaError): pass
class ModelNotFoundError(ArogyaError): pass
class ModelLoadError(ArogyaError): pass
class InvalidContaminationError(ArogyaError): pass
class InsufficientDataForAnomalyError(ArogyaError): pass
class InsufficientVarianceError(ArogyaError): pass

# Drug interaction errors
class SameDrugInteractionError(ArogyaError): pass
class UnrecognizedDrugError(ArogyaError): pass
class InvalidSeverityError(ArogyaError): pass
```

---

## 5. Phase 2 New API Endpoints

### Auth
```
POST   /api/auth/register          New user registration
POST   /api/auth/login             Returns access + refresh token
POST   /api/auth/refresh           Refresh access token
POST   /api/auth/logout            Invalidate refresh token
GET    /api/auth/me                Get current user profile
PUT    /api/auth/me                Update profile
DELETE /api/auth/me                Deactivate account
```

### ML Model Management
```
POST   /api/admin/models/upload    Upload new .pkl model + metadata
GET    /api/admin/models/          List all model versions
GET    /api/admin/models/active    Get active model info
PATCH  /api/admin/models/{id}/activate   Activate a model version
GET    /api/admin/models/{id}/evaluate   Re-run evaluation on holdout set
```

### Anomaly Detection
```
GET    /api/anomalies/             All anomaly results for current user
GET    /api/anomalies/{param_name} Anomaly history for one parameter
POST   /api/anomalies/rerun        Force re-run IF on all parameters
```

### Drug Interactions
```
GET    /api/interactions/          All detected interactions for user
GET    /api/interactions/{id}      Single interaction detail
PATCH  /api/interactions/{id}/dismiss   Dismiss an interaction
POST   /api/interactions/recheck   Re-run interaction check on active meds
```

---

## 6. Phase 2 Folder Additions

```
backend/
├── ml/
│   ├── train_risk_model.py         # Training script (run once)
│   ├── synthetic_data_generator.py # Generates synthetic training dataset
│   ├── feature_engineer.py         # FeatureEngineer class
│   ├── ml_risk_engine.py           # MLRiskEngine class (inference)
│   ├── anomaly_detection_service.py # AnomalyDetectionService class
│   └── models/
│       └── risk_model_v2.pkl       # Trained model artifact
│
├── agents/
│   ├── drug_interaction_agent.py   # NEW: Drug Interaction Agent (LangGraph node)
│   └── graph.py                    # UPDATED: add drug_interaction_agent node
│
├── models/
│   ├── user.py                     # NEW: User ORM model
│   ├── ml_risk_model.py            # NEW: MLRiskModel ORM model
│   ├── anomaly_result.py           # NEW: AnomalyResult ORM model
│   └── drug_interaction.py         # NEW: DrugInteraction ORM model
│
├── routers/
│   ├── auth_router.py              # NEW: /api/auth/* endpoints
│   ├── admin_router.py             # NEW: /api/admin/models/* endpoints
│   ├── anomalies_router.py         # NEW: /api/anomalies/* endpoints
│   └── interactions_router.py      # NEW: /api/interactions/* endpoints
│
├── services/
│   ├── auth_service.py             # JWT creation/validation, bcrypt
│   └── drug_db_service.py          # ChromaDB drug interaction ingestion + query
│
└── data/
    └── drug_db/
        ├── drugbank_open.csv       # Source drug interaction data
        └── ingested_flag.txt       # Marker file — ChromaDB ingestion done

frontend/src/
├── pages/
│   ├── LoginPage.jsx               # NEW
│   ├── RegisterPage.jsx            # NEW
│   └── InteractionsPage.jsx        # NEW
├── components/
│   ├── CameraCapture.jsx           # NEW
│   ├── BottomNav.jsx               # NEW
│   ├── PullToRefresh.jsx           # NEW
│   ├── SwipeableReminderCard.jsx   # NEW
│   └── DrugInteractionCard.jsx     # NEW
└── context/
    └── AuthContext.jsx             # React context for auth state (user, tokens)
```

---

## 7. Phase 2 Build Order (AI IDE Recommended)

```
Step 1: Database & Auth Foundation
  - Create User ORM model + migration
  - Implement auth_service.py (bcrypt + JWT)
  - Build auth_router.py (register, login, refresh, logout, me)
  - Add get_current_user FastAPI dependency
  - Update ALL existing routers to require get_current_user
  - Update all DB queries to filter by current_user.user_id
  - Test: Register → Login → access protected endpoint → refresh → logout

Step 2: ML Training Pipeline
  - Build synthetic_data_generator.py
  - Build feature_engineer.py
  - Run train_risk_model.py → verify model saves to disk
  - Build ml_risk_engine.py (inference wrapper)
  - Update Trend Agent to use MLRiskEngine when active model exists
  - Create MLRiskModel ORM + admin_router.py
  - Test: Feature vector in → risk score out (ML), model activate/deactivate

Step 3: Anomaly Detection
  - Build anomaly_detection_service.py (IsolationForest wrapper)
  - Create AnomalyResult ORM + anomalies_router.py
  - Update Trend Agent to run anomaly detection after risk scoring
  - Update ClinicalParameter: add isolation_forest_score, is_anomaly fields
  - Update Timeline chart: render anomaly dots on flagged readings
  - Test: 3+ readings for a parameter → IF runs → anomaly result saved

Step 4: Drug Interaction Checker
  - Ingest DrugBank CSV into ChromaDB collection drug_interactions
  - Build drug_db_service.py (query + Groq fallback)
  - Build drug_interaction_agent.py (LangGraph node)
  - Update graph.py: add drug_interaction_agent after reminder_agent for PRESCRIPTION records
  - Create DrugInteraction ORM + interactions_router.py
  - Build InteractionsPage.jsx + DrugInteractionCard.jsx
  - Test: 2 interacting drugs in prescription → interaction detected + saved

Step 5: Mobile UI Rebuild
  - Add Tailwind mobile breakpoints to all existing pages
  - Build BottomNav.jsx (visible only on mobile)
  - Build CameraCapture.jsx with MediaDevices API
  - Update UploadPage with camera capture option
  - Build SwipeableReminderCard.jsx
  - Build PullToRefresh.jsx on DashboardPage
  - Test: Full E2E flow on mobile viewport (375px width) in browser devtools

Step 6: Auth UI
  - Build LoginPage.jsx + RegisterPage.jsx
  - Build AuthContext.jsx (stores tokens in memory, refresh logic)
  - Add protected route wrapper (redirect to /login if no token)
  - Update Axios api.js: attach Bearer token to all requests, handle 401 auto-refresh
  - Test: Full auth flow in browser — register → login → access data → refresh → logout

Step 7: Integration & Phase 2 Checklist
  - Run full PHASE2_CHECKLIST.md validation
  - Fix all failing items
  - Run both Phase 1 and Phase 2 checklists — Phase 1 must still pass
```

---

*End of FEATURES_PHASE2.md*
