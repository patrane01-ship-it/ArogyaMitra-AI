# ArogyaMitra AI — Phase 2 Validation Checklist
> Use this after completing Phase 1 Checklist (all 156 items must be passing)
> Phase 2 introduces 5 major upgrades — validate each independently
> Status: [ ] Pending | [x] Done | [!] Failed — needs fix

---

## PRE-CONDITION: Phase 1 Still Passing

Before running any Phase 2 validation, confirm Phase 1 is intact:

- [ ] All Phase 1 CRUD endpoints still return correct responses
- [ ] Ingestion → Trend → Reminder agent pipeline still runs on sample upload
- [ ] Doctor-Prep report generation still works
- [ ] Phase 1 risk scoring (rule-based) still works when no ML model is active
- [ ] AES encryption still applied to uploaded files

**Do not proceed to Phase 2 validation if any Phase 1 item is broken.**

---

## SECTION 1: Database Migrations

- [ ] Alembic is initialized (`alembic init alembic` run, `alembic.ini` configured)
- [ ] `users` table created with all 10 columns
- [ ] `users.email` has a UNIQUE index
- [ ] `ml_risk_models` table created with all 9 columns
- [ ] `anomaly_results` table created with all 10 columns
- [ ] `drug_interactions` table created with all 11 columns
- [ ] `clinical_parameters` table has 3 new columns: `isolation_forest_score`, `is_anomaly`, `ml_risk_contribution`
- [ ] `risk_scores` table has 4 new columns: `model_id`, `model_version`, `ml_confidence`, `scoring_method`
- [ ] All existing Phase 1 data is preserved after migration (no data loss)
- [ ] `alembic upgrade head` runs without errors on a fresh DB
- [ ] `alembic downgrade -1` correctly reverses the last migration

---

## SECTION 2: Multi-User Authentication

### User OOP Entity
- [ ] `User` class exists in `backend/models/user.py`
- [ ] `set_password()` stores bcrypt hash — NEVER stores plain text
- [ ] `verify_password()` returns `True` for correct password, `False` for wrong
- [ ] `validate()` raises `InvalidEmailError` for malformed email
- [ ] `validate()` raises `FutureDateOfBirthError` for DOB in future
- [ ] `compute_age()` returns correct integer age from DOB
- [ ] `to_dict()` does NOT include `hashed_password` or `refresh_token_hash` in output
- [ ] `from_dict()` correctly reconstructs object from DB row

### Registration & Login
- [ ] `POST /api/auth/register` creates user, returns 201 with `{user_id, email}`
- [ ] `POST /api/auth/register` rejects duplicate email with 409 Conflict
- [ ] `POST /api/auth/register` rejects password < 8 chars with 422
- [ ] `POST /api/auth/register` rejects password with no uppercase with 422
- [ ] `POST /api/auth/register` rejects password with no number with 422
- [ ] `POST /api/auth/register` rejects invalid email format with 422
- [ ] `POST /api/auth/login` returns `{access_token, refresh_token, token_type: "bearer"}`
- [ ] `POST /api/auth/login` wrong password returns 401 — error message does NOT say which field is wrong
- [ ] `POST /api/auth/login` sets `last_login` datetime on User record
- [ ] `POST /api/auth/login` rate-limited: 6th attempt within 15 min returns 429

### Token Validation
- [ ] Access token decodes correctly via `python-jose`
- [ ] Access token expires after 15 minutes (test by manually setting short expiry)
- [ ] Expired access token returns 401 `TokenExpiredError`
- [ ] Tampered token (modified payload) returns 401 `InvalidTokenError`
- [ ] `GET /api/auth/me` returns current user profile (no hashed_password field)
- [ ] `GET /api/auth/me` without token returns 401
- [ ] `GET /api/records/` without token returns 401
- [ ] All 15+ protected endpoints return 401 without valid token

