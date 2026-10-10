# ArogyaMitra AI — Phase 3 Advanced Features Specification
> Version: Phase 3 (Platform Scale)
> Prerequisite: Phase 1 (156 checkpoints) + Phase 2 (189 checkpoints) fully passing
> Target: AI IDE Code Generation Ready — context + prompt instructions
> Author: ArogyaMitra Dev

---

## 1. Phase 3 Overview

Phase 3 transforms ArogyaMitra from a single-user personal intelligence tool into a **collaborative health platform** serving patients, families, and (optionally) healthcare providers. It introduces 10 advanced features — each one addressing a gap that no existing Indian or foreign competitor has solved simultaneously.

| Feature | Category | Core Unlock |
|---------|----------|-------------|
| Predictive Health Timeline | Advanced ML | Trajectory forecasting — "18 months from threshold" |
| Family Health Profiles | Platform | Multi-member management under one account |
| ABDM / FHIR Integration | Infrastructure | Pull records from India's national health ID network |
| Multilingual OCR + UI | Accessibility | Hindi, Tamil, Telugu OCR + localized interface |
| Doctor-Patient Shared Workspace | Collaboration | Role-based shared view of patient health timeline |
| WhatsApp Health Bot | Distribution | Access ArogyaMitra intelligence via WhatsApp |
| Wearable Passive Monitoring | Data Sources | Fitbit, Mi Band, Garmin → automatic vitals logging |
| Subscription & Monetization | Business | Freemium → Premium → Pro tiers |
| Health Score API | B2B | Expose ArogyaMitra intelligence as a REST API |
| Voice-First Input | UX | Speak symptoms / medicines → AI structures them |

---

## 2. New & Upgraded OOP Entities

---

### 2.1 `FamilyProfile` Class (NEW)

```
Class: FamilyProfile
Responsibility: Groups multiple health members under one account owner.
One User can manage multiple FamilyProfile members.

Attributes:
  - profile_id: str (UUID4)
  - owner_user_id: str (FK → User — the account holder)
  - member_name: str (e.g. "Dad", "Mom", "Riya")
  - relation: Enum["SELF", "SPOUSE", "PARENT", "CHILD", "SIBLING", "OTHER"]
  - date_of_birth: Optional[date]
  - gender: Optional[Enum["MALE", "FEMALE", "OTHER"]]
  - abha_id: Optional[str] (Ayushman Bharat Health Account ID — 14-digit)
  - is_primary: bool (True for the owner's own profile — auto-created on registration)
  - created_at: datetime
  - is_active: bool

All HealthRecord, ClinicalParameter, RiskScore, Reminder, DoctorReport
objects carry profile_id instead of (or in addition to) user_id.
This allows per-member data isolation under one account.

Methods:
  - validate(): member_name min 2 chars, relation must be valid Enum,
    abha_id if provided must be exactly 14 digits, date_of_birth must be in past
  - compute_age() -> Optional[int]
  - to_dict() / from_dict()
```

**CRUD Operations for FamilyProfile:**
| Operation | Endpoint | Description |
|-----------|----------|-------------|
| CREATE | `POST /api/family/` | Add a new family member |
| READ ALL | `GET /api/family/` | List all members for current user |
| READ | `GET /api/family/{profile_id}` | Get single member profile |
| UPDATE | `PUT /api/family/{profile_id}` | Edit name, DOB, relation, abha_id |
| DELETE | `DELETE /api/family/{profile_id}` | Soft deactivate — cannot delete SELF profile |
| SWITCH | `POST /api/family/{profile_id}/activate` | Set active context to this member |

**Validation Rules:**
- Owner always has exactly one `is_primary=True` SELF profile — auto-created at registration
- Cannot delete or deactivate the SELF (primary) profile — raise `CannotDeletePrimaryProfileError`
- Maximum 10 members per account — raise `FamilyMemberLimitError`
- `abha_id` must be exactly 14 numeric digits if provided — raise `InvalidABHAIDError`
- All subsequent data endpoints (records, params, risk, reminders, report) must accept an optional
  `?profile_id=` query param — default to SELF if omitted

---

### 2.2 `WearableReading` Class (NEW)

```
Class: WearableReading
Responsibility: Stores a single passive vitals reading from a connected wearable device.

Attributes:
  - reading_id: str (UUID4)
  - profile_id: str (FK → FamilyProfile)
  - source: Enum["FITBIT", "MI_BAND", "GARMIN", "SAMSUNG_HEALTH", "MANUAL"]
  - metric_type: Enum["HEART_RATE", "STEPS", "SLEEP_HOURS", "BLOOD_OXYGEN", "WEIGHT", "STRESS_SCORE"]
  - value: float
  - unit: str
  - recorded_at: datetime (when the wearable captured this)
  - synced_at: datetime (when ArogyaMitra received it)
  - raw_payload: Optional[str] (JSON string of the original API response — for debugging)

Methods:
  - validate(): value must be positive float, metric_type must be valid Enum,
    recorded_at must not be in future
  - to_dict() / from_dict()
  - to_clinical_param() -> Optional[ClinicalParameter]: converts HEART_RATE/BLOOD_OXYGEN
    to ClinicalParameter format for trend tracking (other metrics stay as WearableReading only)
```

