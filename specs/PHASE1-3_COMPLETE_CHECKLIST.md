# ArogyaMitra AI — Complete Verification Checklist (Phases 1–3)
> Purpose: One checklist for everything specified through Phase 3, major and minor.
> Give this to your AI IDE to verify the real codebase, item by item, with evidence.
> It verifies reality. It adds no new features. Phase 4 is in `PHASE4_IMPLEMENTATION.md`.
> Severity: 🔴 blocks launch | 🟠 fix before public release | 🟡 polish / first month

---

## 0. How the AI IDE must use this file

```
MARKING (edit the checkbox on each line):
  [x]  VERIFIED   - tested or inspected, evidence recorded
  [~]  PARTIAL    - exists but incomplete or differs from spec (add a note)
  [!]  BROKEN     - exists but fails when run (add the error)
  [ ]  NOT DONE   - missing, or not yet verified

EVIDENCE RULES (the first build went wrong because these were skipped):
  1. Never mark [x] from reading file names. Open the file and read the logic.
     A function with `pass`, TODO, or a stub body is [~], not [x].
  2. For anything runnable, run it and paste the real command and output
     into VERIFICATION_LOG.md under the item ID (e.g. "REC-01").
  3. For anything about "no X exists" (no print(), no secrets, no raw SQL),
     paste the grep/search command and its result.
  4. Do not write results to temporary .bat or log files in the repo. Print
     to the terminal and copy into VERIFICATION_LOG.md.
  5. If a check cannot run (service down, access missing), mark [ ] and say why.
  6. Report counts per section at the end using the script in Section 15.

SPEC FILES this checklist verifies against (must be in /specs/):
  FEATURES.md, TECH_STACK.md, PHASE1_CHECKLIST.md,
  FEATURES_PHASE2.md, TECH_STACK_PHASE2.md, PHASE2_CHECKLIST.md,
  FEATURES_PHASE3.md, PHASE3_PLAN_REVIEW.md,
  PRODUCTION_BACKEND.md, SECURITY_AUDIT.md,
  TRANSFORMATION_PROMPT.md, MASTER_STATUS_CHECKLIST.md
```

---

## 1. Machine & Environment Health (ENV)

- [ ] **ENV-01** 🔴 At least 10 GB free on C: and D: (record exact GB)
- [ ] **ENV-02** 🔴 `python --version` is 3.11 or newer; a project virtualenv is active (not global site-packages)
- [ ] **ENV-03** 🟠 `node --version` and `npm --version` run; version matches what the frontend lockfile was built with
- [ ] **ENV-04** 🔴 PostgreSQL reachable: `psql "$DATABASE_URL" -c "select 1"` succeeds
- [ ] **ENV-05** 🔴 Redis reachable: `redis-cli -u $REDIS_URL ping` returns `PONG`
- [ ] **ENV-06** 🟠 `docker --version` works in the IDE terminal, or hosted Postgres/Redis (Supabase/Upstash) is used and documented
- [ ] **ENV-07** 🔴 Tesseract binary installed and on PATH (`tesseract --version`); `pytesseract` can call it
- [ ] **ENV-08** 🔴 Poppler installed and on PATH (needed by `pdf2image` on Windows); a test PDF converts to images
- [ ] **ENV-09** 🟠 `python-magic` works on this OS (Windows usually needs `python-magic-bin`); `magic.from_buffer` returns a MIME type
- [ ] **ENV-10** 🟠 EasyOCR model cache location known and sized; first run does not fail offline
- [ ] **ENV-11** 🔴 `git fsck` reports no corruption
- [ ] **ENV-12** 🔴 `python -m compileall -q backend` passes; zero zero-byte `.py`/`.tsx`/`.json` source files (`Get-ChildItem -Recurse -File | Where Length -eq 0`)
- [ ] **ENV-13** 🟠 No leftover `verify.bat`, `verify_to_file.bat`, temp scripts, or stray `*.log` in the repo
- [ ] **ENV-14** 🟠 No hung `python`/`pip`/`node`/`git` processes; no `.git/index.lock`
- [ ] **ENV-15** 🟠 No recurring scheduled tasks left behind by the IDE (check its schedule/task list)
- [ ] **ENV-16** 🔴 `.env` exists with every required variable; `.env` is not tracked (`git check-ignore .env`)
- [ ] **ENV-17** 🟡 Free space re-checked after a full test run (tests and caches did not refill the disk)

---

## 2. Repository Structure & Hygiene (REPO)

- [ ] **REPO-01** 🔴 `/specs/` contains every spec file listed in Section 0
- [ ] **REPO-02** 🔴 No Express/TypeScript backend remains: no `server.ts`, no `backend/*.ts`, no `package.json` inside `backend/`
- [ ] **REPO-03** 🔴 `_archive_express_version/` is not imported, linted, built, tested, or copied into Docker images
- [ ] **REPO-04** 🟠 Folder layout matches `TECH_STACK.md` §2 (`backend/{core,models,repositories,schemas,routers,agents,services,exceptions,ml}`, `frontend/src/...`)
- [ ] **REPO-05** 🔴 `.gitignore` covers `.env`, `logs/`, `__pycache__/`, `.venv/`, `node_modules/`, `dist/`, `backend/data/`, `*.pkl`, `.pytest_cache/`
- [ ] **REPO-06** 🟠 `requirements.txt` has exact `==` pins; `pipreqs` comparison shows no missing and no unused packages
- [ ] **REPO-07** 🟠 `package-lock.json` committed; `npm ci` succeeds from a clean checkout
- [ ] **REPO-08** 🟠 `.env.example` lists every variable with placeholders only (no real values)
- [ ] **REPO-09** 🟠 README documents: prerequisites, setup, env vars, run commands (API, worker/scheduler, frontend), migrations, tests
- [ ] **REPO-10** 🟡 Git tags mark milestones (`phase1-complete`, `phase2-complete`, `phase3-complete`) only after their checklists pass
- [ ] **REPO-11** 🔴 `gitleaks detect` over full history is clean (or leaked secrets were rotated)
- [ ] **REPO-12** 🟡 Commit messages describe changes; no giant "fix" commits mixing unrelated work

