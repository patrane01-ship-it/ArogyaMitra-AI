# ArogyaMitra AI — Functionality & Features Specification
> Version: Phase 1 (Prototype)
> Target: AI IDE Code Generation Ready
> Author: ArogyaMitra Dev

---

## 1. System Overview

ArogyaMitra AI is an **Agentic Personal Health Intelligence System** that ingests a user's scattered medical records (PDFs, images, manual entries), extracts structured health data using OCR and NLP, tracks clinical parameter trends over time using time-series analysis, and surfaces actionable insights through an agentic LangGraph pipeline.

**Core value:** "Your doctor sees you for 10 minutes. ArogyaMitra sees your entire health history."

---

## 2. Core Entities (OOP Design)

Every entity below must be implemented as a **Python class** with `__init__`, `validate()`, `to_dict()`, and `from_dict()` class methods. All entities are serialized to/from ChromaDB and local SQLite.

---

### 2.1 `HealthRecord` Class

```
Class: HealthRecord
Responsibility: Represents a single uploaded medical document (PDF, image, or text)

Attributes:
  - record_id: str (UUID4, auto-generated)
  - user_id: str (default: "local_user" for Phase 1)
  - record_type: Enum["LAB_REPORT", "PRESCRIPTION", "DOCTOR_NOTE", "IMAGING", "MANUAL_ENTRY"]
  - upload_date: datetime (auto-set on creation)
  - report_date: datetime (date on the actual document — extracted by OCR or entered manually)
  - source_file_path: str (encrypted local path to uploaded file)
  - raw_text: str (OCR extracted full text)
  - extracted_entities: dict (structured key-value pairs of clinical values, e.g. {"HbA1c": 6.2, "unit": "%"})
  - encryption_hash: str (AES-256 hash reference)
  - is_processed: bool (False until Ingestion Agent completes processing)
  - share_token: Optional[str] (generated only when user requests a share link)
  - share_expires_at: Optional[datetime]

Methods:
  - validate(): Checks record_type is valid enum, report_date is not in future, raw_text is not empty if is_processed=True
  - to_dict(): Serializes for ChromaDB storage
  - from_dict(data: dict): Deserializes from ChromaDB
  - generate_share_token(expiry_hours: int = 24): Creates a signed, expiring token
  - is_share_valid(): Returns bool — checks current time vs share_expires_at
```

**CRUD Operations for HealthRecord:**
| Operation | Endpoint | Description |
|-----------|----------|-------------|
| CREATE | `POST /api/records/upload` | Upload new record (PDF/image/text) |
| READ | `GET /api/records/{record_id}` | Fetch single record by ID |
| READ ALL | `GET /api/records/` | Fetch all records for local_user |
| UPDATE | `PUT /api/records/{record_id}` | Update report_date or record_type manually |
| DELETE | `DELETE /api/records/{record_id}` | Soft delete (mark is_deleted=True, never hard-delete health data) |

**Validation Rules:**
- `record_type` must be one of the defined Enum values — raise `InvalidRecordTypeError` if not
- `report_date` must not be in the future — raise `FutureDateError`
- File size limit: max 10MB per upload — raise `FileSizeLimitError`
- Accepted MIME types: `application/pdf`, `image/jpeg`, `image/png` — raise `UnsupportedFileTypeError`
- `raw_text` cannot be empty string after processing — raise `OCRExtractionError`

---

### 2.2 `ClinicalParameter` Class