**CRUD for WearableReading:**
| Operation | Endpoint | Description |
|-----------|----------|-------------|
| CREATE (bulk) | `POST /api/wearables/sync` | Ingest batch of readings from wearable OAuth callback |
| READ | `GET /api/wearables/?metric_type=HEART_RATE` | Filtered reading history |
| DELETE | `DELETE /api/wearables/{reading_id}` | Remove a single reading |
| CONNECT | `POST /api/wearables/connect/{source}` | Initiate OAuth flow for a wearable |
| DISCONNECT | `DELETE /api/wearables/connect/{source}` | Revoke wearable OAuth token |

---

### 2.3 `PredictionResult` Class (NEW)

```
Class: PredictionResult
Responsibility: Stores an ML trajectory forecast for a clinical parameter —
                "at current rate, you will cross threshold X in Y months"

Attributes:
  - prediction_id: str (UUID4)
  - profile_id: str
  - param_name: str
  - computed_at: datetime
  - current_value: float
  - current_trend: Enum["STABLE", "IMPROVING", "WORSENING", "VOLATILE"]
  - slope: float (linear regression slope — positive = worsening for most params)
  - months_to_threshold: Optional[int] (None if stable/improving)
  - threshold_value: float (the clinical alert threshold for this param)
  - threshold_label: str (e.g. "Pre-diabetes range", "Hypertension Stage 1")
  - confidence: float (R² of the regression — 0 to 1)
  - data_points_used: int (number of readings in regression)
  - alert_level: Enum["NONE", "WATCH", "WARN", "URGENT"]
  - narrative: str (AI-generated one-sentence plain-English summary)

Methods:
  - validate(): slope is finite float, confidence between 0 and 1,
    months_to_threshold if set must be > 0, data_points_used >= 3
  - to_dict() / from_dict()
  - is_actionable() -> bool: True if alert_level != "NONE" and confidence > 0.60
```

**Alert Level Logic:**
```
months_to_threshold >= 24  → WATCH  ("trending toward threshold — monitor closely")
months_to_threshold 12–23  → WARN   ("may cross threshold within 2 years")
months_to_threshold < 12   → URGENT ("on track to cross threshold within a year")
current_trend == "STABLE" or "IMPROVING" → NONE
```

---

### 2.4 `DoctorAccess` Class (NEW)

```
Class: DoctorAccess
Responsibility: Grants a doctor (identified by email + registration number)
                read-only access to a specific patient's health timeline.

Attributes:
  - access_id: str (UUID4)
  - patient_profile_id: str (FK → FamilyProfile — the patient being shared)
  - granted_by_user_id: str (FK → User — who granted access)
  - doctor_name: str
  - doctor_email: str
  - doctor_registration_number: Optional[str] (MCI/NMC registration)
  - specialization: Optional[str]
  - access_token: str (UUID4 — used in the access URL)
  - granted_at: datetime
  - expires_at: datetime (default: 30 days from grant)
  - last_accessed_at: Optional[datetime]
  - access_count: int (how many times doctor has opened the workspace)
  - is_active: bool
  - scope: list[str] (what the doctor can see: ["records", "timeline", "risk", "medications"])

Methods:
  - validate(): doctor_email valid format, expires_at must be in future,
    scope must be non-empty list of valid values
  - is_expired() -> bool
  - to_dict() / from_dict()
  - generate_workspace_url() -> str: returns /doctor-view/{access_token}
```

---

### 2.5 `SubscriptionTier` Class (NEW)

```
Class: SubscriptionTier
Responsibility: Tracks a user's subscription plan and feature access gates.

Attributes:
  - subscription_id: str (UUID4)
  - user_id: str (FK → User)
  - tier: Enum["FREE", "PREMIUM", "PRO"]
  - started_at: datetime
  - expires_at: Optional[datetime] (None for FREE — never expires)
  - is_active: bool
  - payment_reference: Optional[str] (Razorpay order ID)
  - family_member_limit: int (FREE=2, PREMIUM=5, PRO=10)
  - doctor_access_limit: int (FREE=0, PREMIUM=3, PRO=unlimited)
  - prediction_enabled: bool (FREE=False, PREMIUM=True, PRO=True)
  - wearable_enabled: bool (FREE=False, PREMIUM=True, PRO=True)
  - api_access_enabled: bool (FREE=False, PREMIUM=False, PRO=True)

Methods:
  - validate(): tier must be valid Enum, expires_at if set must be in future
  - is_feature_available(feature: str) -> bool
  - days_remaining() -> Optional[int]
  - to_dict() / from_dict()
```