---

## 3. Backend Foundation (CORE)

### 3.1 Configuration & startup
- [ ] **CORE-01** 🔴 `Settings` (pydantic-settings) requires all secrets; no silent defaults for `SECRET_KEY`, `ENCRYPTION_KEY`, `GROQ_API_KEY`, `DATABASE_URL`, `REDIS_URL`
- [ ] **CORE-02** 🔴 Startup validation aborts the app on: short `SECRET_KEY` (<32), `ENCRYPTION_KEY` not base64-of-32-bytes, `DEBUG=True` with `ENVIRONMENT=production`, wildcard CORS in production
- [ ] **CORE-03** 🟠 `SECRET_KEY` and `ENCRYPTION_KEY` are different values
- [ ] **CORE-04** 🟠 Startup summary logged at INFO (version, environment, active model or "rule-based fallback", CORS origins)
- [ ] **CORE-05** 🟠 `GET /health` returns `{"status":"ok","version":...}` with no internal details
- [ ] **CORE-06** 🔴 `/docs`, `/redoc`, `/openapi.json` return 404 when `ENVIRONMENT=production`
- [ ] **CORE-07** 🟡 Long-lived clients (Groq, Redis, Chroma) created once in `lifespan`, closed on shutdown

### 3.2 Database access
- [ ] **CORE-08** 🔴 Async SQLAlchemy engine is a singleton; pool settings applied (`pool_size`, `max_overflow`, `pool_pre_ping`, `pool_recycle`)
- [ ] **CORE-09** 🔴 `get_db` commits on success and rolls back on any exception
- [ ] **CORE-10** 🔴 No `Session()`/engine created inside route handlers or services
- [ ] **CORE-11** 🔴 Zero raw SQL strings built with f-strings or `.format` (`grep -rn 'execute(f"'`)
- [ ] **CORE-12** 🟠 Repositories convert `IntegrityError`/`OperationalError` into `ArogyaError` subclasses; SQLAlchemy exceptions never reach routers
- [ ] **CORE-13** 🟠 All timestamps stored timezone-aware in UTC

### 3.3 Cache (Redis)
- [ ] **CORE-14** 🔴 `ArogyaCache` exposes `get/set/invalidate/invalidate_user` backed by Redis (not an in-process dict)
- [ ] **CORE-15** 🟠 TTLs match spec: risk 300s, params 180s, reminders 60s, family 600s, active model 3600s, interactions 300s
- [ ] **CORE-16** 🔴 Cache keys include `profile_id` (not just `user_id`) for profile-scoped data
- [ ] **CORE-17** 🔴 Second identical request logs a cache HIT (proves caching is wired)
- [ ] **CORE-18** 🟠 Every write endpoint invalidates the affected keys (record, param, reminder, family, risk recompute, model activate)
- [ ] **CORE-19** 🟠 App still works (slower) if Redis is down; failure logged WARNING, not 500
- [ ] **CORE-20** 🟡 `invalidate_user` uses `SCAN`, never `KEYS`

### 3.4 Logging & middleware
- [ ] **CORE-21** 🔴 loguru sinks: daily-rotated app log (30d), error log (90d), console only when `DEBUG=True`
- [ ] **CORE-22** 🔴 Zero `print()` calls in backend code (`grep -rn "print(" backend/`)
- [ ] **CORE-23** 🔴 Logs never contain passwords, tokens, OTPs, API keys, raw OCR text, prompts, LLM output, or file paths (grep logs after a full test run)
- [ ] **CORE-24** 🟠 Every response has `X-Request-ID`; the same ID appears in the log lines for that request
- [ ] **CORE-25** 🟠 Middleware order: TrustedHost → CORS → SecurityHeaders → RequestLogging → RateLimit
- [ ] **CORE-26** 🔴 Security headers present on every response (CSP, HSTS, X-Frame-Options DENY, nosniff, Referrer-Policy, Permissions-Policy); `Server` header suppressed
- [ ] **CORE-27** 🟠 GZip enabled; CORS allows only configured origins, credentials enabled, no `*`

### 3.5 Errors & dependency injection
- [ ] **CORE-28** 🔴 Global handlers registered for `ArogyaError`, `RequestValidationError`, `HTTPException`, and a catch-all `Exception`
- [ ] **CORE-29** 🔴 Error responses never include tracebacks, SQL, file paths, or exception messages from libraries
- [ ] **CORE-30** 🟠 All custom exceptions inherit `ArogyaError` and carry `status_code` and `error_code`
- [ ] **CORE-31** 🔴 `backend/core/dependencies.py` is the single provider module; no Service Locator or global `Container.get(...)`
- [ ] **CORE-32** 🟠 No service or repository is instantiated directly inside a route handler
- [ ] **CORE-33** 🟠 Tests use `app.dependency_overrides` (not monkeypatching globals)
- [ ] **CORE-34** 🟠 No `bare except:` anywhere (`grep -rn "except:" backend/`)

---

## 4. Data Layer & Migrations (DB)