```
Class: ClinicalParameter
Responsibility: Represents a single extracted clinical value from a health record (one record can have many parameters)

Attributes:
  - param_id: str (UUID4)
  - record_id: str (FK to HealthRecord)
  - param_name: str (e.g. "HbA1c", "Cholesterol", "Hemoglobin", "Blood Pressure Systolic")
  - value: float
  - unit: str (e.g. "%", "mg/dL", "g/dL", "mmHg")
  - reference_range_min: Optional[float]
  - reference_range_max: Optional[float]
  - report_date: datetime (inherited from parent HealthRecord)
  - status: Enum["NORMAL", "LOW", "HIGH", "CRITICAL"] (auto-computed in validate())
  - anomaly_score: Optional[float] (set by Trend Agent after time-series analysis)

Methods:
  - validate(): Computes status based on value vs reference_range, raises MissingReferenceRangeWarning if ranges are None
  - compute_status(): Returns "NORMAL"/"LOW"/"HIGH"/"CRITICAL" using threshold logic
  - to_dict() / from_dict()
```

**CRUD Operations for ClinicalParameter:**
| Operation | Endpoint | Description |
|-----------|----------|-------------|
| CREATE | Auto — created by Ingestion Agent post-OCR | Not directly user-facing |
| READ | `GET /api/params/{param_name}` | Get all historical values for a parameter (for timeline chart) |
| READ ALL | `GET /api/params/` | Get all parameters across all records |
| UPDATE | `PUT /api/params/{param_id}` | Allow manual correction of extracted value |
| DELETE | Cascades with parent HealthRecord soft-delete | — |

**Validation Rules:**
- `value` must be a positive float — raise `InvalidParameterValueError`
- `unit` must not be empty string — raise `MissingUnitError`
- If `value > reference_range_max * 2`, auto-set status to "CRITICAL"
- `param_name` must match a known parameter from the `SUPPORTED_PARAMETERS` config list

---

### 2.3 `RiskScore` Class

```
Class: RiskScore
Responsibility: Stores the computed overall and per-parameter risk scores for a user at a point in time

Attributes:
  - score_id: str (UUID4)
  - user_id: str
  - computed_at: datetime
  - overall_risk: float (0.0 to 1.0)
  - risk_level: Enum["LOW", "MODERATE", "HIGH", "CRITICAL"]
  - contributing_factors: list[dict] (list of {param_name, value, weight, contribution})
  - recommendations: list[str] (generated by Doctor-Prep Agent)
  - version: int (increments each time risk is recomputed)

Methods:
  - validate(): overall_risk must be between 0.0 and 1.0, contributing_factors must not be empty
  - to_dict() / from_dict()
  - compute_risk_level(): Converts float score to Enum label using thresholds
```

**Threshold Logic (Rule-Based Engine for Phase 1):**
```
0.0 - 0.29  → LOW
0.30 - 0.59 → MODERATE
0.60 - 0.79 → HIGH
0.80 - 1.0  → CRITICAL
```

---

### 2.4 `Reminder` Class

```
Class: Reminder
Responsibility: Tracks medication schedules, refill timing, and follow-up test due-dates

Attributes:
  - reminder_id: str (UUID4)
  - user_id: str
  - reminder_type: Enum["MEDICATION", "TEST_DUE", "DOCTOR_VISIT", "REFILL"]
  - title: str (e.g. "Take Metformin 500mg")
  - due_date: datetime
  - recurrence: Enum["NONE", "DAILY", "WEEKLY", "MONTHLY"]
  - is_active: bool
  - created_from_record_id: Optional[str] (FK to HealthRecord if auto-generated)
  - is_acknowledged: bool

Methods:
  - validate(): due_date must not be in past for new reminders, title must not be empty
  - is_due_today(): Returns bool
  - to_dict() / from_dict()
```

**CRUD Operations for Reminder:**
| Operation | Endpoint | Description |
|-----------|----------|-------------|
| CREATE | `POST /api/reminders/` | Manual or auto-created by Reminder Agent |
| READ | `GET /api/reminders/` | Get all active reminders |
| UPDATE | `PUT /api/reminders/{reminder_id}` | Edit title, due_date, recurrence |
| DELETE | `DELETE /api/reminders/{reminder_id}` | Hard delete (user-initiated) |
| ACK | `PATCH /api/reminders/{reminder_id}/ack` | Mark as acknowledged |

