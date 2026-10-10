# ArogyaMitra AI — Phase 1 Validation Checklist
> Use this file to validate every feature before marking Phase 1 complete.
> Check each item manually or via automated test.
> Status: [ ] Pending | [x] Done | [!] Failed — needs fix

---

## SECTION 1: Project Setup & Environment

- [ ] `requirements.txt` exists and all packages install without errors (`pip install -r requirements.txt`)
- [ ] `.env` file contains all 6 required variables (`GROQ_API_KEY`, `SECRET_KEY`, `ENCRYPTION_KEY`, `CHROMA_DB_PATH`, `SQLITE_DB_PATH`, `UPLOAD_DIR`)
- [ ] FastAPI server starts without errors (`uvicorn main:app --reload`)
- [ ] FastAPI `/docs` (Swagger UI) loads and shows all routers
- [ ] SQLite database file created at path defined in `.env`
- [ ] All 5 DB tables created: `health_records`, `clinical_parameters`, `risk_scores`, `reminders`, `doctor_reports`
- [ ] ChromaDB collection initializes without errors at configured path
- [ ] Frontend builds without errors (`npm run dev`)
- [ ] Frontend loads at `localhost:5173` and Navbar renders correctly
- [ ] Axios `api.js` points to correct `VITE_API_BASE_URL`

---

## SECTION 2: OOP Entity Classes

### HealthRecord
- [ ] Class exists in `backend/models/health_record.py`
- [ ] All 12 attributes defined and typed correctly
- [ ] `validate()` raises `InvalidRecordTypeError` for invalid record_type
- [ ] `validate()` raises `FutureDateError` when report_date is in the future
- [ ] `to_dict()` returns a JSON-serializable dictionary
- [ ] `from_dict()` reconstructs the object correctly
- [ ] `generate_share_token()` returns a non-empty JWT string
- [ ] `is_share_valid()` returns `False` after token expiry time

### ClinicalParameter
- [ ] Class exists in `backend/models/clinical_parameter.py`
- [ ] `compute_status()` returns "CRITICAL" when `value > reference_range_max * 2`
- [ ] `compute_status()` returns "HIGH" when `value > reference_range_max`
- [ ] `compute_status()` returns "LOW" when `value < reference_range_min`
- [ ] `compute_status()` returns "NORMAL" when within range
- [ ] `validate()` raises `InvalidParameterValueError` for negative values
- [ ] `validate()` raises `MissingUnitError` for empty unit string
- [ ] `param_name` not in `SUPPORTED_PARAMETERS` list raises appropriate error

### RiskScore
- [ ] `overall_risk` is clamped between 0.0 and 1.0 (never exceeds 1.0)
- [ ] `compute_risk_level()` maps correctly: <0.30 → LOW, <0.60 → MODERATE, <0.80 → HIGH, ≥0.80 → CRITICAL
- [ ] `validate()` raises error if `contributing_factors` is empty list
- [ ] `version` increments correctly on each recompute

### Reminder
- [ ] `validate()` raises `EmptyReminderTitleError` for title with < 3 characters
- [ ] `validate()` raises `InvalidDueDateError` for due_date more than 2 years in future
- [ ] `is_due_today()` returns `True` only for reminders due on current date
- [ ] `recurrence` accepts only `NONE`, `DAILY`, `WEEKLY`, `MONTHLY`

### DoctorReport
- [ ] `validate()` raises error if `report_content` is empty
- [ ] `validate()` raises error if `records_included` list is empty
- [ ] `generate_share_token()` and `is_share_valid()` work identically to HealthRecord

---

## SECTION 3: CRUD Operations

### Health Records CRUD
- [ ] `POST /api/records/upload` — accepts PDF file, returns 201 with `record_id`
- [ ] `POST /api/records/upload` — accepts image file (jpg/png), returns 201
- [ ] `POST /api/records/upload` — accepts manual text entry JSON, returns 201
- [ ] `POST /api/records/upload` — rejects file > 10MB with 400 error
- [ ] `POST /api/records/upload` — rejects unsupported MIME type with 400 error
- [ ] `GET /api/records/` — returns list of all non-deleted records
- [ ] `GET /api/records/{id}` — returns single record with extracted entities
- [ ] `GET /api/records/{id}` — returns 404 for non-existent ID
- [ ] `PUT /api/records/{id}` — updates report_date and record_type successfully
- [ ] `PUT /api/records/{id}` — rejects invalid record_type with 422 error
- [ ] `DELETE /api/records/{id}` — sets `is_deleted=True`, record still in DB
- [ ] `GET /api/records/` — soft-deleted records do NOT appear in list

### Clinical Parameters CRUD
- [ ] `GET /api/params/` — returns all parameters with status badges
- [ ] `GET /api/params/{param_name}` — returns historical values sorted by `report_date` ascending
- [ ] `GET /api/params/{param_name}` — returns empty list (not error) if no data for that param
- [ ] `PUT /api/params/{param_id}` — updates value and re-runs `compute_status()`
- [ ] `PUT /api/params/{param_id}` — rejects negative value with 422 error