**Tier Feature Gates:**
```
FREE:     2 family members, 3 doctor reports/month, no predictions,
          no wearables, no doctor workspace, no API access
PREMIUM:  5 family members, unlimited reports, predictions, wearables,
          3 doctor workspaces, no API access — ₹299/month
PRO:      10 family members, unlimited everything, API access,
          WhatsApp bot, priority Groq inference — ₹799/month
```

---

### 2.6 `WhatsAppSession` Class (NEW)

```
Class: WhatsAppSession
Responsibility: Tracks a WhatsApp bot session for a user — links phone number
                to ArogyaMitra account and maintains conversation context.

Attributes:
  - session_id: str (UUID4)
  - user_id: str (FK → User)
  - phone_number: str (E.164 format — e.g. +919876543210)
  - verified_at: datetime (when OTP was confirmed)
  - is_active: bool
  - active_profile_id: str (which FamilyProfile context is active in chat)
  - last_message_at: Optional[datetime]
  - conversation_state: str (JSON — current multi-turn conversation context)
  - otp_hash: Optional[str] (bcrypt hash of OTP during verification)
  - otp_expires_at: Optional[datetime]

Methods:
  - validate(): phone_number must match E.164 regex, user_id must exist
  - is_otp_valid(otp: str) -> bool: bcrypt compare + expiry check
  - to_dict() / from_dict()
```

---

## 3. Phase 3 Feature Modules

---

### Feature 1: Predictive Health Timeline

**Description:** ArogyaMitra's most powerful Phase 3 feature. After a patient has 3+ readings for any clinical parameter, the Prediction Agent runs linear regression on the time-series and forecasts when (if ever) the patient will cross a clinical threshold. This is not a guess — it is a statistically grounded projection with confidence scores.

**Implementation Approach:**

```
PredictionService class:
  fit_trend(param_name, dates, values):
    1. Convert dates to ordinal integers (days since epoch)
    2. numpy polyfit degree=1 → slope + intercept
    3. Compute R² (coefficient of determination) as confidence score
    4. Determine current_trend:
       - slope > +0.02 per month → "WORSENING" (for most params)
       - slope < -0.02 per month → "IMPROVING"
       - |slope| <= 0.02 → "STABLE"
       - R² < 0.4 → "VOLATILE" (insufficient linear pattern)
    5. If WORSENING and R² >= 0.50:
       - Extrapolate to threshold: months = (threshold - current) / slope_per_month
    6. Build PredictionResult with alert_level + narrative
    7. narrative generated by Groq llama-3.1-8b-instant:
       prompt = "In one plain-English sentence for a non-medical patient,
                 summarize: param={param_name}, current={value}, trend={trend},
                 months_to_threshold={N}. Be reassuring but honest."

Prediction Agent (LangGraph node):
  - Runs AFTER Trend Agent on every record upload
  - Also runs on demand via POST /api/predictions/rerun
  - For each param with >= 3 readings: calls PredictionService.fit_trend()
  - Saves PredictionResult to DB
  - Adds URGENT predictions to Dashboard alert banner
```

**UI — Prediction Card on Timeline:**
```
Each parameter timeline shows a dotted extrapolation line beyond the last reading.
Color: teal (stable) → amber (watch) → red (urgent).
Card text example:
  "📈 HbA1c Trend: At current rate, you may cross the pre-diabetes threshold
   (6.5%) in approximately 11 months. Confidence: 78%.
   [Talk to your doctor about this →]"
```

**Validation Rules:**
- Minimum 3 readings required — raise `InsufficientDataError` if fewer
- R² < 0.40 → `current_trend = "VOLATILE"` — do not compute months_to_threshold
- `confidence` must be between 0.0 and 1.0 — clamp, never raise
- If slope is negative for a "higher is worse" param (e.g. HbA1c) → `IMPROVING`, no alert
- `months_to_threshold` cap: display max "36+ months" — do not extrapolate beyond 3 years

---

### Feature 2: Family Health Profiles

**Description:** One ArogyaMitra account manages health records for the entire family — elderly parents, spouse, children — each with fully isolated data, their own timeline, risk score, and reminders.

**Implementation Approach:**

```
FamilyProfileService class:
  create_member(owner_user_id, name, relation, dob, gender):
    → validate() → save FamilyProfile → return profile_id

  get_all_members(user_id):
    → return list of FamilyProfile where owner_user_id = user_id AND is_active = True

  switch_active_context(user_id, profile_id):
    → validate profile belongs to user
    → store active_profile_id in session/JWT claims
    → all subsequent requests use this profile_id

All existing services (OCR, risk, reminders, report) accept profile_id parameter.
All DB queries updated: filter by profile_id instead of user_id directly.
```