### 4.1 Migrations
- [ ] **DB-01** 🔴 Alembic initialized; `alembic heads` shows exactly one head
- [ ] **DB-02** 🔴 `alembic upgrade head` succeeds on an empty database
- [ ] **DB-03** 🔴 `alembic downgrade -1` then `upgrade head` round-trips cleanly (repeat for the `profile_id` revisions)
- [ ] **DB-04** 🔴 `Base.metadata.create_all()` is only reachable when `ENVIRONMENT=development`
- [ ] **DB-05** 🔴 `profile_id` migration: SELF profile created per existing user, backfilled, assertion of zero NULLs, then NOT NULL + FK + index
- [ ] **DB-06** 🟠 Migrations run as a release step in staging/production, not on every app boot
- [ ] **DB-07** 🟠 Migrations were tested on data shaped like real data, not only an empty DB

### 4.2 Tables (confirm each exists with correct columns, types, constraints)
- [ ] **DB-08** 🔴 Phase 1: `health_records`, `clinical_parameters`, `risk_scores`, `reminders`, `doctor_reports`
- [ ] **DB-09** 🔴 Phase 2: `users`, `ml_risk_models`, `anomaly_results`, `drug_interactions`
- [ ] **DB-10** 🔴 Phase 3: `family_profiles`, `wearable_readings`, `wearable_tokens`, `prediction_results`, `doctor_access`, `subscription_tiers`, `whatsapp_sessions`, `api_keys`
- [ ] **DB-11** 🔴 Support tables exist: API-key audit log, processed webhook events (idempotency)
- [ ] **DB-12** 🔴 `users.email` unique with index; `hashed_password` NOT NULL
- [ ] **DB-13** 🟠 Every health table has `profile_id` NOT NULL with FK to `family_profiles`
- [ ] **DB-14** 🟠 Indexes on `(profile_id)` and `(profile_id, report_date)` for time-series reads; index on `share_token`, `access_token`
- [ ] **DB-15** 🟠 Enum-like columns use a check constraint or DB enum (record_type, risk_level, severity, tier, recurrence)
- [ ] **DB-16** 🟠 JSON columns (`contributing_factors`, `extracted_entities`) use `JSONB` on Postgres
- [ ] **DB-17** 🟠 Soft-delete flags (`is_deleted`, `is_active`) present where specified; list queries exclude deleted rows
- [ ] **DB-18** 🟡 UUID primary keys everywhere; no sequential integer IDs exposed in URLs
- [ ] **DB-19** 🟡 `created_at`/`updated_at` populated automatically

### 4.3 Repositories & ownership
- [ ] **DB-20** 🔴 One repository per entity; routers never build ORM queries
- [ ] **DB-21** 🔴 Every read/update/delete filters by ownership (`profile_id` AND `profile.owner_user_id == current_user.user_id`)
- [ ] **DB-22** 🔴 Nested resources (ClinicalParameter → HealthRecord → Profile) verify ownership through the JOIN
- [ ] **DB-23** 🔴 Request schemas never accept `user_id`, `owner_user_id`, `profile_id` (body), or `is_admin` as client-set fields
- [ ] **DB-24** 🟠 Pagination on every list endpoint (`skip`, `limit` capped at 100)
- [ ] **DB-25** 🟡 No N+1 queries on list endpoints (check with `echo=True` once)

---

## 5. OOP Entities (OOP)

For each entity confirm: `__init__`, `validate()` raising the specified named exception, `to_dict()`, `from_dict()`.

- [ ] **OOP-01** 🔴 `HealthRecord`: invalid type, future date, empty `raw_text` when processed, share-token methods
- [ ] **OOP-02** 🔴 `ClinicalParameter`: `compute_status()` (NORMAL/LOW/HIGH/CRITICAL), negative value, empty unit, unsupported param name
- [ ] **OOP-03** 🔴 `RiskScore`: `overall_risk` clamped 0–1, level thresholds (<0.30 LOW, <0.60 MODERATE, <0.80 HIGH, else CRITICAL), empty factors rejected
- [ ] **OOP-04** 🔴 `Reminder`: title ≥3 chars, due date not past (new) and ≤2 years ahead, valid recurrence
- [ ] **OOP-05** 🟠 `DoctorReport`: non-empty content, at least one record included
- [ ] **OOP-06** 🔴 `User`: email format, password never stored in plain, `to_dict()` excludes `hashed_password` and refresh-token fields
- [ ] **OOP-07** 🟠 `MLRiskModel`, `AnomalyResult`, `DrugInteraction` validations (accuracy 0–1, score −1..0, drug_a ≠ drug_b)
- [ ] **OOP-08** 🟠 `FamilyProfile`: name ≥2, valid relation, ABHA exactly 14 digits, DOB in the past, SELF cannot be removed
- [ ] **OOP-09** 🟠 `PredictionResult`: finite slope, confidence 0–1, ≥3 data points, months-to-threshold >0
- [ ] **OOP-10** 🟠 `DoctorAccess`, `SubscriptionTier`, `WearableReading`, `WhatsAppSession` validations as in `FEATURES_PHASE3.md` §2

---

## 6. Phase 1 Features