### Refresh & Logout
- [ ] `POST /api/auth/refresh` returns new access_token
- [ ] `POST /api/auth/refresh` with invalid refresh_token returns 401
- [ ] `POST /api/auth/logout` sets `refresh_token_hash = None` in DB
- [ ] After logout, `POST /api/auth/refresh` returns 401 (old refresh token invalid)

### Data Isolation
- [ ] User A cannot access User B's records via `GET /api/records/{id}`
- [ ] User A cannot access User B's risk scores via `GET /api/risk/current`
- [ ] User A cannot access User B's reminders or doctor reports
- [ ] All DB queries filter by `user_id == current_user.user_id` — verified in code review
- [ ] Soft-deleted user (`is_active=False`) cannot login (returns 403)

### Profile Management
- [ ] `PUT /api/auth/me` updates `full_name`, `date_of_birth`, `gender` successfully
- [ ] `DELETE /api/auth/me` sets `is_active=False`, does not hard-delete
- [ ] Deactivated user's records remain in DB (for data recovery)

---

## SECTION 3: Trained ML Risk Prediction Model

### Data Generation & Training
- [ ] `synthetic_data_generator.py` runs without error and produces a CSV
- [ ] Generated CSV has exactly 16 columns (15 features + risk_level label)
- [ ] Label distribution: roughly 40% LOW, 35% MODERATE, 20% HIGH, 5% CRITICAL (±10%)
- [ ] `train_risk_model.py` runs end-to-end without error
- [ ] Model saved as `.pkl` file at configured `ACTIVE_MODEL_PATH`
- [ ] `MLRiskModel` record created in DB with `training_accuracy` populated
- [ ] Training accuracy on holdout set >= 82%
- [ ] F1 score (macro) >= 0.80 on all 4 classes
- [ ] Classification report printed to stdout during training

### Feature Engineering
- [ ] `FeatureEngineer.build_feature_vector()` returns a list of exactly 15 floats
- [ ] Missing parameter imputed with reference_range midpoint (not 0, not NaN)
- [ ] All values normalized to roughly 0.0–1.0 range (out-of-range values can exceed)
- [ ] `validate_feature_vector()` raises `InvalidFeatureVectorError` if vector length != 15
- [ ] `validate_feature_vector()` raises error if any element is NaN or infinite
- [ ] Feature order is IDENTICAL in training and inference (same `SUPPORTED_PARAMS` list)

### MLRiskEngine Inference
- [ ] `MLRiskEngine.predict()` returns `{risk_level, overall_risk, confidence, class_probabilities}`
- [ ] `overall_risk` is always between 0.0 and 1.0
- [ ] `confidence < 0.55` appends warning to `RiskScore.recommendations`
- [ ] If model `.pkl` file missing at startup — falls back to Phase 1 rule-based engine (logged as WARNING, not crash)
- [ ] `scoring_method` field on saved `RiskScore` = "ML_MODEL" when ML used, "RULE_BASED" when fallback

### Model Management API
- [ ] `POST /api/admin/models/upload` uploads `.pkl` + metadata, creates `MLRiskModel` record
- [ ] `GET /api/admin/models/active` returns currently active model with version + accuracy
- [ ] `PATCH /api/admin/models/{id}/activate` sets target model active, deactivates all others
- [ ] Cannot delete an active model — returns 400 with clear error message
- [ ] Only one model can be active at a time (verified in DB after activation)

---

## SECTION 4: Isolation Forest Anomaly Detection

### AnomalyDetectionService
- [ ] `AnomalyDetectionService.detect_anomalies()` runs without error on a list of 5+ floats
- [ ] Returns list of `AnomalyResult` objects with `anomaly_score` between -1.0 and 0.0
- [ ] `is_anomaly=True` for scores below `threshold` (-0.1 default)
- [ ] `is_anomaly=False` for scores above threshold
- [ ] Raises `InsufficientDataForAnomalyError` when input has < 3 values
- [ ] Raises `InsufficientVarianceError` when all values are identical
- [ ] Raises `InvalidParameterValueError` when input contains NaN