**UI — Family Switcher:**
```
Top of Dashboard: Avatar row showing all family member initials.
Active member highlighted in teal ring.
Tap any member → entire dashboard switches context to that member.
Upload, Timeline, Reminders, Report all scoped to the active member.
```

**Validation Rules:**
- `relation == "SELF"` profile auto-created at User registration — only 1 allowed per account
- Maximum 10 members — configurable per subscription tier (FREE: 2, PREMIUM: 5, PRO: 10)
- Switching to another member requires the user to be the account owner — no shared accounts Phase 3
- All existing Phase 1 + Phase 2 API endpoints must accept `?profile_id=` query param
- If `profile_id` not provided → default to the user's SELF profile silently

---

### Feature 3: ABDM / FHIR Integration

**Description:** India's Ayushman Bharat Digital Mission (ABDM) provides a national health record infrastructure. ArogyaMitra integrates with it — allowing users to connect their ABHA ID and automatically pull records from ABDM-linked hospitals, clinics, and labs.

**Implementation Approach:**

```
ABDMService class:
  Endpoints: ABDM sandbox/production APIs (https://healthid.ndhm.gov.in)

  link_abha_id(profile_id, abha_id, mobile_otp):
    1. Call ABDM API: POST /v1/auth/init {healthid: abha_id}
    2. Receive OTP on user's ABDM-registered mobile
    3. User enters OTP in ArogyaMitra
    4. Call ABDM API: POST /v1/auth/confirm {txnId, otp}
    5. Receive ABDM access token + user demographics
    6. Store ABDM token (encrypted) in FamilyProfile.abha_id field
    7. Trigger record fetch

  fetch_abdm_records(profile_id):
    1. Use stored ABDM access token
    2. Call ABDM FHIR API: GET /fhir/Patient/{abha_id}/$everything
    3. Parse FHIR Bundle → extract DiagnosticReport, MedicationRequest, Observation resources
    4. Convert each FHIR resource → ArogyaMitra HealthRecord format
    5. Run Ingestion Agent on each converted record
    6. Return count of records fetched

FHIR → ArogyaMitra mapping:
  DiagnosticReport → record_type = "LAB_REPORT"
  MedicationRequest → record_type = "PRESCRIPTION"
  Observation (lab value) → ClinicalParameter (direct extraction — no OCR needed)
  ImagingStudy → record_type = "IMAGING"
```

**UI:**
```
Settings → "Connect ABHA ID" section.
Enter 14-digit ABHA ID → OTP sent to registered mobile.
After verification: "Fetching your ABDM records..." loading state.
Success: "✅ 12 records imported from your ABHA account"
Ongoing: Auto-refresh every 30 days or on-demand "Sync ABDM" button.
```

**Validation Rules:**
- `abha_id` must be 14 digits — raise `InvalidABHAIDError`
- ABDM OAuth token stored AES-256 encrypted — same encryption service as files
- FHIR parsing failures are logged but never crash the sync — partial success is acceptable
- Duplicate records detected by `source_reference_id` (FHIR resource ID) — skip if already imported
- ABDM API rate limit: max 1 full sync per 24 hours per profile — raise `ABDMSyncCooldownError`

---

### Feature 4: Multilingual OCR + UI

**Description:** ArogyaMitra becomes accessible to non-English-speaking patients in Hindi, Tamil, and Telugu — both in OCR extraction (reading regional-language lab reports) and in the UI language.

**Implementation Approach:**

```
Multilingual OCR:
  EasyOCR already supports: ['en', 'hi', 'ta', 'te']
  
  MultilingualOCRService(extends existing ocr_service.py):
    detect_language(image_path) -> str:
      Use langdetect on a sample crop of the image text
      Return: "en", "hi", "ta", "te"
    
    extract_text(file_path, languages=None):
      If languages=None: auto-detect + include English
      reader = easyocr.Reader(['en', detected_lang])
      return reader.readtext(file_path, detail=0, paragraph=True)
    
    The entity_extractor handles extracted text regardless of language —
    parameter values (numbers + units) are language-agnostic.
    Parameter name matching uses the SUPPORTED_PARAMETERS aliases list
    (expand aliases to include Hindi/Tamil/Telugu parameter names).

Hindi parameter aliases to add to config.py:
  "hba1c": aliases += ["ग्लाइकेटेड हीमोग्लोबिन", "एचबीए1सी"]
  "hemoglobin": aliases += ["हीमोग्लोबिन", "हिमोग्लोबिन"]
  "blood_sugar": aliases += ["रक्त शर्करा", "ब्लड शुगर"]
  (expand similarly for Tamil + Telugu)

Frontend i18n:
  Library: react-i18next
  Translation files: /frontend/src/locales/{en,hi,ta,te}/translation.json
  Language switcher: Globe icon in Navbar/BottomNav
  Persist language choice: localStorage ("arogya_lang")
  All UI strings must use t("key") — no hardcoded English
  Date formatting: use date-fns with locale-aware formatters
```