### 6.1 Records (`/api/records`)
- [ ] **REC-01** 🔴 `POST /upload` accepts PDF, JPG, PNG; returns **202** with `record_id`; pipeline runs in background
- [ ] **REC-02** 🔴 MIME verified by magic bytes (not the `Content-Type` header); a renamed `.exe` as `.pdf` is rejected
- [ ] **REC-03** 🔴 Files over 10 MB rejected before any processing (400)
- [ ] **REC-04** 🟠 PDF structure check (`%PDF` header, stream-count limit); image minimum 100×100 px
- [ ] **REC-05** 🔴 File saved as `{record_id}.enc`, never using the client filename; AES-256-GCM applied before writing to disk
- [ ] **REC-06** 🔴 The saved `.enc` file is unreadable as plain text (open it and confirm)
- [ ] **REC-07** 🔴 Rate limit 20/hour/user enforced (21st request returns 429)
- [ ] **REC-08** 🟠 Manual text entry creates a `MANUAL_ENTRY` record and still runs validation
- [ ] **REC-09** 🔴 `GET /` returns only the caller's non-deleted records, paginated, with no `raw_text` or file path
- [ ] **REC-10** 🔴 `GET /{id}` returns 404 for a missing record **and** for another user's record (identical response)
- [ ] **REC-11** 🟠 `GET /{id}/download` decrypts in memory, streams, sends `Cache-Control: no-store`, re-checks ownership
- [ ] **REC-12** 🟠 `PUT /{id}` only allows `report_date` and `record_type`; invalid type returns 422; future date rejected
- [ ] **REC-13** 🟠 `DELETE /{id}` soft-deletes, returns 204, cascades to parameters, invalidates caches; encrypted file kept
- [ ] **REC-14** 🟠 Failed processing leaves the record with `is_processed=False` and a sanitized error (not deleted)

### 6.2 OCR & extraction
- [ ] **OCR-01** 🔴 Tesseract extracts text from a sample lab-report PDF
- [ ] **OCR-02** 🔴 EasyOCR extracts text from a sample prescription photo
- [ ] **OCR-03** 🔴 Output shorter than 20 characters raises `OCRExtractionError` and prompts manual entry
- [ ] **OCR-04** 🔴 All 15 supported parameters are extracted from a golden sample (HbA1c, FBS, total cholesterol, LDL, HDL, triglycerides, hemoglobin, creatinine, eGFR, BP systolic/diastolic, TSH, vitamin D, vitamin B12, uric acid)
- [ ] **OCR-05** 🟠 Parameter aliases resolve (e.g. "glycated hemoglobin" → `hba1c`)
- [ ] **OCR-06** 🔴 Groq fallback output is parsed, schema-validated, capped at 20 parameters, unknown names dropped
- [ ] **OCR-07** 🟠 Corrupt or password-protected PDF fails gracefully with a clear message, no crash
- [ ] **OCR-08** 🟡 Extraction accuracy measured on a golden set and recorded (field-level %), even if small

### 6.3 Parameters, risk, reminders, reports, share
- [ ] **PAR-01** 🔴 `GET /api/params/` latest value per parameter, cached, empty list (not 404) when none
- [ ] **PAR-02** 🔴 `GET /api/params/{name}` history sorted by date ascending; unknown name returns 404
- [ ] **PAR-03** 🟠 `PUT /api/params/{id}` re-computes status and risk, invalidates caches, rejects negative or empty-unit input
- [ ] **RSK-01** 🔴 Risk recomputes after every ingestion; weights CRITICAL 0.25, HIGH 0.15, LOW 0.10
- [ ] **RSK-02** 🟠 `GET /api/risk/current` returns the "upload your first report" state (200) when no data
- [ ] **RSK-03** 🟠 `POST /api/risk/recompute` rate-limited 5/hour, increments `version`, returns synchronously
- [ ] **RSK-04** 🟠 `GET /api/risk/history` paginated, newest first
- [ ] **REM-01** 🔴 `POST /api/reminders/` validates title, due date, recurrence, type; returns 201
- [ ] **REM-02** 🟠 `GET` returns active, unacknowledged reminders by due date; `include_acknowledged` works
- [ ] **REM-03** 🟠 `PUT`/`DELETE` check ownership; DELETE is a hard delete
- [ ] **REM-04** 🟠 `PATCH /{id}/ack` is idempotent
- [ ] **REM-05** 🟠 Reminder Agent creates MEDICATION reminders only for PRESCRIPTION records, with `created_from_record_id`, and no duplicates on re-run
- [ ] **RPT-01** 🔴 `POST /api/report/generate` returns 400 if no processed record exists; rate-limited 10/hour
- [ ] **RPT-02** 🔴 Report contains all 6 sections built from database values, not invented numbers (compare against stored data)
- [ ] **RPT-03** 🟠 Output validated (length >200, expected sections), retried once, guardrails applied; includes the "not medical advice" disclaimer
- [ ] **RPT-04** 🟠 PDF downloads non-empty, streamed, `no-store`, ownership checked
- [ ] **SHR-01** 🔴 Share token is a signed JWT with expiry; `GET /share/{token}` needs no login
- [ ] **SHR-02** 🔴 Expired token returns **410**; tampered token returns 400; neither leaks data
- [ ] **SHR-03** 🟠 Regeneration blocked for 1 hour after the last token (429 `SHARE_TOKEN_COOLDOWN`)
- [ ] **SHR-04** 🟠 Shared view is read-only; the token itself is never logged

### 6.4 Agents (LangGraph)
- [ ] **AGT-01** 🔴 `graph.py` compiles; `ArogyaState` has every field in the spec
- [ ] **AGT-02** 🔴 Four nodes exist and are wired: Ingestion → Trend → (PRESCRIPTION only) Reminder; Doctor-Prep on request
- [ ] **AGT-03** 🔴 Each node catches exceptions into `state["errors"]`; one failing node never crashes the graph
- [ ] **AGT-04** 🟠 Each node logs entry, exit with duration, and failure (no PHI)
- [ ] **AGT-05** 🟠 If Ingestion fails the graph stops early; if Trend fails Reminder still runs
- [ ] **AGT-06** 🟠 Partial failures return a "partial" status to the client, not a 500
- [ ] **AGT-07** 🔴 Pipeline runs end to end on a sample record against real Postgres and Redis