### Integration with Trend Agent
- [ ] Trend Agent runs anomaly detection after ML/rule-based risk scoring
- [ ] `AnomalyResult` records saved to DB for each parameter with >= 3 readings
- [ ] `ClinicalParameter.isolation_forest_score` updated after detection
- [ ] `ClinicalParameter.is_anomaly` set to `True`/`False` correctly
- [ ] For parameters with < 3 readings: no `AnomalyResult` created (no error — silent skip)

### Anomaly API
- [ ] `GET /api/anomalies/` returns all anomaly results for current user
- [ ] `GET /api/anomalies/{param_name}` returns anomaly history for one parameter sorted by `computed_at`
- [ ] `POST /api/anomalies/rerun` re-runs IF on all parameters and returns updated results

### Anomaly UI
- [ ] Timeline chart renders anomaly-flagged points as visually distinct (different color/shape) from normal points
- [ ] Hovering/tapping an anomaly point shows a tooltip with explanation text
- [ ] Dashboard shows anomaly count badge: "X anomalies detected"
- [ ] Badge is not shown if 0 anomalies detected (no zero-count badge)

---

## SECTION 5: Drug Interaction Checker

### Knowledge Base Ingestion
- [ ] DrugBank CSV loaded from `DRUG_DB_CSV_PATH` without error
- [ ] `DrugDBService.ingest_from_csv()` runs and returns count > 0
- [ ] ChromaDB `drug_interactions` collection exists after ingestion
- [ ] `ingested_flag.txt` created after first ingestion
- [ ] On app restart: ingestion is skipped if `ingested_flag.txt` exists
- [ ] `DrugDBService.query_interaction()` returns results with distance scores

### DrugInteractionAgent
- [ ] Agent runs only for PRESCRIPTION records (not LAB_REPORT, DOCTOR_NOTE, etc.)
- [ ] Agent correctly identifies all active drugs for the user (from MEDICATION reminders)
- [ ] All drug name pairs generated via `itertools.combinations()`
- [ ] ChromaDB query used first — Groq fallback triggered only if distance > 0.35
- [ ] Groq fallback returns valid JSON with all required fields
- [ ] Groq JSON response validated before saving — malformed response raises error (agent logs, continues)
- [ ] `DrugInteraction` created only if `severity != "NONE"`
- [ ] `SameDrugInteractionError` raised if `drug_a == drug_b`
- [ ] No duplicate interactions created for same drug pair (check before insert)

### Drug Interaction API & UI
- [ ] `GET /api/interactions/` returns all non-dismissed interactions for user
- [ ] `GET /api/interactions/{id}` returns single interaction with full description
- [ ] `PATCH /api/interactions/{id}/dismiss` sets `is_dismissed=True`
- [ ] `POST /api/interactions/recheck` re-runs agent on all active drugs, returns new results
- [ ] `InteractionsPage.jsx` renders interaction cards with severity color-coding
- [ ] MAJOR/CONTRAINDICATED interaction shows a non-dismissable banner on Dashboard
- [ ] MINOR/MODERATE interactions shown only on `/interactions` page
- [ ] Dismissed interactions do not appear in `GET /api/interactions/` by default

---

## SECTION 6: Mobile-Optimized UI

### Responsive Layouts
- [ ] `DashboardPage` renders correctly at 375px width (iPhone SE viewport)
- [ ] `DashboardPage` renders correctly at 768px width (tablet viewport)
- [ ] `DashboardPage` renders correctly at 1280px width (desktop viewport)
- [ ] All 7 pages have no horizontal scroll at 375px viewport width
- [ ] Card grids stack to single column on mobile, expand on larger screens
- [ ] All font sizes readable without zoom at 375px (min 14px body text)

### BottomNav
- [ ] `BottomNav` visible only on screens < 768px (`md:hidden`)
- [ ] Desktop `Navbar` visible only on screens >= 768px (`hidden md:flex`)
- [ ] BottomNav has 4 tabs: Dashboard, Upload, Reminders, Report
- [ ] Active tab has mint color and filled icon state
- [ ] BottomNav is fixed to bottom, does not overlap page content (page has `pb-20` on mobile)

