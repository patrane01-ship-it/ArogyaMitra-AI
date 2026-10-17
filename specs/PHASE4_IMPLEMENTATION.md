# ArogyaMitra AI — Phase 4 Implementation Specification
> Theme: **Trust, Intelligence & Reliability**
> Prerequisite: Phases 1–3 verified with `PHASE1-3_COMPLETE_CHECKLIST.md`
> Target: AI IDE context file — specification, build order, paste-ready prompt, acceptance checklist
> Stack stays: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Redis + LangGraph + Groq + ChromaDB + React/Vite/Tailwind

---

## 0. What Phase 4 Is (and Why)

Phases 1–3 built features. Phase 4 makes ArogyaMitra safe to hand to real people with
real medical records. It has four goals:

1. **Trust** — consent, export, erasure, children's data, audit trail, account security
   (India's data protection rules are now law and are phased in; see Section 2).
2. **Data quality** — OCR you can correct, lab-specific reference ranges, unit
   normalization. Every prediction and risk score is only as good as the extracted numbers.
3. **Intelligence that stays honest** — grounded "ask your records", explainable risk,
   model governance. No claims of clinical accuracy.
4. **Reliability** — a real job queue, object storage, key rotation, monitoring, backups,
   and a pilot with consenting users before any wider launch.

### 0.1 Assumptions I made (change any of these and the plan adjusts)

| # | Assumption |
|---|-----------|
| A1 | Phases 1–3 pass `PHASE1-3_COMPLETE_CHECKLIST.md` before Phase 4 starts. |
| A2 | Market is still India. English + Hindi are live; Tamil/Telugu were deferred. |
| A3 | Hosting stays on low-cost tiers. Object storage is any S3-compatible service. |
| A4 | There is **no legal counsel yet**. Every compliance item below is marked "confirm with counsel". This document is engineering guidance, not legal advice. |
| A5 | One developer plus an AI IDE, so scope is split into Must / Should / Could. |
| A6 | A pilot with 20–50 consenting users (friends, family, volunteers) is possible. |

### 0.2 Priority

| Feature | Priority | Tier gate |
|---------|----------|-----------|
| F1 Consent & Privacy Center | **Must** | All |
| F2 Data export & erasure | **Must** | All |
| F3 Guardian consent for child profiles | **Must** | All |
| F4 Job queue, object storage, key rotation | **Must** | n/a (infra) |
| F6 OCR quality loop | **Must** | All |
| F7 Smart reference ranges & units | **Must** | All |
| F12 Account security | **Must** | All |
| F13 Observability, backups, load tests | **Must** | n/a (ops) |
| F14 Pilot & feedback loop | **Must** | n/a |
| F5 Ask Your Records | Should | PREMIUM+ |
| F9 Smart reminders & notifications | Should | Basic all; WhatsApp channel PRO |
| F10 Caregiver access | Should | PREMIUM (3), PRO (10) |
| F11 PWA, accessibility, Tamil/Telugu | Should | All |
| F8 Explainable risk + model governance | Should (explainability) / Could (retraining) | All |

### 0.3 Explicitly NOT in Phase 4

| Deferred | Why |
|----------|-----|
| Insurer "wellness score" integration | Discrimination and regulatory risk. Needs legal review first. |
| Population / anonymized insights | Needs k-anonymity or differential privacy plus legal review, and a much larger user base. |
| Federated learning | Research spike only. Not a build item at this scale. |
| Clinic / doctor-side portal (doctor accounts, e-prescriptions) | A separate product; candidate for Phase 5. |
| Native iOS/Android apps | Decide after the pilot. Evaluate a Capacitor wrapper around the PWA first. |
| Garmin / Mi Band, ABDM production onboarding | Depend on partner access. Track availability; don't stub as done. |

---

## 1. Start Gate

```
Do not start Phase 4 until all of these are true. Report each with evidence.

  [ ] PHASE1-3_COMPLETE_CHECKLIST.md: every 🔴 item verified; every 🟠 verified or
      deferred with a written reason
  [ ] SECURITY_AUDIT.md: all 🔴 items pass
  [ ] Restore of a database backup tested at least once
  [ ] At least 10 GB free disk; disk-usage alert configured
  [ ] A staging environment exists that mirrors production (Postgres, Redis, object store)
  [ ] /specs/ contains this file and every earlier spec

If any item fails, fix it first. Phase 4 adds load (queue, storage, encryption changes)
and must not be stacked on an unverified base.
```

---

## 2. Compliance Context (read before F1–F3)

> Engineering guidance only. **Confirm every legal point with a qualified lawyer before launch.**

**Correction to earlier documents.** `MASTER_OVERVIEW.md` says health data is classed as
"Sensitive Personal Data" under India's DPDP Act. Based on current legal summaries, the DPDP
Act treats all personal data uniformly and does not create a separate "sensitive" tier.
Health data still carries higher practical risk and should be protected accordingly, but
update that sentence in the overview so it isn't repeated in a pitch.

**What is known (as of the sources reviewed):**
- The Digital Personal Data Protection Rules, 2025 were notified on **13 November 2025**.
- Implementation is phased. Consent-manager provisions start about 12 months after
  notification. Most data-fiduciary duties (notice, consent, security safeguards, breach
  notification, erasure and retention, children's data) apply after **about 18 months,
  roughly mid-May 2027**. Confirm exact dates.
- Duties include: clear notice with ways to withdraw consent, exercise rights, and complain;
  reasonable security safeguards; breach notification to the Data Protection Board and affected
  people (a detailed report within 72 hours has been reported); erasure when consent is
  withdrawn unless law requires retention; and **verifiable parental consent** for processing
  the data of anyone under 18.
- Cross-border transfer rules exist. LLM, hosting, SMS and payment vendors may process data
  outside India. Check each vendor's data-processing terms and location.
- India's medical-device rules may apply to software that diagnoses or predicts disease.
  Risk scores and predictions must stay informational until you have regulatory advice.
  (Current applicability not verified here.)

**Practical rule for the whole phase:** treat the 18-month date as a deadline for being
compliant, not a start date. Build consent, erasure and breach handling now.

---

## 3. New Entities (OOP + tables)

Every entity keeps the established pattern: `__init__`, `validate()` raising a named
`ArogyaError` subclass, `to_dict()`, `from_dict()`, repository with ownership filters.

| Entity | Key attributes |
|--------|----------------|
| `PrivacyNoticeVersion` | version, language, text_hash, effective_at |
| `ConsentRecord` (append-only) | user_id, profile_id?, purpose (`CORE_SERVICE`, `AI_PROCESSING`, `WHATSAPP`, `WEARABLE_SYNC`, `ABDM_SYNC`, `DOCTOR_SHARING`, `RESEARCH_TRAINING`, `MARKETING`), granted, notice_version, recorded_at, method |
| `GuardianConsent` | profile_id, guardian_user_id, attested_at, method, notice_version, revoked_at |
| `DataExportJob` | user_id, profile_id?, format (`JSON`, `FHIR_BUNDLE`, `PDF_ZIP`), status, file_key, expires_at |
| `ErasureRequest` | user_id, scope (`PROFILE`, `ACCOUNT`), status, grace_until, completed_at |
| `AuditLogEntry` (append-only) | actor_type, actor_id, action, target_type, target_id, profile_id, request_id, ip_hash, occurred_at (no PHI content) |
| `JobRecord` | job_id, type, owner_user_id, profile_id?, status, attempts, last_error_code, created_at, finished_at |
| `StoredFileKey` | file_key, wrapped_data_key, nonce, kek_version, checksum, size |
| `RecordChunk` (vector store) | profile_id, record_id, chunk_type, report_date, text, embedding |
| `OCRCorrection` | param_id, original_value/unit, corrected_value/unit, field_confidence, created_at |
| `ReferenceRangeProfile` | param_name, sex?, age_min?, age_max?, ref_min, ref_max, unit, source |
| `ModelEvaluation` / `DriftReport` | model_id, metrics_json, data_source, psi_by_feature, computed_at |
| `NotificationPreference` | user_id, channels, quiet_hours, timezone (default `Asia/Kolkata`), per-type toggles |
| `PushSubscription` | user_id, endpoint, encrypted keys, user_agent, last_success_at |
| `ReminderDelivery` | reminder_id, scheduled_for, channel, status, attempts — unique (reminder_id, scheduled_for, channel) |
| `AdherenceLog` | reminder_id, scheduled_for, status (`TAKEN`, `SKIPPED`, `SNOOZED`, `MISSED`), logged_at |
| `CaregiverAccess` | patient_profile_id, caregiver_user_id?, invite_email, role (`VIEWER`, `CONTRIBUTOR`), scope[], invite_token_hash, accepted_at, expires_at, revoked_at |
| `EmailVerificationToken` / `PasswordResetToken` | user_id, token_hash, expires_at, used_at |
| `TotpSecret` / `RecoveryCode` | user_id, encrypted_secret, enabled_at / code_hash, used_at |
| `UserSession` | session_id, user_id, refresh_family_id, device_label, ip_hash, last_used_at, revoked_at |
| `FeedbackEntry` / `ProductEvent` | sanitized message, screen, category / event name, anonymized user hash, whitelisted props |

New columns on existing tables: `clinical_parameters` gets `ref_source`, `value_original`,
`unit_original`, `value_normalized`, `needs_review`, `field_confidence`; `family_profiles` gets
`sex`, `is_minor`; `health_records` gets `file_hash`, `stored_file_key`.

---

## 4. Feature Specifications

### F1 — Consent & Privacy Center (Must)

**Goal:** Specific, revocable, recorded consent for each purpose, plus a clear notice.

**Behavior**
- Notice in English and Hindi, versioned. Consent is **separate per purpose**, never pre-ticked,
  and as easy to withdraw as to give.
- First upload requires `AI_PROCESSING` consent, and the screen must say plainly that extracted
  text is sent to a third-party AI service to be processed.
- `RESEARCH_TRAINING` and `MARKETING` are optional and off by default. Research consent is never
  offered for child profiles.
- `require_consent(purpose)` dependency guards the features that need it (uploads, WhatsApp,
  wearable sync, ABDM sync, doctor sharing, research use).
- **Withdrawal** disables the dependent feature immediately, revokes related tokens (wearable,
  ABDM, WhatsApp session), and queues deletion of derived data where required.
- Consent ledger is append-only. A change adds a new row; nothing is edited.
- Grievance contact and complaint route shown in the notice and the app footer.

**Endpoints**
```
GET   /api/privacy/notice?lang=en|hi
GET   /api/privacy/consents                  current state per purpose
POST  /api/privacy/consents                  {purpose, granted, notice_version}
POST  /api/privacy/grievance                 {message}  (sanitized, rate-limited 5/day)
GET   /api/privacy/access-log                who accessed this profile and when (from audit log)
```

**Rules:** unknown `notice_version` → 422; withdrawing `CORE_SERVICE` routes to account erasure (F2).
**Exceptions:** `ConsentRequiredError` (403, `CONSENT_REQUIRED`), `InvalidConsentPurposeError`.
**UI:** Privacy Center page; consent step before first upload; per-feature "turn off" links.

### F2 — Data Export & Erasure (Must)

**Export**
- Formats: `JSON` (all data), `FHIR_BUNDLE` (portable clinical data), `PDF_ZIP` (reports + original documents).
- Re-authenticate (password, plus TOTP if enabled) before requesting.
- Runs as a queue job. Download only through an authenticated endpoint; link valid 24 hours, single use.
  No PHI is sent by email or chat. Rate limit 3 per day.

**Erasure**
- Scope: one family profile, or the whole account.
- 7-day grace period with a cancel option, then a job deletes: database rows, stored files in
  object storage, vector-store documents, Redis cache keys, wearable and ABDM tokens (revoked
  at the provider), WhatsApp sessions, API keys, doctor and caregiver access.
- Keep only what must be kept (for example payment records) and the PHI-free audit entries.
- Backups: state the backup retention window in the privacy notice; erased data ages out of
  backups within that window. Do not claim instant removal from backups.
- After completion, a verification step proves zero rows, zero files, zero vectors for the scope.

**Endpoints**
```
POST   /api/privacy/export                  {profile_id?, format}
GET    /api/privacy/export/{id}
GET    /api/privacy/export/{id}/download
POST   /api/privacy/erasure                 {scope, profile_id?}   (re-auth required)
DELETE /api/privacy/erasure/{id}            cancel during grace period
GET    /api/privacy/erasure/{id}
```
**Exceptions:** `ReauthenticationRequiredError`, `ExportExpiredError`, `ErasureNotCancellableError`, `ErasureVerificationFailedError`.

### F3 — Guardian Consent for Child Profiles (Must)

**Why:** `FamilyProfile` allows `CHILD`. The data protection rules require **verifiable parental
consent** for under-18s and restrict tracking, behavioral monitoring, and targeted advertising
aimed at children. Exemptions for some healthcare providers exist; assume ArogyaMitra does not
qualify unless counsel says otherwise.

**Behavior**
- Profile with `relation=CHILD` or DOB under 18 is flagged `is_minor` and needs a `GuardianConsent`
  before any upload.
- Verification sits behind a `GuardianVerifier` interface. Baseline implementation: account holder is
  an adult (self-declared adult DOB at registration), email verified (F12), and signs an attestation
  naming the child. A stronger implementation (for example a government digital-ID check) plugs in
  later. **Confirm with counsel what counts as "verifiable".**
- For minors: no marketing, no research use, no analytics events about the child, no WhatsApp bot
  linking, no wearable sync unless the guardian opts in per feature.
- A profile that turns 18 is flagged for review; ownership is never transferred automatically.
- Registration requires the user to confirm they are 18 or older.

**Endpoints**
```
POST   /api/family/{profile_id}/guardian-consent
DELETE /api/family/{profile_id}/guardian-consent      withdraw (stops processing, starts erasure flow)
```
**Exceptions:** `GuardianConsentRequiredError`, `MinorFeatureRestrictedError`.

### F4 — Job Queue, Object Storage, Key Rotation (Must)

**Job queue**
- Replace `asyncio.create_task` with a Redis-backed queue (**ARQ** recommended, async-native; Celery or RQ acceptable).
- Separate worker process. OCR is CPU-heavy: limit worker concurrency and set per-job timeouts.
- Jobs: `process_record`, `generate_report`, `wearable_sync`, `prediction_rerun`, `export`, `erasure`,
  `notification_delivery`, `embed_record`, `retrain_eval`.
- Idempotency key per job; retries with exponential backoff (max 3); permanent failures logged to a dead-letter list;
  `JobRecord` tracks state. Restarting the worker must not lose or duplicate work.
- Upload returns `202 {record_id, job_id}`; the UI polls `GET /api/jobs/{id}` (owner-scoped).

**Object storage (`FileStore` strategy)**
- `LocalFileStore` for development, `S3FileStore` for production. Keys: `profiles/{profile_id}/records/{record_id}.enc`.
- Bucket is private. PHI is streamed through the API (no public or long-lived presigned URLs).
- Migration: copy existing local files, verify checksums, then delete local copies.

**Envelope encryption and rotation**
- Each file gets a random data key. Encrypt the file with AES-256-GCM, then **wrap** the data key with a master key
  identified by `kek_version`. Store wrapped key, nonce, version, checksum in `StoredFileKey`.
- Rotation: add a new master-key version, run a job that **re-wraps** data keys (files are not re-encrypted), keep the old
  version until every key is re-wrapped. Third-party tokens (ABDM, wearable) use the same service.
- Master key comes from the secrets manager or environment; use a KMS if your host offers one.

**Resilience for Groq calls:** retries with jitter, a circuit breaker (open for 60 s after repeated failures), and the
specified rule-based fallbacks.

**Exceptions:** `JobNotFoundError`, `StorageWriteError`, `KeyVersionNotFoundError`, `CircuitOpenError`.

### F5 — Ask Your Records (Should, PREMIUM+)

**Goal:** Answer questions about the user's **own** records, with citations, and refuse everything else.

**Design**
- After ingestion, an `embed_record` job stores `RecordChunk`s (structured parameters, medications, notes, document text)
  with `profile_id` metadata.
- Access goes through a `ProfileScopedVectorStore` wrapper that **cannot be called without a profile_id** and always filters on
  it. The profile comes from the verified session, never from the client request body.
- Retrieval top-k = 6. If the best similarity is below a threshold, answer "I couldn't find that in your records."
- Retrieved text is **untrusted data**: placed in delimited blocks, with a system prompt that says never to follow instructions
  found inside it.
- **Numeric grounding check:** every number in the answer must appear in the retrieved chunks, otherwise retry once, then refuse.
- Refuse diagnosis, dosing, and treatment advice. Output goes through `apply_output_guardrails()`. Disclaimer attached.
- Stateless in Phase 4 (client keeps the last few turns). No server-side chat history unless the user opts in.
- Chunks are deleted with their record and during erasure.

**Endpoint:** `POST /api/ask` `{question}` → `{answer, citations:[{record_id, date, param?}], disclaimer}`.
Rate limit 30/hour; requires `AI_PROCESSING` consent and PREMIUM+.

**Evaluation set (build before shipping):** 30+ questions including 10 unanswerable and 5 prompt-injection attempts.
Proposed targets: at least 90% correct on answerable questions, 100% refusal on unanswerable ones, 0 injection successes.

### F6 — OCR Quality Loop (Must)

- Record a per-field confidence (OCR confidence combined with name-match quality). Fields under a threshold
  (start at 0.80, tune on data) set `needs_review=true`.
- **Review screen:** original document page (decrypted stream) next to the extracted fields. The user edits or confirms;
  edits save an `OCRCorrection`.
- Plausibility bounds per parameter (a clinician-reviewed table) flag impossible values (for example HbA1c of 90).
- **Duplicate detection:** file hash plus parameter and date match, so a report uploaded twice is not counted twice in trends.
- **Golden set:** a folder of documents (your own, synthetic, or consented) with expected values. `eval_ocr.py` reports field-level
  precision and recall per parameter; CI fails if accuracy drops by more than 2 points.
- Corrections are used for evaluation only, unless the user has granted `RESEARCH_TRAINING`.
- Endpoints: `GET /api/records/{id}/review`, `PUT /api/params/{id}` (existing, now marks `needs_review=false`),
  `POST /api/records/{id}/confirm`.

### F7 — Smart Reference Ranges & Units (Must)

- **Report-specific ranges:** capture the range printed on each report; `ref_source` is `REPORT`, `DEFAULT`, or `DERIVED`.
  Status uses the report's own range when present.
- **Sex- and age-aware defaults** (for example hemoglobin by sex). Profiles gain optional `sex` and DOB; when missing, defaults are
  used and clearly labeled.
- **eGFR:** if not printed and creatinine, age, and sex are known, compute with the published CKD-EPI 2021 equation, label it
  `DERIVED`, and unit-test it against published reference values.
- **Unit normalization:** store the original value and unit plus a normalized value in canonical units. Unknown units set
  `needs_review` instead of guessing.

| Parameter | Canonical | Conversion to canonical |
|-----------|-----------|--------------------------|
| Glucose | mg/dL | mmol/L × 18.016 |
| Total cholesterol, LDL, HDL | mg/dL | mmol/L × 38.67 |
| Triglycerides | mg/dL | mmol/L × 88.57 |
| Creatinine | mg/dL | µmol/L ÷ 88.4 |
| Uric acid | mg/dL | µmol/L ÷ 59.48 |
| Vitamin D | ng/mL | nmol/L ÷ 2.496 |
| Vitamin B12 | pg/mL | pmol/L ÷ 0.738 |
| Hemoglobin | g/dL | g/L ÷ 10 |
| HbA1c | % (NGSP) | mmol/mol: % = mmol/mol ÷ 10.929 + 2.15 |

*Verify every factor against a clinical reference before shipping, and unit-test round trips.*

### F8 — Explainable Risk & Model Governance (Should; retraining Could)

- **Explainability:** show the top contributing parameters behind each score ("why this score"). Rule-based scores already list
  contributions; for the Random Forest use per-prediction attributions (for example SHAP).
- **Model card** generated for every model version: training data (synthetic or real), per-class metrics, limitations, intended use,
  "informational, not clinical."
- **Registry:** `MLRiskModel` gains `status` (`SHADOW`, `ACTIVE`, `RETIRED`), `data_source`, `metrics_json`. A new model runs in
  **shadow mode** alongside the active one; an admin promotes it manually. No auto-promotion.
- **Drift:** weekly population stability index per feature against the training distribution; alert when it exceeds a threshold
  (0.2 is a common starting point); log class-distribution shift.
- **Retraining (only after the pilot):** only from users with `RESEARCH_TRAINING` consent, never children; de-identified (no names,
  dates shifted to relative offsets, IDs hashed with a rotating salt). **Be honest about labels:** there is no outcome ground truth.
  Training on the rule engine's labels only teaches the model to imitate the rules. Require a clinician-labeled evaluation set
  before claiming any improvement.
- UI copy: "an estimate based on the values you uploaded," never "diagnosis."

### F9 — Smart Reminders & Notifications (Should)

- **Channels:** Web Push (VAPID keys), WhatsApp (PRO), email. Preferences per user: channels, quiet hours, timezone
  (default `Asia/Kolkata`), per-type toggles.
- **Delivery:** a single-run scheduler (dedicated process or Redis lock) enqueues `ReminderDelivery` rows; the unique key
  (reminder_id, scheduled_for, channel) makes delivery idempotent. Use timezone-aware recurrence.
- **Quiet hours** defer non-urgent reminders; urgent ones (for example low SpO₂) bypass them.
- **Privacy:** notification text is generic by default ("Medication reminder"); showing the drug name is an opt-in.
- **Adherence:** `TAKEN`, `SKIPPED`, `SNOOZED` (10/30/60 min), and `MISSED` after a grace window. 7- and 30-day summaries; optional
  line in the Doctor-Prep report.
- **Refill reminders** only when quantity and dosage were extracted; otherwise skipped.
- **Platform rules to verify:** WhatsApp business-initiated messages generally need pre-approved templates outside the 24-hour
  customer window. iOS web push works only for an installed PWA (Safari 16.4+).
- Endpoints: `GET/PUT /api/notifications/preferences`, `POST /api/notifications/push/subscribe`,
  `DELETE /api/notifications/push/subscribe/{id}`, `POST /api/reminders/{id}/log`, `POST /api/reminders/{id}/snooze`,
  `GET /api/adherence?days=30`.

### F10 — Caregiver Access (Should)

- Lets another **ArogyaMitra account holder** (for example a sibling) view or contribute to a profile. Different from the doctor
  link, which is token-based and read-only.
- Invite by email with a single-use token (stored hashed); the invitee must sign in or register and **accept**. Roles: `VIEWER`,
  `CONTRIBUTOR`. Optional scopes and expiry. Limits: PREMIUM 3, PRO 10.
- **Central `ProfileAccessPolicy.can(user, profile, action)`** replaces ownership checks scattered across repositories.
  Owner: full access. Caregiver: per role and scope. Export, erasure, billing, and caregiver management stay **owner-only**.
- Every caregiver access writes an audit entry; the owner can view and revoke at any time.
- This touches every repository. Test a full matrix: {owner, viewer, contributor, outsider} × {read, write, delete, share,
  export, erase} for each profile-scoped resource.
- Endpoints: `POST /api/family/{profile_id}/caregivers`, `GET /api/family/{profile_id}/caregivers`,
  `POST /api/caregivers/accept` `{token}`, `DELETE /api/family/{profile_id}/caregivers/{id}`.

### F11 — PWA, Accessibility, Tamil & Telugu (Should)

- **PWA:** manifest, icons, service worker (vite-plugin-pwa/Workbox). Precache the app shell only. **API responses containing
  health data are not cached** by the service worker (`NetworkOnly` for `/api`). Offline page and install prompt.
  Optional offline reading would need an encrypted local store; treat it as a stretch goal with its own security review.
- **Accessibility:** WCAG 2.1 AA target. `axe-core` in CI plus a manual screen-reader pass. Large-text mode (125–150%),
  high-contrast mode, a simplified navigation mode for older users, and read-aloud of summaries via the browser's speech synthesis.
- **Languages:** Tamil and Telugu for the UI and OCR, with medical terms reviewed by a person fluent in the language, not
  machine translation alone. Missing keys fall back to English.
- **Performance budgets (proposed):** Lighthouse CI on a mid-range Android profile over 4G; initial JS bundle under 250 KB gzipped;
  largest contentful paint under 2.5 s.
- Native app decision deferred to after the pilot.

### F12 — Account Security (Must)

- **Email verification:** hashed single-use token, 24 h expiry. Required before export, erasure, share links, doctor or caregiver
  access, and payments.
- **Password reset:** hashed single-use token, 30 min expiry, same response whether or not the email exists, rate limit 3/hour
  per email and IP, **revokes all sessions** on success.
- **Email delivery:** provider adapter (mock in development). Configure SPF, DKIM, and DMARC for the sender domain.
- **TOTP MFA:** enrollment with QR code, secret encrypted at rest, 10 single-use recovery codes stored hashed. Mandatory for admins,
  optional for users. Re-authentication required for export, erasure, and MFA changes.
- **Sessions:** `UserSession` per login. **Refresh-token rotation** with reuse detection: using an old refresh token revokes the
  whole token family. Users can list and revoke sessions. New-device login sends an email alert.
- Password change requires the current password. Optional breached-password check using the k-anonymity range API.
- Endpoints: `POST /api/auth/verify-email`, `POST /api/auth/resend-verification`, `POST /api/auth/forgot-password`,
  `POST /api/auth/reset-password`, `POST /api/auth/mfa/enroll`, `POST /api/auth/mfa/verify`, `POST /api/auth/mfa/disable`,
  `GET /api/auth/sessions`, `DELETE /api/auth/sessions/{id}`, `POST /api/auth/change-password`.
- **Exceptions:** `EmailNotVerifiedError`, `ResetTokenInvalidError`, `MfaRequiredError`, `MfaCodeInvalidError`,
  `SessionRevokedError`, `RefreshReuseDetectedError`.

### F13 — Observability, Backups, Load Testing (Must)

- **Errors:** Sentry or equivalent with PII off: `send_default_pii=False`, a `before_send` hook that strips request bodies, auth
  headers, emails, and anything resembling a token.
- **Metrics:** Prometheus endpoint `/metrics`, **internal only** (IP allow-list or auth). Track HTTP latency and status, queue depth and
  oldest job age, job failures, LLM latency, error rate and tokens, OCR duration, cache hit ratio, DB pool usage.
- **Alerts (proposed starting thresholds):** 5xx over 2% for 5 min; p95 latency over 1.5 s; oldest queued job over 5 min; LLM error rate
  over 10%; disk over 80%; DB connections over 80%; backup failure; TLS certificate under 14 days.
- **Audit log:** append-only `AuditLogEntry` for record view/download, export, share creation and access, doctor and caregiver access,
  admin actions, API-key reads. No PHI content in entries. Users can read their own profile's access history (F1).
- **Backups:** nightly encrypted `pg_dump` stored off the primary platform, plus point-in-time recovery if your plan supports it
  (free tiers often don't, so verify). Object-storage versioning. Retention 30 days. **Monthly restore drill.** Proposed targets:
  recovery point 24 h, recovery time 4 h.
- **Load test (k6 or Locust):** login, upload, list, report. Proposed target: 50 concurrent users with p95 under 1.5 s on read endpoints.
  Fix what the test finds (indexes, N+1 queries, pool size).
- **Runbooks:** incident response, **personal-data breach** (who decides, how affected users and the regulator are notified within the
  required window), restore, key rotation, leaked-secret rotation.

### F14 — Pilot & Feedback Loop (Must)

- **Pilot:** 20–50 consenting users for 4 weeks, with a written consent and clear "this is a pilot, not medical advice" wording.
- **Feedback:** in-app widget (`FeedbackEntry`, sanitized text). Optional contact consent.
- **Product events:** an events table with a whitelist of event names and properties. **No PHI, no third-party trackers by default.**
  Analytics are opt-in and never collected for minors.
- **Metrics:** activation (first successful extraction within 10 min), % of extracted fields edited by users, reports generated per active
  user, weekly retention, p95 upload-to-ready time (proposed under 60 s), crash-free sessions, open support issues.
- **Go / no-go review** after the pilot decides: public launch, retraining work (F8), native app, clinic portal (Phase 5).

---

## 5. Stack Additions

Pin the current stable version when you add each package, then run `pip-audit` / `npm audit`.

| Need | Package or service |
|------|--------------------|
| Job queue | `arq` (or Celery/RQ) |
| Object storage | `boto3` / `aioboto3` + any S3-compatible store (verify free-tier limits) |
| Web Push | `pywebpush` (VAPID keys in secrets) |
| TOTP | `pyotp`, `qrcode` |
| Retries / circuit breaker | `tenacity` (+ small breaker helper) |
| Explainability | `shap` (optional) |
| Errors / metrics | `sentry-sdk`, `prometheus-client` (OpenTelemetry optional) |
| Email | provider SDK or SMTP library, behind an adapter |
| PWA | `vite-plugin-pwa`, Workbox |
| Accessibility / performance CI | `axe-core`, Lighthouse CI |
| Load testing | k6 or Locust |

**New environment variables:** `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `KEK_VERSION`, `KEK_CURRENT`,
`KEK_PREVIOUS` (during rotation), `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `EMAIL_PROVIDER`, `EMAIL_API_KEY`, `SENTRY_DSN`,
`METRICS_ALLOWED_IPS`, `QUEUE_CONCURRENCY`, `EXPORT_TTL_HOURS`, `ERASURE_GRACE_DAYS`.
Add every one to `.env.example` (placeholders only) and to startup validation.

---

## 6. New Exceptions

```
Consent / privacy : ConsentRequiredError, InvalidConsentPurposeError,
                    ReauthenticationRequiredError, ExportExpiredError,
                    ErasureNotCancellableError, ErasureVerificationFailedError
Minors            : GuardianConsentRequiredError, MinorFeatureRestrictedError
Infra             : JobNotFoundError, StorageWriteError, KeyVersionNotFoundError, CircuitOpenError
Account security  : EmailNotVerifiedError, ResetTokenInvalidError, MfaRequiredError,
                    MfaCodeInvalidError, SessionRevokedError, RefreshReuseDetectedError
Data quality      : ImplausibleValueError, UnknownUnitError, DuplicateRecordError
Ask-records       : NoGroundedAnswerError, NumericGroundingFailedError
Caregiver         : CaregiverInviteInvalidError, AccessPolicyDeniedError
```
All inherit `ArogyaError` with `status_code` and `error_code`; policy denials return 404 where revealing existence would leak data.

---

## 7. Build Order (follow exactly; verify and report after each step)

```
Step 0  Start gate (Section 1). Basic Sentry + metrics wired now so every later step is observable.
Step 1  F4  Job queue + FileStore + envelope encryption + key rotation
        Verify: kill the worker mid-job and restart; no lost or duplicated work. Files migrated with checksums.
Step 2  F12 Account security (sessions, refresh rotation, email verification, reset, MFA)
        Verify: reuse of an old refresh token revokes the family; reset revokes all sessions.
Step 3  F1  Consent & privacy center + audit log
        Verify: withdrawing a consent actually stops the dependent feature and revokes tokens.
Step 4  F2  Export & erasure, then F3 guardian consent
        Verify: erasure leaves zero rows, files, vectors, cache keys for the scope.
Step 5  F6  OCR quality loop, then F7 ranges & units
        Verify: golden-set accuracy report; unit round-trip tests; derived eGFR matches published values.
Step 6  F5  Ask Your Records
        Verify: evaluation set; cross-profile retrieval attempts return nothing.
Step 7  F9  Notifications & adherence
        Verify: two scheduler instances still deliver once; quiet hours respected.
Step 8  F10 Caregiver access + ProfileAccessPolicy refactor
        Verify: the full access matrix passes for every profile-scoped resource.
Step 9  F8  Explainability, registry, shadow mode, drift (retraining only after the pilot)
Step 10 F11 PWA, accessibility, Tamil/Telugu
Step 11 F13 Alerts, backups and restore drill, load test, runbooks
Step 12 F14 Pilot → review → decide Phase 5
```

---

## 8. Paste-Ready Prompt for the AI IDE

**BEGIN MESSAGE**

Implement Phase 4 of ArogyaMitra AI following `/specs/PHASE4_IMPLEMENTATION.md`. Stack is unchanged
(FastAPI, async SQLAlchemy, PostgreSQL, Redis, LangGraph, Groq, ChromaDB, React/Vite/Tailwind).

**Rules**
1. First report the start gate (spec Section 1) with evidence. If it fails, stop and fix it.
2. Follow the build order in Section 7. Do not run steps in parallel. After each step, run its "Verify" item and paste real
   command output, not a summary. Mark a checklist item done only after testing it.
3. Keep every established rule: dependency injection through `Depends()` in `dependencies.py` (no service locator), ownership filters
   on every query, `sanitize_for_prompt()` and `apply_output_guardrails()` around every LLM call, PHI-free logs, rate limits,
   encrypted third-party tokens, no secrets in the frontend, no API key in the web client.
4. Every schema change is an Alembic revision with a tested downgrade. Migrations run as a release step, not on app boot.
5. Use adapters with mock implementations for email, push, WhatsApp, and object storage. Report which real services are available.
6. For any legal or regulatory statement, add a `TODO(counsel)` note. Do not claim compliance.
7. Do not write scratch files, `.bat` scripts, or logs into the repo. Print results to the terminal and record evidence in
   `VERIFICATION_LOG.md`.
8. Check disk space before large installs and after test runs. Stop and report if free space drops below 5 GB.
9. Create `task.md` from the build order. Update `PHASE1-3_COMPLETE_CHECKLIST.md` and the Phase 4 checklist honestly with
   `[x]`, `[~]`, `[!]`, `[ ]`.
10. Retraining of the risk model is **out of scope until the pilot ends**. Implement explainability, registry, shadow mode, and drift only.

**END MESSAGE**

---

## 9. Phase 4 Acceptance Checklist

Marks: `[x]` verified with evidence, `[~]` partial, `[!]` broken, `[ ]` not done.

### 9.1 Platform (F4)
- [ ] **P4-01** 🔴 Records are processed by a worker via the queue; no `asyncio.create_task` pipeline remains
- [ ] **P4-02** 🔴 Killing the worker mid-job and restarting loses and duplicates nothing (idempotency verified)
- [ ] **P4-03** 🟠 Retries use backoff (max 3); permanent failures land in a dead-letter list; `GET /api/jobs/{id}` is owner-scoped
- [ ] **P4-04** 🔴 Files live in object storage via `FileStore`; bucket is private; no public or long-lived presigned URLs for PHI
- [ ] **P4-05** 🔴 Each file has its own data key wrapped by a versioned master key; wrapped key, nonce, version, checksum stored
- [ ] **P4-06** 🔴 Key rotation re-wraps all data keys without re-encrypting files; old version kept until complete; tested end to end
- [ ] **P4-07** 🟠 Existing local files migrated with verified checksums; local copies removed afterward
- [ ] **P4-08** 🟠 Groq calls have retries with jitter and a circuit breaker; fallback paths work when the circuit is open

### 9.2 Account security (F12)
- [ ] **P4-09** 🔴 Email verification gates export, erasure, share links, doctor/caregiver access, payments
- [ ] **P4-10** 🔴 Password reset: single-use hashed token, 30 min expiry, identical response for unknown emails, rate-limited, revokes all sessions
- [ ] **P4-11** 🔴 Refresh tokens rotate; reuse of an old token revokes the whole family
- [ ] **P4-12** 🟠 Users can list and revoke sessions; new-device login emails an alert
- [ ] **P4-13** 🟠 TOTP enrollment, verification, recovery codes (hashed, single-use); admins must have MFA
- [ ] **P4-14** 🟠 Re-authentication required for export, erasure, and MFA changes
- [ ] **P4-15** 🟡 SPF/DKIM/DMARC configured for the sender domain; password change needs the current password

### 9.3 Consent, privacy, children (F1–F3)
- [ ] **P4-16** 🔴 Notice available in English and Hindi, versioned; consent is per purpose, never pre-ticked
- [ ] **P4-17** 🔴 First upload requires `AI_PROCESSING` consent with a plain statement that text goes to a third-party AI service
- [ ] **P4-18** 🔴 Consent ledger is append-only; withdrawal stops the dependent feature and revokes related tokens
- [ ] **P4-19** 🟠 `require_consent()` guards uploads, WhatsApp, wearable sync, ABDM sync, doctor sharing, research use
- [ ] **P4-20** 🟠 Grievance route and contact are visible; access history for a profile is viewable by its owner
- [ ] **P4-21** 🔴 Export (JSON, FHIR bundle, PDF zip) runs as a job; re-auth required; download link single-use and expires in 24 h
- [ ] **P4-22** 🔴 Erasure has a 7-day cancellable grace period, then removes rows, files, vectors, cache keys, third-party tokens, sessions, API keys, shared access
- [ ] **P4-23** 🔴 Post-erasure verification proves zero rows, files, and vectors for the scope
- [ ] **P4-24** 🟠 Privacy notice states the backup retention window; no claim of instant removal from backups
- [ ] **P4-25** 🔴 Minor profiles (CHILD or DOB under 18) require guardian consent before any upload
- [ ] **P4-26** 🔴 Minors have no marketing, research use, analytics events, or WhatsApp linking
- [ ] **P4-27** 🟠 `GuardianVerifier` is an interface with a baseline implementation; registration requires an 18+ confirmation
- [ ] **P4-28** 🟡 Profile turning 18 is flagged for review, never auto-transferred
- [ ] **P4-29** 🟡 Every compliance statement carries a `TODO(counsel)` note; `MASTER_OVERVIEW.md` "sensitive personal data" wording corrected

### 9.4 Data quality (F6, F7)
- [ ] **P4-30** 🟠 Per-field confidence stored; low-confidence fields set `needs_review`
- [ ] **P4-31** 🟠 Review screen shows the original page beside extracted fields; edits saved as `OCRCorrection`
- [ ] **P4-32** 🟠 Plausibility bounds flag impossible values; duplicate uploads detected by file hash and parameter/date
- [ ] **P4-33** 🟠 Golden set and `eval_ocr.py` report field-level precision and recall; CI fails on a drop over 2 points
- [ ] **P4-34** 🟠 Report-specific reference ranges captured; `ref_source` recorded; status uses the report range when present
- [ ] **P4-35** 🟠 Sex- and age-aware defaults applied; missing data is labeled, not silently defaulted
- [ ] **P4-36** 🟠 Derived eGFR (CKD-EPI 2021) labeled `DERIVED` and unit-tested against published values
- [ ] **P4-37** 🟠 Unit normalization stores original and normalized values; unknown units set `needs_review`; conversion factors verified against a clinical reference; round-trip tests pass
- [ ] **P4-38** 🟡 Timeline plots normalized values and shows the original unit

### 9.5 Intelligence (F5, F8)
- [ ] **P4-39** 🔴 `ProfileScopedVectorStore` cannot be used without a profile ID taken from the verified session; cross-profile retrieval returns nothing
- [ ] **P4-40** 🔴 Retrieved text is treated as untrusted data; injection attempts inside documents do not change behavior
- [ ] **P4-41** 🔴 Numeric grounding check enforced; unanswerable questions return "couldn't find that in your records"
- [ ] **P4-42** 🟠 Answers carry citations and the informational disclaimer; diagnosis, dosing, and treatment requests are refused
- [ ] **P4-43** 🟠 Evaluation set (30+ questions incl. 10 unanswerable, 5 injection) meets the targets and results are recorded
- [ ] **P4-44** 🟠 Chunks are removed with their record and during erasure; `ask` limited to 30/hour and PREMIUM+
- [ ] **P4-45** 🟠 "Why this score" explanation shown for risk results; model card generated per model version
- [ ] **P4-46** 🟠 Shadow mode runs a candidate model beside the active one; promotion is manual
- [ ] **P4-47** 🟡 Weekly drift report (PSI per feature) stored; alert on threshold
- [ ] **P4-48** 🟡 No retraining code path runs before the pilot ends; UI says "estimate", never "diagnosis"

### 9.6 Notifications & caregivers (F9, F10)
- [ ] **P4-49** 🟠 Preferences, quiet hours, timezone honored; urgent reminders bypass quiet hours
- [ ] **P4-50** 🔴 Two scheduler instances deliver each reminder once (unique key + lock verified)
- [ ] **P4-51** 🟠 Notification text is generic by default; drug names shown only with opt-in
- [ ] **P4-52** 🟠 Adherence logging, snooze (10/30/60 min), missed detection, 7/30-day summaries
- [ ] **P4-53** 🟡 WhatsApp template and push-platform requirements checked and recorded
- [ ] **P4-54** 🔴 `ProfileAccessPolicy` is the single access decision point; no scattered ownership checks remain
- [ ] **P4-55** 🔴 Access matrix {owner, viewer, contributor, outsider} × {read, write, delete, share, export, erase} passes for every profile-scoped resource
- [ ] **P4-56** 🔴 Export, erasure, billing, and caregiver management are owner-only
- [ ] **P4-57** 🟠 Caregiver invite token single-use and hashed; acceptance required; revoke works immediately; every caregiver access is audit-logged
- [ ] **P4-58** 🟡 Caregiver limits enforced by tier (PREMIUM 3, PRO 10, FREE 0)

### 9.7 Reach (F11)
- [ ] **P4-59** 🟠 App installs as a PWA; service worker caches the shell only and never health-data API responses
- [ ] **P4-60** 🟠 `axe-core` has no serious violations; manual screen-reader pass done; large-text and high-contrast modes work
- [ ] **P4-61** 🟡 Lighthouse CI budgets met on a mid-range Android profile; initial JS bundle under budget
- [ ] **P4-62** 🟡 Tamil and Telugu UI and OCR shipped with human-reviewed medical terms, or recorded as not started

### 9.8 Operations & pilot (F13, F14)
- [ ] **P4-63** 🔴 Sentry runs with PII off and a `before_send` scrubber (verified by sending a test error containing an email and token)
- [ ] **P4-64** 🔴 `/metrics` is not publicly reachable; key metrics and alerts configured
- [ ] **P4-65** 🔴 Nightly encrypted backup runs off-platform and a **restore drill was completed and timed**
- [ ] **P4-66** 🟠 Audit log is append-only, PHI-free, and covers record access, exports, shares, doctor/caregiver access, admin actions
- [ ] **P4-67** 🟠 Load test results recorded; bottlenecks fixed (indexes, N+1, pool size)
- [ ] **P4-68** 🟠 Runbooks written: incident, personal-data breach, restore, key rotation, leaked secret
- [ ] **P4-69** 🟠 Pilot ran with written consent; feedback widget and PHI-free events live; metrics collected
- [ ] **P4-70** 🟡 Go/no-go review written and Phase 5 candidates ranked

### 9.9 Regression
- [ ] **P4-71** 🔴 `PHASE1-3_COMPLETE_CHECKLIST.md` still passes after all Phase 4 changes
- [ ] **P4-72** 🔴 `SECURITY_AUDIT.md` re-run; all 🔴 items pass
- [ ] **P4-73** 🟠 Coverage stays ≈80% overall, with 100% of branches in access policy, consent gates, erasure, and token handling

---

## 10. Exit Criteria for Phase 4

Phase 4 is complete when:
1. Every 🔴 item above is `[x]` with evidence in `VERIFICATION_LOG.md`.
2. Every 🟠 item is `[x]` or has a written reason for deferral.
3. The pilot has run and its go/no-go review is written.
4. Section 2's compliance points have been reviewed by counsel, or are listed as open risks with an owner and date.
5. Phase 1–3 and security checklists still pass.

---

*End of PHASE4_IMPLEMENTATION.md*