---

## 7. Phase 2 Features

### 7.1 Authentication (`/api/auth`)
- [ ] **AUTH-01** 🔴 `register` validates email, password (≥8, 1 upper, 1 number), name; duplicate email returns 409; rate limit 3/hour
- [ ] **AUTH-02** 🔴 Password hashed with bcrypt cost ≥12; stored value starts with `$2b$` (query the DB)
- [ ] **AUTH-03** 🔴 `login` returns the same message for wrong password and unknown email; unknown email still runs a dummy bcrypt check
- [ ] **AUTH-04** 🔴 Login rate limit 5/15 min per IP; per-email lockout after repeated failures
- [ ] **AUTH-05** 🔴 Access token 15 min, in memory on the client; refresh token in an httpOnly, Secure, SameSite=Strict cookie scoped to `/api/auth/refresh`
- [ ] **AUTH-06** 🔴 `refresh` validates type, expiry, and stored hash; revoked tokens rejected
- [ ] **AUTH-07** 🔴 `logout` clears the stored refresh hash server-side (old refresh token fails afterward)
- [ ] **AUTH-08** 🔴 Expired/tampered access tokens return 401; a refresh token cannot be used as an access token
- [ ] **AUTH-09** 🟠 `GET/PUT /me` exclude secrets; `DELETE /me` deactivates (soft), deactivated users cannot log in (403)
- [ ] **AUTH-10** 🔴 Every non-public route returns 401 without a token (enumerate all routes)
- [ ] **AUTH-11** 🔴 IDOR test: User B gets 404 for User A's records, params, reminders, reports, risk scores
- [ ] **AUTH-12** 🔴 `/api/admin/*` requires `require_admin`, returns **404** (not 403) to non-admins; no default admin password

### 7.2 ML risk model
- [ ] **ML-01** 🟠 `synthetic_data_generator.py` produces 2000+ rows, 16 columns, roughly 40/35/20/5 class split
- [ ] **ML-02** 🟠 `train_risk_model.py` runs end to end; holdout accuracy ≥82% and macro F1 ≥0.80 (record actual numbers)
- [ ] **ML-03** 🟠 Feature order identical in training and inference (single `SUPPORTED_PARAMS` list)
- [ ] **ML-04** 🟠 Missing parameters imputed with reference midpoint; vector validated (15 finite floats)
- [ ] **ML-05** 🟠 `MLRiskEngine.predict` returns level, overall risk, confidence, class probabilities; confidence <0.55 adds a warning
- [ ] **ML-06** 🔴 Missing/corrupt model file falls back to rule-based scoring; `scoring_method` records which ran
- [ ] **ML-07** 🟠 Only one active model at a time; active model cannot be deleted; `.pkl` files are gitignored
- [ ] **ML-08** 🟡 Documented honestly: labels are synthetic, so accuracy is not clinical accuracy

### 7.3 Anomaly detection & drug interactions
- [ ] **ANO-01** 🟠 Isolation Forest runs only with ≥3 readings; fewer is a silent skip; identical values raise `InsufficientVarianceError`
- [ ] **ANO-02** 🟠 Scores stored in −1..0; threshold −0.1; `is_anomaly` set on `ClinicalParameter`
- [ ] **ANO-03** 🟡 Timeline marks anomaly points distinctly with an explanatory tooltip
- [ ] **DRG-01** 🟠 Drug knowledge base ingested once (flag file/marker); restart does not re-ingest
- [ ] **DRG-02** 🟠 All active-drug pairs checked; ChromaDB first, Groq fallback only when distance >0.35
- [ ] **DRG-03** 🟠 Groq fallback must return valid JSON; invalid output is logged and skipped, never saved
- [ ] **DRG-04** 🟠 No duplicate interaction rows per drug pair; same drug twice rejected
- [ ] **DRG-05** 🟠 MAJOR/CONTRAINDICATED shows a non-dismissable banner; MINOR/MODERATE only on the interactions page
- [ ] **DRG-06** 🟡 Output carries "consult your doctor" wording; no dosing advice

---

## 8. Phase 3 Features

### 8.1 Family profiles (`/api/family`)
- [ ] **FAM-01** 🔴 SELF profile auto-created at registration; cannot be deleted or deactivated
- [ ] **FAM-02** 🔴 `?profile_id=` defaults to SELF when omitted; a foreign `profile_id` returns 404
- [ ] **FAM-03** 🟠 Member limit enforced by tier (FREE 2, PREMIUM 5, PRO 10)
- [ ] **FAM-04** 🟠 ABHA must be exactly 14 digits; DOB in the past
- [ ] **FAM-05** 🟠 Switching profile changes every page (dashboard, timeline, reminders, reports, predictions)
- [ ] **FAM-06** 🔴 After switching, no previous member's data remains on screen or in client state/cache

### 8.2 Predictive timeline (`/api/predictions`)
- [ ] **PRD-01** 🔴 Needs ≥3 readings; fewer returns a friendly "not enough data" state
- [ ] **PRD-02** 🔴 Regression uses real reading dates (irregular spacing handled)
- [ ] **PRD-03** 🟠 R² <0.40 → `VOLATILE`, no months-to-threshold; improving/stable → no alert
- [ ] **PRD-04** 🟠 Alert levels: ≥24 months WATCH, 12–23 WARN, <12 URGENT; display capped at "36+"
- [ ] **PRD-05** 🟠 Narrative generated from sanitized input, validated, guardrailed, never diagnostic
- [ ] **PRD-06** 🟠 Gated to PREMIUM+ server-side; `rerun` limited to 5/hour
- [ ] **PRD-07** 🟡 Recharts dashed extrapolation renders; card shows confidence and a "talk to your doctor" prompt