### Reminders CRUD
- [ ] `POST /api/reminders/` — creates reminder, returns 201
- [ ] `POST /api/reminders/` — rejects empty title with 422 error
- [ ] `POST /api/reminders/` — rejects past due_date for new reminders
- [ ] `GET /api/reminders/` — returns only `is_active=True` reminders by default
- [ ] `PUT /api/reminders/{id}` — updates title and due_date
- [ ] `DELETE /api/reminders/{id}` — hard deletes, record gone from DB
- [ ] `PATCH /api/reminders/{id}/ack` — sets `is_acknowledged=True`
- [ ] Acknowledged reminders no longer appear in active list

### Risk Score
- [ ] `GET /api/risk/current` — returns latest risk score
- [ ] `GET /api/risk/current` — returns 404 with message "Upload your first report to see your health score" if no records
- [ ] `GET /api/risk/history` — returns all historical risk scores sorted by `computed_at`
- [ ] `POST /api/risk/recompute` — creates new RiskScore with incremented `version`

### Doctor Report
- [ ] `POST /api/report/generate` — returns 400 if no processed records exist
- [ ] `POST /api/report/generate` — returns report with all 6 sections populated
- [ ] `POST /api/report/generate` — report_content length > 200 characters
- [ ] `GET /api/report/latest` — returns most recently generated report
- [ ] `GET /api/report/{id}/pdf` — returns downloadable PDF file (non-empty)
- [ ] `POST /api/report/{id}/share` — returns a valid token URL

---

## SECTION 4: Agent Pipeline

### Ingestion Agent
- [ ] Triggered automatically after `POST /api/records/upload`
- [ ] Tesseract correctly extracts text from a sample lab report PDF
- [ ] EasyOCR correctly extracts text from a sample prescription image
- [ ] At least 1 `ClinicalParameter` created from a standard lab report
- [ ] `HealthRecord.is_processed` set to `True` after agent completes
- [ ] If OCR text < 20 characters, agent sets `is_processed=False` and logs `OCRExtractionError`
- [ ] Agent handles corrupt/unreadable file gracefully — does not crash

### Trend Agent
- [ ] Triggered after Ingestion Agent completes
- [ ] Reads all `ClinicalParameter` objects for user from DB
- [ ] Risk score computed using rule-based engine (threshold logic applied correctly)
- [ ] `RiskScore` saved to DB with correct `risk_level`
- [ ] `contributing_factors` list contains all HIGH/CRITICAL parameters
- [ ] If no parameters exist, risk score is NOT computed (agent exits early)

### Reminder Agent
- [ ] Triggered only when `record_type == PRESCRIPTION`
- [ ] NOT triggered for LAB_REPORT records
- [ ] Auto-creates at least 1 MEDICATION reminder from a sample prescription
- [ ] Auto-created reminders have `created_from_record_id` populated
- [ ] Agent does not create duplicate reminders for the same medicine on re-run

### Doctor-Prep Agent
- [ ] Triggered via `POST /api/report/generate` (not automatic)
- [ ] Calls Groq `llama-3.3-70b-versatile` successfully
- [ ] Generated report contains all 6 sections (Patient Summary, Parameters, Flagged Concerns, Medications, Questions, Trends)
- [ ] Report uses actual data from DB (not hallucinated values)
- [ ] Agent retries once if report_content < 200 characters
- [ ] Report saved to `doctor_reports` table

### LangGraph Graph
- [ ] `ArogyaState` TypedDict has all required fields
- [ ] Conditional edge correctly routes to `reminder_agent` only for PRESCRIPTION records
- [ ] `errors` field in state captures exceptions without crashing entire graph
- [ ] Graph completes end-to-end without raising unhandled exceptions on sample input

---

## SECTION 5: Security Layer

- [ ] Uploaded files are AES-256-GCM encrypted before saving to disk
- [ ] Encrypted file on disk is NOT readable as plain text (verify manually)
- [ ] Decryption works correctly — file can be decrypted and fed to OCR
- [ ] Share token is a valid JWT (verifiable at jwt.io)
- [ ] Share token expires correctly after configured hours
- [ ] `GET /share/{expired_token}` returns HTTP 410 Gone (not 404)
- [ ] Share token cannot be regenerated for same record within 1 hour of last generation
- [ ] `.env` file is in `.gitignore` — not committed to version control
- [ ] `ENCRYPTION_KEY` is not hardcoded anywhere in source code

---

## SECTION 6: Frontend Validation