**Validation Rules:**
- If language detection confidence < 0.70 → default to `['en']` only — do not break
- Translation files must be complete — missing keys fall back to English, never show key string
- Language switcher must not require page reload (dynamic i18n)
- Numbers and units always displayed in English (numerals) regardless of UI language

---

### Feature 5: Doctor-Patient Shared Workspace

**Description:** A patient grants a doctor read-only access to their ArogyaMitra health timeline via a long-lived (30-day) access link. The doctor opens a clean, clinical view — parameters, trends, anomalies, medications, prediction alerts — without needing to create an ArogyaMitra account.

**Implementation Approach:**

```
DoctorWorkspaceService:
  grant_access(patient_profile_id, user_id, doctor_name, doctor_email, scope, days=30):
    1. validate() all inputs
    2. Check subscription tier: FREE → raise FeatureNotAvailableError
    3. Check doctor_access_limit for tier
    4. Create DoctorAccess record with access_token = uuid4()
    5. Send access link to doctor_email via email (or display for user to share)
    6. Return {workspace_url: /doctor-view/{access_token}, expires_at}

  get_workspace_data(access_token) -> dict:
    1. Lookup DoctorAccess by access_token
    2. If is_expired() or not is_active → raise WorkspaceAccessExpiredError (410)
    3. Load patient FamilyProfile (member name, age, gender — no PII like full DOB)
    4. Load ClinicalParameter history per scope
    5. Load latest RiskScore
    6. Load active Reminders (medications only)
    7. Load latest PredictionResults
    8. Update last_accessed_at + increment access_count
    9. Return structured workspace payload

Doctor Workspace UI (/doctor-view/{token}):
  - Clean, clinical design — teal + white, no consumer app chrome
  - Patient header: "Viewing: [Member Name], [Age], [Gender]"
  - Tabbed layout: Overview | Parameters | Predictions | Medications
  - Overview: Risk gauge + URGENT prediction alerts
  - Parameters: Same timeline chart as patient view (read-only)
  - Predictions: Table of all PredictionResults with alert levels
  - Medications: Active reminder list with dosage info
  - Footer: "Powered by ArogyaMitra AI — Data shared by patient with consent"
  - NO edit/delete controls — pure read-only view
  - Print button → browser print-optimized CSS layout
```

**Validation Rules:**
- `scope` list must only contain: `["records", "timeline", "risk", "medications", "predictions"]`
- Expired token returns `HTTP 410 Gone` with "This workspace link has expired" message
- `access_count` increments on every load — doctor can see how many times they've accessed
- Patient can revoke access at any time via `DELETE /api/doctor-access/{access_id}`
- Doctor email notification on grant: plain HTML email with workspace URL + expiry date
- Workspace URL must not appear in URL history / browser suggest for security (use POST redirect)

---

### Feature 6: WhatsApp Health Bot

**Description:** Users can interact with ArogyaMitra via WhatsApp. Ask for their latest risk score, upcoming reminders, last HbA1c value, or request a Doctor-Prep report to be sent — all without opening the app.

**Implementation Approach:**

```
WhatsApp Integration: Twilio WhatsApp Business API (or Meta Cloud API)
Webhook: POST /api/whatsapp/webhook

WhatsAppBotService:
  handle_incoming(from_number, body):
    1. Lookup WhatsAppSession by phone_number
    2. If no session → initiate verification flow (OTP)
    3. If unverified → send OTP, prompt confirmation
    4. If verified → parse intent from body text

  parse_intent(body: str) -> dict:
    Use Groq llama-3.1-8b-instant with intent classification prompt:
    {
      "intents": ["risk_score", "last_reading", "reminders", "send_report", "help", "switch_member"],
      "entities": {"param_name": "hba1c", "member_name": "dad"}
    }
    Return parsed intent + entities

  execute_intent(session, intent, entities) -> str:
    "risk_score" → fetch latest RiskScore for active profile → format reply
    "last_reading" → fetch latest ClinicalParameter for named param → format reply
    "reminders" → fetch today's reminders → format as numbered list
    "send_report" → trigger DoctorPrepAgent → send PDF via WhatsApp media message
    "switch_member" → update session.active_profile_id
    "help" → return help menu

Verification Flow:
  User texts "Hi" from unregistered number
  → Bot: "Welcome to ArogyaMitra! Enter your registered email to link this number."
  → User sends email
  → Bot: "OTP sent to your email. Enter it here."
  → User sends OTP → verify → WhatsAppSession created

Example Bot Replies:
  User: "my hba1c"
  Bot: "📊 HbA1c (Dad) — Latest: 6.8% (Oct 12, 2026)
        Status: HIGH ⚠️
        Trend: 📈 Worsening — was 6.2% in Jan 2026
        Prediction: May cross 7.0% in ~8 months."

  User: "send me my report"
  Bot: [generates PDF + sends as WhatsApp document]
       "📄 Your Doctor-Prep Report is ready! Generated on Oct 26, 2026."
```