### CameraCapture
- [ ] Camera modal opens on "Take Photo" button tap
- [ ] Live camera preview renders in the modal
- [ ] "Capture" button freezes frame and converts to File object
- [ ] Captured file sent to same `POST /api/records/upload` endpoint as file picker
- [ ] If `getUserMedia` denied by browser: shows "Use file upload instead" fallback without crashing
- [ ] Captured image validated: minimum 200x200px before sending (show error if too small)
- [ ] Camera uses rear-facing mode on mobile (`facingMode: "environment"`)

### PullToRefresh
- [ ] On DashboardPage: pull-down gesture (>60px) triggers refresh
- [ ] Spinner shown during refresh network calls
- [ ] Dashboard data updates after refresh completes
- [ ] PullToRefresh does not interfere with normal vertical scroll

### SwipeableReminderCard
- [ ] Swipe left on reminder card reveals red Delete action
- [ ] Swipe right on reminder card reveals green Acknowledge action
- [ ] Tap on revealed action executes the action (no second tap)
- [ ] Card snaps back if swipe is released without reaching action threshold

### Touch Targets
- [ ] All buttons and interactive elements have minimum 44x44px touch area
- [ ] Form inputs use correct `inputMode` attribute (`decimal` for number fields, `email` for email)
- [ ] No tap targets closer than 8px to adjacent elements

---

## SECTION 7: Auth UI

### LoginPage & RegisterPage
- [ ] `/login` route renders `LoginPage` when user is not authenticated
- [ ] `/register` route renders `RegisterPage`
- [ ] Login form shows inline validation (not just API errors) for empty fields
- [ ] Register form shows password strength indicator
- [ ] Register form confirms password match before submitting
- [ ] After successful login: redirect to Dashboard
- [ ] After successful register: redirect to Login with success toast

### AuthContext
- [ ] `AuthContext.jsx` provides `{user, accessToken, login, logout, refreshToken}` to app
- [ ] `accessToken` stored in React state — NOT in localStorage or sessionStorage
- [ ] On app load: auto-refresh attempted via `POST /api/auth/refresh` (httpOnly cookie)
- [ ] If refresh succeeds: user treated as logged in, Dashboard shown
- [ ] If refresh fails: user redirected to `/login`

### Protected Routes
- [ ] All routes except `/login`, `/register`, `/share/:token` redirect to `/login` if no access token
- [ ] After token expires: Axios interceptor tries refresh automatically before showing 401 error
- [ ] If refresh fails: user redirected to `/login`, current page URL saved for post-login redirect
- [ ] Logout clears auth state and redirects to `/login`

### Axios Interceptor
- [ ] Every API request automatically includes `Authorization: Bearer <access_token>` header
- [ ] On 401 response: interceptor tries `POST /api/auth/refresh` once
- [ ] If refresh succeeds: original request retried with new token
- [ ] If refresh fails: logout triggered, user redirected to login
- [ ] Interceptor does NOT retry the refresh request itself on 401 (infinite loop prevention)

---

## SECTION 8: New Exception Coverage

- [ ] All 18 new Phase 2 exceptions defined in `arogya_errors.py`
- [ ] All new exceptions inherit from `ArogyaError`
- [ ] Auth exceptions return correct HTTP status codes:
  - `InvalidCredentialsError` → 401
  - `EmailAlreadyExistsError` → 409
  - `InvalidTokenError` / `TokenExpiredError` → 401
  - `WeakPasswordError` / `InvalidEmailError` → 422
- [ ] ML exceptions degrade gracefully (log + fallback, not crash)
- [ ] Drug interaction exceptions log errors and continue pipeline (never crash graph)
- [ ] Frontend displays all auth errors as toasts with user-friendly messages (not raw exception names)

---

## SECTION 9: End-to-End Phase 2 Flow Test