**Validation Rules:**
- `title` min length: 3 characters — raise `EmptyReminderTitleError`
- `due_date` cannot be more than 2 years in the future — raise `InvalidDueDateError`
- `recurrence` must be a valid Enum value — raise `InvalidRecurrenceError`

---

### 2.5 `DoctorReport` Class

```
Class: DoctorReport
Responsibility: Stores the AI-generated pre-visit summary for the user

Attributes:
  - report_id: str (UUID4)
  - user_id: str
  - generated_at: datetime
  - report_content: str (full markdown text of the summary)
  - pdf_path: Optional[str] (path to exported PDF if user downloads)
  - records_included: list[str] (list of record_ids used to generate this report)
  - share_token: Optional[str]
  - share_expires_at: Optional[datetime]

Methods:
  - validate(): report_content must not be empty, records_included must have at least 1 item
  - generate_share_token(expiry_hours: int)
  - is_share_valid()
  - to_dict() / from_dict()
```

---

## 3. Feature Modules

---

### Feature 1: Record Ingestion & OCR Pipeline

**Description:** User uploads a PDF or image (or enters text manually). The system extracts structured clinical data from raw text using OCR + regex/NLP rules.

**Steps:**
1. User uploads file via React drag-and-drop UI
2. File is validated (size, type)
3. File is AES-256 encrypted and saved to `/data/records/encrypted/`
4. Ingestion Agent is triggered (LangGraph node)
5. OCR runs (Tesseract for PDFs, EasyOCR for images)
6. Raw text passed to entity-extraction module (regex + Groq llama-3.3-70b for complex parsing)
7. `ClinicalParameter` objects created for each extracted value
8. `HealthRecord.is_processed` set to `True`
9. Frontend notified via polling or WebSocket

**Validation at each step:**
- File upload: MIME type + size check before OCR runs
- OCR output: If `len(raw_text) < 20`, flag as `OCRExtractionError` and prompt manual entry
- Entity extraction: Each parameter validated via `ClinicalParameter.validate()` before save
- Manual entry: All fields validated on frontend (React form validation) + backend re-validation

---

### Feature 2: Health Timeline (Trend Visualization)

**Description:** Visual chart showing a user's lab values over time. Color-coded by status (green=normal, yellow=high, red=critical).

**Steps:**
1. `GET /api/params/{param_name}` returns all historical values sorted by `report_date`
2. Frontend renders a Recharts line chart (date on X-axis, value on Y-axis)
3. Reference range rendered as a shaded band
4. Anomaly points (flagged by Trend Agent) rendered as red dots

**Supported Parameters (Phase 1):**
```
HbA1c, Fasting Blood Sugar, Total Cholesterol, LDL, HDL, Triglycerides,
Hemoglobin, Creatinine, eGFR, Blood Pressure (Systolic/Diastolic),
TSH, Vitamin D, Vitamin B12, Uric Acid
```

**Validation:**
- If fewer than 2 data points exist for a parameter, show "Not enough data for trend — add more records"
- Chart axis must auto-scale based on reference range, not raw value extremes

---

### Feature 3: Anomaly Detection & Risk Scoring

**Description:** The Trend Agent runs a rule-based scoring engine (Phase 1) on all ClinicalParameter values and computes an overall `RiskScore`.

**Rule-Based Scoring Logic:**
```
For each ClinicalParameter:
  if status == "CRITICAL": contribution = 0.25
  if status == "HIGH":     contribution = 0.15
  if status == "LOW":      contribution = 0.10
  if status == "NORMAL":   contribution = 0.0

overall_risk = min(sum(all contributions), 1.0)
risk_level = compute_risk_level(overall_risk)
```

**Risk Dashboard UI:**
- A circular progress gauge showing overall_risk (0–100%)
- List of contributing factors sorted by weight
- Colored badges per factor (green/yellow/orange/red)

**Validation:**
- Risk recomputed every time a new record is ingested
- `RiskScore.validate()` runs before every save
- If no ClinicalParameters exist, risk score is not computed — show "Upload your first report to see your health score"