**Validation Rules:**
- Phone number must match E.164 format — raise `InvalidPhoneNumberError`
- OTP expires in 10 minutes — raise `OTPExpiredError` after expiry
- Bot rate limit: max 20 messages per user per hour — raise `BotRateLimitError`
- PDF via WhatsApp: max 16MB (WhatsApp media limit) — ReportLab output typically < 1MB
- Webhook must validate Twilio signature header before processing — `InvalidWebhookSignatureError`
- WhatsApp feature gated to PRO tier in Phase 3 — `FeatureNotAvailableError` for lower tiers

---

### Feature 7: Wearable Passive Monitoring

**Description:** Connect Fitbit, Mi Band (Zepp/Amazfit), Garmin, or Samsung Health to automatically import heart rate, step count, sleep data, and blood oxygen readings — without manual upload.

**Implementation Approach:**

```
Wearable OAuth Flow (per device):
  1. User taps "Connect [Device]" in Settings
  2. Backend generates OAuth authorization URL for device's API
  3. User redirected to device login → grants permission
  4. Device redirects to /api/wearables/callback/{source}?code=...
  5. Backend exchanges code for access_token + refresh_token
  6. Tokens stored AES-256 encrypted in WearableToken table
  7. Initial sync runs immediately

Supported APIs:
  Fitbit    → Fitbit Web API (OAuth 2.0) — heart rate, sleep, steps, SpO2
  Garmin    → Garmin Health API (OAuth 1.0a) — HR, steps, stress, sleep
  Mi Band   → Zepp Health Open API (OAuth 2.0) — HR, steps, sleep
  Samsung   → Samsung Health SDK (already integrated via Eka Care partnership)

WearableSyncService:
  sync_all(profile_id):
    For each connected wearable (active WearableToken):
      → Call device API for last 7 days of data
      → Convert to WearableReading objects
      → Filter duplicates (by recorded_at + metric_type + source)
      → Save new readings
      → For HEART_RATE / BLOOD_OXYGEN: also create ClinicalParameter
        (so they appear on the Health Timeline)
      → Return sync summary

  refresh_token_if_needed(token_record):
    If access_token expires within 1 hour:
      → Use refresh_token to get new access_token
      → Update WearableToken record

Scheduled Sync:
  APScheduler (or simple startup background task):
  Run sync_all for all users with connected wearables every 6 hours
```

**Validation Rules:**
- OAuth tokens stored AES-256 encrypted — never in plain text
- If API call fails (device API down): log warning, do not crash sync — partial sync is fine
- Duplicate readings skipped silently (same `recorded_at` + `metric_type` + `source`)
- Heart rate values outside 30–250 BPM flagged as `is_anomaly=True` before saving
- Blood oxygen below 85% → auto-generate URGENT reminder: "Low SpO2 detected — consult a doctor"
- Token refresh failure → mark WearableToken as `needs_reconnect=True` → notify user in app

---

### Feature 8: Subscription & Monetization (Razorpay)