Run this full scenario and confirm all steps pass:

```
Step 1:  Register a new user (User A)
Step 2:  Login as User A → receive access + refresh tokens
Step 3:  Upload a lab report PDF as User A
Step 4:  Verify ML risk scoring used (scoring_method = "ML_MODEL" in risk score)
Step 5:  Verify anomaly detection ran (AnomalyResult records exist for params with 3+ readings)
Step 6:  Upload 2 more lab reports to get 3+ readings for HbA1c
Step 7:  Verify HbA1c anomaly detection ran (AnomalyResult for HbA1c exists)
Step 8:  Upload a prescription image with 2+ known interacting drugs
Step 9:  Verify DrugInteraction record created for the drug pair
Step 10: Open InteractionsPage → verify interaction card appears with correct severity
Step 11: Dismiss a MINOR interaction → verify it disappears from the list
Step 12: Register User B in a new browser tab
Step 13: Login as User B → try to access User A's record_id via GET /api/records/{id}
Step 14: Verify 404 returned (not User A's data)
Step 15: Let access token expire (set to 1 min for testing) → make an API call
Step 16: Verify Axios interceptor auto-refreshes token and retries the call
Step 17: Logout User A → try to refresh → verify 401
Step 18: Open app on 375px viewport → verify BottomNav visible, Navbar hidden
Step 19: Open UploadPage on mobile → tap "Take Photo" → capture image → upload
Step 20: Pull down on Dashboard → verify data refreshes
Step 21: Swipe left on a reminder card → tap Delete → verify reminder gone
Step 22: Navigate to Timeline → verify anomaly points rendered distinctly
Step 23: Deactivate ML model via PATCH /api/admin/models/{id}/activate with different model
         → Upload new record → verify scoring_method = "RULE_BASED"
Step 24: Re-activate ML model → upload record → verify scoring_method = "ML_MODEL"
```

All 24 steps passing = **Phase 2 Complete ✅**

---

## SECTION 10: Code Quality & Security Checks

- [ ] `hashed_password` never appears in any API response body
- [ ] `refresh_token_hash` never appears in any API response body
- [ ] No plain-text passwords anywhere in codebase (grep for "password" + verify)
- [ ] `bcrypt` rounds >= 12 (configured in `.env` as `BCRYPT_ROUNDS=12`)
- [ ] All new ORM models have `__init__`, `validate()`, `to_dict()`, `from_dict()`
- [ ] `train_risk_model.py` is a standalone script — not imported by FastAPI app
- [ ] Model `.pkl` files are in `.gitignore` (too large for git)
- [ ] `drug_db/drugbank_open.csv` is in `.gitignore` if it contains proprietary data
- [ ] Rate limiting applied to `/api/auth/login` and `/api/auth/register`
- [ ] No `bare except:` in any new auth or ML code
- [ ] Axios interceptor has loop prevention (does not retry refresh endpoint on 401)
- [ ] All 4 new DB tables have correct FK constraints (verified via Alembic schema)

---

## Phase 2 Sign-Off

| Section | Total Items | Passed | Failed |
|---------|-------------|--------|--------|
| Pre-condition: Phase 1 Still Passing | 5 | | |
| 1. Database Migrations | 11 | | |
| 2. Multi-User Authentication | 33 | | |
| 3. Trained ML Risk Model | 20 | | |
| 4. Isolation Forest Anomaly Detection | 16 | | |
| 5. Drug Interaction Checker | 20 | | |
| 6. Mobile-Optimized UI | 24 | | |
| 7. Auth UI | 16 | | |
| 8. New Exception Coverage | 8 | | |
| 9. E2E Flow Test | 24 | | |
| 10. Code Quality & Security | 12 | | |
| **TOTAL** | **189** | | |

**Phase 2 is complete when all 189 items are checked ✅**
**Combined: Phase 1 (156) + Phase 2 (189) = 345 total validation checkpoints**

---

*End of PHASE2_CHECKLIST.md*