### 8.3 Subscription & payments
- [ ] **SUB-01** 🔴 Payment signature (HMAC-SHA256) verified before any tier change
- [ ] **SUB-02** 🔴 Webhook signature verified; duplicate events ignored via stored event IDs
- [ ] **SUB-03** 🔴 Amounts in paise (₹299 → 29900, ₹799 → 79900); order tied to the authenticated user
- [ ] **SUB-04** 🟠 Expiry degrades to FREE without deleting data
- [ ] **SUB-05** 🟠 `require_tier()` returns a clear upgrade message; every gated route enforces it server-side (try with a FREE token)
- [ ] **SUB-06** 🟡 Razorpay test-mode purchase unlocks features immediately in the UI

### 8.4 ABDM / FHIR
- [ ] **ABD-01** 🔴 Adapter interface with a mock and a sandbox implementation; real credential status reported
- [ ] **ABD-02** 🔴 ABDM tokens stored AES-256 encrypted
- [ ] **ABD-03** 🟠 FHIR parse errors are logged and skipped; partial import succeeds
- [ ] **ABD-04** 🟠 Duplicates skipped by FHIR resource ID; 24-hour sync cooldown per profile
- [ ] **ABD-05** 🟡 Imported records flow through the normal ingestion path

### 8.5 Doctor workspace
- [ ] **DOC-01** 🔴 Access resolved only from the signed token; scope enforced server-side
- [ ] **DOC-02** 🔴 No mutating endpoint is reachable with a doctor token
- [ ] **DOC-03** 🔴 Expired or revoked token returns 410; patient can revoke any time
- [ ] **DOC-04** 🟠 Gated to PREMIUM+; per-tier doctor limit enforced (FREE 0, PREMIUM 3)
- [ ] **DOC-05** 🟠 `access_count` and `last_accessed_at` update on each open
- [ ] **DOC-06** 🟠 Page sends `Referrer-Policy: no-referrer`, `noindex`, makes no authenticated calls, removes the token from history
- [ ] **DOC-07** 🟡 Print layout works

### 8.6 Multilingual
- [ ] **LNG-01** 🟠 Hindi OCR extracts values from a sample Hindi report; Hindi aliases added to the single config source
- [ ] **LNG-02** 🟠 Language auto-detect falls back to English below the confidence threshold
- [ ] **LNG-03** 🟠 All UI strings use `t()`; missing keys fall back to English; no raw keys on screen
- [ ] **LNG-04** 🟡 Language switch needs no reload; the choice persists; numerals and units stay consistent
- [ ] **LNG-05** 🟡 Tamil and Telugu: marked NOT STARTED unless actually shipped

### 8.7 Wearables
- [ ] **WER-01** 🔴 OAuth tokens encrypted; refresh handled; failure sets `needs_reconnect`
- [ ] **WER-02** 🔴 Scheduler runs once (dedicated process or Redis lock); verify by starting two instances
- [ ] **WER-03** 🟠 Fitbit sync works; other vendors recorded as deferred if access is unavailable
- [ ] **WER-04** 🟠 Duplicate readings skipped; heart rate outside 30–250 flagged; SpO₂ <85% creates an urgent reminder
- [ ] **WER-05** 🟡 Heart rate and SpO₂ appear on the timeline

### 8.8 WhatsApp bot
- [ ] **WAB-01** 🔴 Twilio signature verified before any processing (forged request returns 403)
- [ ] **WAB-02** 🔴 Message sanitized before intent classification; classifier output restricted to allowed intents
- [ ] **WAB-03** 🔴 Webhook returns 200 quickly; heavy work runs in the background
- [ ] **WAB-04** 🟠 OTP linking: hashed OTP, 10-minute expiry, attempt limits
- [ ] **WAB-05** 🟠 Limits: 20 messages/user/hour and 60/hour webhook; PRO-gated
- [ ] **WAB-06** 🟠 Replies pass output guardrails; no PHI in logs
- [ ] **WAB-07** 🟡 PDF delivery fits media size limits

### 8.9 Voice input
- [ ] **VOI-01** 🔴 Transcript shown and saved only after explicit user confirmation
- [ ] **VOI-02** 🔴 Transcript sanitized before intent parsing; parsed JSON validated
- [ ] **VOI-03** 🟠 Limits enforced: 60 s, 25 MB, webm/mp3/mp4/wav; empty transcript retried once
- [ ] **VOI-04** 🟠 Gated to PREMIUM+; spoken lab value creates a `ClinicalParameter` only after confirmation

### 8.10 Health Score API (`/v1`)
- [ ] **API-01** 🔴 Keys stored as SHA-256 hash; plain key shown once and never logged
- [ ] **API-02** 🔴 Per-profile consent and scope checked on every request
- [ ] **API-03** 🔴 Per-key rate limit via Redis (default 100/hour); 429 with `Retry-After`
- [ ] **API-04** 🟠 Audit record per request (key ID, endpoint, status, time); revoked keys fail immediately
- [ ] **API-05** 🟠 PRO-gated; the web client never holds or sends an API key

---

## 9. AI Safety (AIS)