### UploadPage
- [ ] Drag-and-drop accepts PDF and image files
- [ ] File size > 10MB shows error toast before upload attempt
- [ ] Unsupported file types rejected with clear error message
- [ ] Manual entry form shows validation errors inline (not just console)
- [ ] Record type dropdown contains all 5 valid options
- [ ] Report date field rejects future dates
- [ ] Upload success shows confirmation and navigates to record detail

### DashboardPage
- [ ] Risk gauge renders with correct color (teal=low, amber=moderate, red=high/critical)
- [ ] "Upload your first report" empty state shows when no records exist
- [ ] Recent records list shows last 5 records
- [ ] Upcoming reminders section shows next 3 due reminders
- [ ] Clicking a record navigates to RecordDetailPage

### TimelinePage
- [ ] Parameter dropdown contains only parameters that have data
- [ ] Recharts line chart renders with date on X-axis and value on Y-axis
- [ ] Reference range rendered as horizontal shaded band
- [ ] "Not enough data" message shown when fewer than 2 data points exist
- [ ] Chart updates when different parameter selected from dropdown

### RemindersPage
- [ ] Create reminder form validates title (min 3 chars)
- [ ] Create reminder form rejects past due_date
- [ ] Acknowledge toggle updates UI immediately (optimistic update)
- [ ] Delete confirmation prompt before hard delete
- [ ] Recurrence badge displayed on each reminder card

### DoctorReportPage
- [ ] "Generate Report" button disabled if no processed records exist (with tooltip)
- [ ] Loading spinner shown during agent execution
- [ ] Report content rendered in readable formatted view (markdown → HTML)
- [ ] "Download PDF" button downloads non-empty PDF file
- [ ] "Share Link" button copies shareable URL to clipboard with toast confirmation

### SharePage
- [ ] Expired token shows "This link has expired" message (410 state)
- [ ] Invalid token shows "Invalid link" message
- [ ] Valid token renders report/record in read-only mode (no edit/delete buttons)

---

## SECTION 7: Error Handling

- [ ] All custom exceptions inherit from `ArogyaError`
- [ ] FastAPI returns structured JSON error response (with `error`, `message`, `field` keys)
- [ ] Frontend displays API error messages via toast notifications (not console-only)
- [ ] No unhandled 500 errors on any documented endpoint
- [ ] Agent pipeline errors stored in `ArogyaState.errors` without crashing graph
- [ ] OCR failure degrades gracefully — prompts manual entry fallback

---

## SECTION 8: End-to-End Flow Test

Run this full scenario manually and confirm all steps succeed:

```
Step 1:  Launch backend + frontend
Step 2:  Upload a sample lab report PDF (HbA1c, cholesterol included)
Step 3:  Verify HealthRecord created in DB (is_processed=True)
Step 4:  Verify at least 2 ClinicalParameters extracted
Step 5:  Verify RiskScore computed and visible on Dashboard
Step 6:  Navigate to Timeline → select HbA1c → chart renders
Step 7:  Upload a sample prescription image
Step 8:  Verify Reminder(s) auto-created for medicine(s)
Step 9:  Navigate to Reminders → acknowledge one reminder
Step 10: Navigate to Doctor Report → click Generate
Step 11: Verify 6-section report rendered
Step 12: Download PDF → open → verify content readable
Step 13: Click Share → copy link → open in incognito tab → report visible
Step 14: Wait for token to expire (or manually set expiry to 1 min) → verify 410 response
Step 15: Manually correct a ClinicalParameter value → verify status recomputes
Step 16: Trigger risk recompute → verify version incremented
```

All 16 steps passing = **Phase 1 Complete ✅**

---

## SECTION 9: Code Quality Checks

- [ ] All 5 entity classes have `__init__`, `validate()`, `to_dict()`, `from_dict()` implemented
- [ ] No hardcoded API keys or secrets in any `.py` or `.js` file
- [ ] All FastAPI route functions have Pydantic schema for request + response
- [ ] All `except` blocks are specific (no bare `except:` anywhere)
- [ ] `SUPPORTED_PARAMETERS` config list defined in one place (`config.py` backend, `parameterConfig.js` frontend) — not duplicated
- [ ] SQLAlchemy ORM used for all DB operations — no raw SQL strings in routers
- [ ] All async FastAPI endpoints use `async def` correctly

---

## Phase 1 Sign-Off

| Section | Total Items | Passed | Failed |
|---------|-------------|--------|--------|
| 1. Setup & Environment | 10 | | |
| 2. OOP Entity Classes | 22 | | |
| 3. CRUD Operations | 34 | | |
| 4. Agent Pipeline | 20 | | |
| 5. Security Layer | 9 | | |
| 6. Frontend Validation | 30 | | |
| 7. Error Handling | 7 | | |
| 8. E2E Flow | 16 | | |
| 9. Code Quality | 8 | | |
| **TOTAL** | **156** | | |

**Phase 1 is complete when all 156 items are checked ✅**

---

*End of PHASE1_CHECKLIST.md — Phase 1*