**Description:** A freemium model — Free tier provides core value, Premium and Pro unlock advanced features. Payments via Razorpay (India's leading payment gateway).

**Implementation Approach:**

```
RazorpayService:
  create_order(user_id, tier, months=1) -> dict:
    amount = TIER_PRICES[tier] * months  # in paise (₹299 = 29900 paise)
    order = razorpay_client.order.create({
      "amount": amount,
      "currency": "INR",
      "receipt": f"arogya_{user_id}_{tier}_{timestamp}",
      "notes": {"user_id": user_id, "tier": tier}
    })
    return {"order_id": order["id"], "amount": amount, "currency": "INR"}

  verify_payment(order_id, payment_id, signature) -> bool:
    Verify HMAC-SHA256 signature using Razorpay secret key
    If valid: create/update SubscriptionTier record
    If invalid: raise PaymentVerificationError

  webhook_handler(payload, signature):
    Verify webhook signature
    On payment.captured: activate subscription
    On subscription.cancelled: degrade to FREE tier gracefully

TIER_PRICES = {
  "PREMIUM": 29900,   # ₹299/month in paise
  "PRO":     79900,   # ₹799/month in paise
}

FeatureGate middleware:
  @require_tier("PREMIUM")  decorator for route handlers
  Checks SubscriptionTier.is_feature_available(feature)
  If not available: raise FeatureNotAvailableError with upgrade prompt
```

**UI — Subscription Page:**
```
/subscription page with 3 tier cards (FREE | PREMIUM | PRO)
Each card: feature checklist, price, "Current Plan" badge or "Upgrade" button
Upgrade flow: Razorpay checkout modal (embedded JS)
Post-payment: instant feature unlock — no page refresh required
Subscription management: cancel, view renewal date, download invoice
```

**Validation Rules:**
- Payment signature must be HMAC-SHA256 verified before any subscription activation
- Downgrade: immediate tier change, no refunds (display this clearly pre-purchase)
- Expired subscription gracefully downgrades to FREE — data never deleted on downgrade
- FREE tier users see "🔒 Premium Feature" badges on locked features with upgrade CTA
- Webhook endpoint must be publicly accessible + Razorpay-signature-verified

---

### Feature 9: Health Score API (B2B)

**Description:** Expose ArogyaMitra's health intelligence as a REST API — clinics, insurance companies, and third-party apps can query a patient's health score and parameter trends (with patient consent).

**Implementation Approach:**

```
API Key Management:
  APIKey model:
    - key_id: UUID4
    - user_id: FK → User (the PRO account holder)
    - api_key: str (32-char random hex — shown once at creation)
    - api_key_hash: str (SHA-256 hash — stored, not the plain key)
    - name: str (e.g. "My Clinic Integration")
    - created_at: datetime
    - last_used_at: Optional[datetime]
    - is_active: bool
    - rate_limit: int (requests per hour — default 100)

API Endpoints (under /v1/ prefix — versioned):
  GET  /v1/health-score/{profile_id}     → latest RiskScore for profile
  GET  /v1/parameters/{profile_id}       → all latest ClinicalParameter values
  GET  /v1/predictions/{profile_id}      → all PredictionResult objects
  GET  /v1/medications/{profile_id}      → active MEDICATION reminders
  POST /v1/records/{profile_id}/ingest   → push a FHIR Observation to ArogyaMitra

Authentication: Bearer API key in Authorization header
  Middleware: hash incoming key → lookup APIKey table → validate
  Rate limiting: per api_key_id → max rate_limit requests/hour

Consent Model:
  Profile must have api_access_scope set by the user:
  POST /api/settings/api-consent
  {
    "allowed_keys": ["key_id_1"],
    "scope": ["risk_score", "parameters"]  // what the API key can access
  }
```

**Validation Rules:**
- API access gated to PRO tier — raise `FeatureNotAvailableError` for lower tiers
- API key shown ONLY once at creation — hash stored, plain key never retrievable again
- Each API request logs: key_id, endpoint, timestamp, response_code → audit table
- Rate limit exceeded → HTTP 429 with Retry-After header
- Profile consent must be explicitly granted before any API key can read that profile's data

---

### Feature 10: Voice-First Input

**Description:** User speaks their symptoms, medication names, or lab values — ArogyaMitra transcribes, understands, and creates structured records or reminders automatically.

**Implementation Approach:**

```
VoiceInputService:
  transcribe(audio_blob: bytes, language: str = "hi-IN") -> str:
    Use Groq Whisper API (whisper-large-v3):
    response = groq_client.audio.transcriptions.create(
      model="whisper-large-v3",
      file=("audio.webm", audio_blob, "audio/webm"),
      language=language,
      response_format="text"
    )
    return response

  parse_health_intent(transcript: str) -> dict:
    Groq llama-3.3-70b with structured output prompt:
    "Extract from this health statement:
     {
       'intent': 'add_lab_value' | 'add_reminder' | 'report_symptom' | 'query',
       'param_name': Optional[str],
       'value': Optional[float],
       'unit': Optional[str],
       'medicine_name': Optional[str],
       'dosage': Optional[str],
       'symptom': Optional[str],
       'query_type': Optional[str]
     }
     Statement: {transcript}"

  handle_voice_command(profile_id, audio_blob, language):
    1. transcribe(audio_blob, language)
    2. parse_health_intent(transcript)
    3. Route by intent:
       'add_lab_value' → create ClinicalParameter directly (manual entry)
       'add_reminder'  → create Reminder (medication/appointment)
       'report_symptom' → add to a new DOCTOR_NOTE HealthRecord
       'query'         → query DB + return plain-text answer via TTS

Supported Input Languages: English, Hindi, Tamil, Telugu
Frontend Voice UI:
  Microphone button on Upload page + Dashboard
  Press-and-hold to record (max 60 seconds)
  Visual waveform animation during recording
  Transcript displayed for user confirmation before saving
  "Confirm" → save | "Re-record" → discard + try again
```

**Validation Rules:**
- Audio max duration: 60 seconds — raise `AudioTooLongError`
- Audio max size: 25MB (Groq Whisper limit) — raise `AudioFileTooLargeError`
- Supported formats: webm, mp3, mp4, wav — raise `UnsupportedAudioFormatError`
- Transcript confidence: if Groq returns empty string → retry once, then prompt re-record
- User must confirm transcript before any data is saved — never auto-save from voice
- Voice feature available on PREMIUM + PRO tiers only

---

## 4. Phase 3 New Exceptions

```python
# Family profile
class CannotDeletePrimaryProfileError(ArogyaError): pass
class FamilyMemberLimitError(ArogyaError): pass
class InvalidABHAIDError(ArogyaError): pass
class FamilyProfileNotFoundError(ArogyaError): pass

# ABDM
class ABDMAuthError(ArogyaError): pass
class ABDMSyncCooldownError(ArogyaError): pass
class FHIRParseError(ArogyaError): pass

# Predictions
class InsufficientDataForPredictionError(ArogyaError): pass
class VolatileTrendError(ArogyaError): pass

# Doctor workspace
class WorkspaceAccessExpiredError(ArogyaError): pass
class WorkspaceNotFoundError(ArogyaError): pass

# WhatsApp
class InvalidPhoneNumberError(ArogyaError): pass
class OTPExpiredError(ArogyaError): pass
class BotRateLimitError(ArogyaError): pass
class InvalidWebhookSignatureError(ArogyaError): pass

# Wearables
class WearableAuthError(ArogyaError): pass
class WearableSyncError(ArogyaError): pass

# Subscription / Payment
class PaymentVerificationError(ArogyaError): pass
class FeatureNotAvailableError(ArogyaError): pass
class SubscriptionNotFoundError(ArogyaError): pass

# API
class APIKeyNotFoundError(ArogyaError): pass
class APIRateLimitError(ArogyaError): pass
class ConsentNotGrantedError(ArogyaError): pass

# Voice
class AudioTooLongError(ArogyaError): pass
class AudioFileTooLargeError(ArogyaError): pass
class UnsupportedAudioFormatError(ArogyaError): pass
class TranscriptionFailedError(ArogyaError): pass
```

---

## 5. Phase 3 Build Order (AI IDE Recommended)

```
Step 1: Family Profiles
  Create FamilyProfile ORM + migration
  Update ALL existing endpoints to accept profile_id param
  Update all DB queries to filter by profile_id
  Build family router + UI switcher
  Test: Create 3 members, switch context, verify data isolation

Step 2: Predictive Health Timeline
  Build PredictionService (numpy linear regression)
  Add Prediction Agent as LangGraph node (after Trend Agent)
  Create PredictionResult ORM + router
  Update Timeline page: add dotted extrapolation line + prediction card
  Test: 5+ readings for HbA1c → prediction generated → shown on timeline

Step 3: Subscription & Razorpay
  SubscriptionTier ORM + router
  RazorpayService (order create + verify + webhook)
  FeatureGate decorator/middleware
  Subscription UI page
  Test: Full payment flow (Razorpay test mode) → feature unlocked

Step 4: ABDM / FHIR Integration
  ABDMService (OAuth + FHIR record fetch)
  FHIRParser (DiagnosticReport/Observation → HealthRecord/ClinicalParameter)
  ABDM settings UI + sync button
  Test: ABDM sandbox → verify records imported correctly

Step 5: Doctor-Patient Shared Workspace
  DoctorAccess ORM + router
  DoctorWorkspaceService (data aggregation)
  Doctor view page (/doctor-view/{token}) — separate clean design
  Email notification on grant
  Test: Grant access → open link as doctor → verify read-only view

Step 6: Multilingual OCR + UI
  Expand EasyOCR language list
  Add Hindi/Tamil/Telugu parameter aliases to config.py
  Install + configure react-i18next
  Build translation files (en, hi, ta, te)
  Language switcher component
  Test: Upload Hindi lab report → parameters extracted → switch to Hindi UI

Step 7: Wearable Passive Monitoring
  WearableToken ORM (AES encrypted)
  OAuth flows per device (start with Fitbit)
  WearableSyncService + APScheduler background job
  Settings UI: connect/disconnect wearables
  Test: Fitbit OAuth → sync → heart rate appears on timeline

Step 8: WhatsApp Health Bot
  WhatsAppSession ORM
  Twilio webhook endpoint + signature verification
  WhatsAppBotService (intent parsing + execution)
  OTP verification flow
  Test: Full conversation flow on WhatsApp test number

Step 9: Voice-First Input
  VoiceInputService (Groq Whisper + intent parser)
  Frontend microphone component (press-and-hold)
  Voice confirmation UI (transcript review before save)
  Test: Speak "My HbA1c is 7.2 percent" → ClinicalParameter created

Step 10: Health Score API
  APIKey ORM + management router
  /v1/ API versioned router
  API key auth middleware + rate limiting
  Consent model (per-profile, per-key scope)
  Test: Generate API key → curl /v1/health-score/{profile_id} → JSON response

Step 11: Full Phase 3 Checklist
  Run PHASE3_CHECKLIST.md — all items must pass
  Run Phase 1 + Phase 2 checklists — confirm nothing regressed
```

---

*End of FEATURES_PHASE3.md*