- [ ] **AIS-01** 🔴 `sanitize_for_prompt()` precedes every Groq call that includes user-derived text (OCR text, notes, WhatsApp, voice)
- [ ] **AIS-02** 🔴 Hardened system prompts used for extraction, report generation, intent classification
- [ ] **AIS-03** 🔴 Injection test: upload a document containing "ignore previous instructions…"; it is blocked or ignored and nothing leaks
- [ ] **AIS-04** 🔴 Every LLM response is validated (schema, length, section markers) before use; failures retry once, then raise a clean error
- [ ] **AIS-05** 🔴 `apply_output_guardrails()` applied to everything stored, sent, or rendered (reports, narratives, bot replies)
- [ ] **AIS-06** 🟠 Guardrail tests: prescriptive medication advice, diagnosis claims, phone/email leakage are stripped or blocked
- [ ] **AIS-07** 🟠 Groq timeouts and errors handled with backoff; app degrades to rule-based paths where specified
- [ ] **AIS-08** 🟠 Disclaimer present on reports, predictions, and bot answers: informational only, not medical advice
- [ ] **AIS-09** 🟡 Token and request budgets set per user to cap LLM cost

---

## 10. Security (SEC) — full list lives in `SECURITY_AUDIT.md`

- [ ] **SEC-01** 🔴 `SECURITY_AUDIT.md` run in full; all 62 🔴 items pass (record the count)
- [ ] **SEC-02** 🔴 No secret in source, frontend bundle, logs, or git history; no `VITE_` variable holds a secret
- [ ] **SEC-03** 🔴 `GET /.env`, `/.git/config`, the database path, `/requirements.txt` return 404 on the deployed app
- [ ] **SEC-04** 🔴 `pip-audit` and `npm audit` show no HIGH/CRITICAL findings
- [ ] **SEC-05** 🔴 Encrypted files are never served by a static mount or CDN
- [ ] **SEC-06** 🟠 Rate limits match the table: login 5/15min, register 3/h, upload 20/h, report 10/h, share 30/h, recompute 5/h, predictions rerun 5/h
- [ ] **SEC-07** 🟠 Origin/Referer check on state-changing requests in production
- [ ] **SEC-08** 🟠 Postgres connection uses TLS; app database role is least-privilege (not a superuser)
- [ ] **SEC-09** 🟠 Backups exist **and a restore was actually tested**
- [ ] **SEC-10** 🟡 Pre-commit `gitleaks` hook installed

---

## 11. Frontend (FE)

### 11.1 App shell & state
- [ ] **FE-01** 🔴 `npm run build` succeeds with zero errors; `npm run lint` clean
- [ ] **FE-02** 🔴 Routing: public routes (`/login`, `/register`, `/share/:token`, `/doctor-view/:token`) and protected routes redirect to login when unauthenticated
- [ ] **FE-03** 🔴 Access token held in memory only; zero `localStorage`/`sessionStorage` token writes (`grep`)
- [ ] **FE-04** 🔴 Axios interceptor refreshes once on 401, retries the request, never loops on the refresh call, and logs out if refresh fails
- [ ] **FE-05** 🟠 After login, the intended page is restored
- [ ] **FE-06** 🔴 `profile_id` is attached only to profile-scoped endpoints (not auth, subscription, or API-key calls)
- [ ] **FE-07** 🔴 Profile switch clears cached lists, charts, and form state; no flash of the previous member's data
- [ ] **FE-08** 🔴 No `dangerouslySetInnerHTML` with user or LLM content
- [ ] **FE-09** 🟠 `VITE_API_URL` is the only environment variable read by the client

### 11.2 Pages
- [ ] **FE-10** 🟠 Auth page: inline validation, password strength, confirm-password match, show/hide, loading state, error toast
- [ ] **FE-11** 🟠 Dashboard: risk gauge colors, empty state, recent records (5), reminders (3), interaction banner, anomaly badge, prediction alerts
- [ ] **FE-12** 🟠 Upload: drag-and-drop, camera capture with permission-denied fallback, size/type errors before upload, manual entry with inline errors, voice input with confirm step
- [ ] **FE-13** 🟠 Timeline: parameter dropdown only for params with data, reference band, "not enough data" state, anomaly dots, prediction line
- [ ] **FE-14** 🟠 Reminders: create/edit/delete with confirmation, acknowledge (optimistic), recurrence badge, swipe actions on mobile
- [ ] **FE-15** 🟠 Report: generate disabled with tooltip when no processed record; loading state; formatted preview; PDF download; share link copy with toast
- [ ] **FE-16** 🟠 Family page, subscription page (tier cards, current-plan badge, upgrade flow), predictions page (gated with upgrade CTA)
- [ ] **FE-17** 🟠 Doctor workspace and share pages: read-only, expired/invalid states, no edit controls
- [ ] **FE-18** 🟠 Screens for doctor-access grant/revoke, wearable connect, ABDM connect, WhatsApp linking, API-key management exist or are marked NOT STARTED

### 11.3 Quality
- [ ] **FE-19** 🟠 Every async view has loading, empty, and error states
- [ ] **FE-20** 🟠 API errors shown as friendly toasts (never raw exception names or stack traces)
- [ ] **FE-21** 🟠 Layouts verified at 375, 768, and 1280 px; no horizontal scroll; bottom nav only on mobile
- [ ] **FE-22** 🟠 Touch targets ≥44 px; correct `inputMode` on numeric/email fields
- [ ] **FE-23** 🟡 Keyboard navigation and visible focus; form fields have labels; color is not the only status signal
- [ ] **FE-24** 🟡 Contrast ≥4.5:1 for body text on the teal/mint palette
- [ ] **FE-25** 🟡 Palette respected (teal `#1A6B5A`, mint `#4ECBA0`); dark mode and glass effects added last and do not hurt contrast
- [ ] **FE-26** 🟡 Bundle size reviewed; routes lazy-loaded; no unused dependencies (`depcheck`)
- [ ] **FE-27** 🟠 Backend health poll on load with a friendly offline state