---

### Feature 4: Reminder & Medication Tracker

**Description:** Users can create medication/follow-up reminders manually, or the Reminder Agent auto-creates them from prescription records.

**Auto-creation Logic:**
```
If record_type == "PRESCRIPTION":
  Extract medicine names + dosage instructions
  For each medicine: create Reminder(type=MEDICATION, recurrence=DAILY)
  For follow-up: create Reminder(type=DOCTOR_VISIT, due_date=extracted_date)
```

**UI:**
- A simple card-list of upcoming reminders (sorted by due_date)
- Toggle to mark as acknowledged
- Edit/delete per reminder

---

### Feature 5: Doctor-Prep Report Generation

**Description:** One-click generation of a clean pre-visit health summary using the Doctor-Prep Agent. Output is a downloadable PDF.

**Report Structure:**
```
1. Patient Summary (name, age if entered, report date range)
2. Key Clinical Parameters — current vs last reading vs reference range
3. Flagged Concerns (HIGH/CRITICAL parameters highlighted)
4. Active Medications (from Reminder tracker)
5. AI-Generated Questions to Ask Your Doctor (Groq llama-3.3-70b)
6. Recent Trend Analysis (1-paragraph summary of trends)
```

**Validation:**
- At least 1 processed HealthRecord must exist before generation — else show error
- PDF export uses ReportLab — validate that PDF is non-empty after generation
- Report content must be > 200 characters — else retry generation once

---

### Feature 6: Secure Share Link

**Description:** User can share a DoctorReport or HealthRecord with a doctor via a time-limited link.

**Logic:**
```
generate_share_token(expiry_hours=24):
  token = JWT signed with SECRET_KEY
  payload = {record_id/report_id, exp: now + expiry_hours}
  save share_token + share_expires_at to entity
  return /share/{token}
```

**Validation:**
- `is_share_valid()` checked on every `/share/{token}` request
- Expired tokens return `410 Gone` — not `404`
- Token cannot be regenerated for the same record within 1 hour of last generation

---

## 4. Error Handling Strategy

All custom exceptions must inherit from a base `ArogyaError`:

```python
class ArogyaError(Exception): pass
class InvalidRecordTypeError(ArogyaError): pass
class FutureDateError(ArogyaError): pass
class FileSizeLimitError(ArogyaError): pass
class UnsupportedFileTypeError(ArogyaError): pass
class OCRExtractionError(ArogyaError): pass
class InvalidParameterValueError(ArogyaError): pass
class MissingUnitError(ArogyaError): pass
class EmptyReminderTitleError(ArogyaError): pass
class InvalidDueDateError(ArogyaError): pass
class InvalidRecurrenceError(ArogyaError): pass
class ShareTokenExpiredError(ArogyaError): pass
class InsufficientDataError(ArogyaError): pass
```

All FastAPI endpoints must return structured error responses:
```json
{
  "error": "InvalidRecordTypeError",
  "message": "record_type must be one of LAB_REPORT, PRESCRIPTION, DOCTOR_NOTE, IMAGING, MANUAL_ENTRY",
  "field": "record_type"
}
```

---

## 5. Frontend Component Map

| Component | Route | Responsibility |
|-----------|-------|----------------|
| `UploadPage` | `/upload` | Drag-and-drop file upload + manual entry form |
| `DashboardPage` | `/` | Risk score gauge + recent records + upcoming reminders |
| `TimelinePage` | `/timeline` | Parameter selector + Recharts line chart |
| `RemindersPage` | `/reminders` | CRUD for reminders |
| `DoctorReportPage` | `/report` | Generate + preview + download PDF |
| `RecordDetailPage` | `/records/:id` | View extracted data from a single record |
| `SharePage` | `/share/:token` | Public (read-only) view for shared records/reports |

---

*End of FEATURES.md — Phase 1*