---

## 12. Testing & CI (TST)

- [ ] **TST-01** 🔴 `pytest` runs and passes; report pass/fail counts
- [ ] **TST-02** 🟠 Coverage ≈80% overall and 100% of branches in auth, ownership, tier gates, payment verification, webhook verification (report the numbers)
- [ ] **TST-03** 🔴 IDOR regression tests exist for records, params, reminders, reports, family profiles, predictions, wearables, doctor access, API keys
- [ ] **TST-04** 🟠 Unit tests cover each OOP `validate()` branch and each service
- [ ] **TST-05** 🟠 Integration tests use `TestClient` with dependency overrides and a real test Postgres/Redis
- [ ] **TST-06** 🟠 Webhook tests use correctly signed and badly signed payloads (Razorpay, Twilio)
- [ ] **TST-07** 🟠 Playwright covers: register → upload → dashboard → timeline → reminder → report → share → add family member → switch profile → prediction → upgrade → doctor access
- [ ] **TST-08** 🟠 CI runs `ruff`, `mypy`, `bandit`, `pip-audit`, `npm audit`, `gitleaks`, tests, and builds
- [ ] **TST-09** 🟡 Tests do not write into the repo or fill the disk (temp directories cleaned)
- [ ] **TST-10** 🟡 Phase 1 (156) and Phase 2 (189) checklists still pass after Phase 3 changes

---

## 13. Operations & Deployment Readiness (OPS)

- [ ] **OPS-01** 🔴 No automatic deploy; deployment is manual after checklists pass
- [ ] **OPS-02** 🟠 Docker image builds; excludes `.env`, `.git`, `backend/data`, `logs`, `_archive_express_version`; no secret in any image layer
- [ ] **OPS-03** 🟠 Process model documented: API, scheduler (single instance), worker if any
- [ ] **OPS-04** 🟠 Reverse proxy or platform edge terminates TLS; HTTP redirects to HTTPS; uvicorn is not directly exposed
- [ ] **OPS-05** 🟠 CDN serves only the built frontend with hashed asset names; `index.html` is `no-cache`
- [ ] **OPS-06** 🟠 Log files rotate and do not grow unbounded; disk usage alert exists (the first build died from a full disk)
- [ ] **OPS-07** 🟠 Daily database backup to encrypted storage; restore procedure written and tested
- [ ] **OPS-08** 🟡 `robots.txt` disallows `/api/admin/` and `/doctor-view/`
- [ ] **OPS-09** 🟡 Production checklist from `PRODUCTION_BACKEND.md` §12 completed

---

## 14. Documentation & Minor Hygiene (DOCS)

- [ ] **DOCS-01** 🟠 Spec files and this checklist live in `/specs/` and match the code (update specs when behavior intentionally changes)
- [ ] **DOCS-02** 🟡 Docstrings on public services and repositories; type hints throughout
- [ ] **DOCS-03** 🟡 `CHANGELOG.md` records what each phase delivered
- [ ] **DOCS-04** 🟡 Known limitations documented (synthetic ML labels, deferred vendors, languages not shipped)
- [ ] **DOCS-05** 🟡 No dead code, commented-out blocks, or unused imports (`ruff` clean)
- [ ] **DOCS-06** 🟡 Consistent naming: snake_case Python, PascalCase React components, kebab-case routes
- [ ] **DOCS-07** 🟡 One source of truth for supported parameters (backend `config.py`; frontend mirrors it, not a second copy of the logic)

---

## 15. Counting Script & Sign-off

Run from the repo root to count items per section:

```python
# count_checklist.py  (run: python count_checklist.py specs/PHASE1-3_COMPLETE_CHECKLIST.md)
import re, sys
section, counts = "Preamble", {}
for line in open(sys.argv[1], encoding="utf-8"):
    if line.startswith("## "):
        section = line.strip()
    m = re.match(r"- \[(.)\] \*\*", line)
    if m:
        c = counts.setdefault(section, {"x": 0, "~": 0, "!": 0, " ": 0})
        c[m.group(1)] += 1
for s, c in counts.items():
    total = sum(c.values())
    print(f"{s}: verified {c['x']}/{total}  partial {c['~']}  broken {c['!']}  open {c[' ']}")
```

| Section | Verified | Partial | Broken | Open |
|---------|:-------:|:-------:|:------:|:----:|
| 1 Environment | | | | |
| 2 Repository | | | | |
| 3 Backend foundation | | | | |
| 4 Data layer | | | | |
| 5 OOP entities | | | | |
| 6 Phase 1 features | | | | |
| 7 Phase 2 features | | | | |
| 8 Phase 3 features | | | | |
| 9 AI safety | | | | |
| 10 Security | | | | |
| 11 Frontend | | | | |
| 12 Testing & CI | | | | |
| 13 Operations | | | | |
| 14 Documentation | | | | |

**Rules for "Phases 1–3 complete":**
1. Every 🔴 item is `[x]` with evidence in `VERIFICATION_LOG.md`.
2. Every 🟠 item is `[x]`, or has a written reason for deferral.
3. `SECURITY_AUDIT.md` passes, and the Phase 1 and 2 checklists still pass.
4. Anything that depends on external access (ABDM sandbox, Garmin, Twilio production, Razorpay live) is listed as available or unavailable, never marked done from a mock.

**Known-issues log (IDE fills in):**

| ID | Problem | Severity | Owner | Fix status |
|----|---------|----------|-------|-----------|
| | | | | |

---

*End of PHASE1-3_COMPLETE_CHECKLIST.md*
