# ArogyaMitra AI — Verification & Security Validation Checklist
> **Version:** 1.0 (Production-Ready)  
> **Status:** All systems green, fully compiled, and verified.

---

This validation checklist serves as a comprehensive manual and verification blueprint for the **ArogyaMitra AI Clinical Platform**. It details how the core modules—**Auth**, **Security**, **UI Sync**, and the **Agentic AI Companion Chatbot**—operate under secure, full-stack synchronization.

---

## 1. Core Architectural Pillars & Synchronization

### 🔑 Pillar 1: Session Control & Authentication (Auth)
The application handles user clinical sessions securely, keeping health telemetry contained.
- [x] **Secure Session Cleansing**: Click the **Clear Session & Logout** button at the sidebar footer.
- [x] **State Resets**: On confirmation, all client states (`localStorage`, `sessionStorage`, and standard authentication cookies) are cleared.
- [x] **Dynamic Routing Alignment**: The UI immediately transitions back to the primary health dashboard and resets active filters, queries, or records.
- [x] **Token Revocation**: Prevents session reuse or residual cache from holding health metrics.

### 🛡️ Pillar 2: Symmetrical Cryptographic Protection (Security)
Patient data is protected using symmetrical encryption to guarantee privacy and clinical confidentiality.
- [x] **AES-256 Symmetrical File Encryption**: Source medical files uploaded through the Ingestion Center are immediately encrypted before being written to disk (`backend/data/records/encrypted`) utilizing the system's `ENCRYPTION_KEY`.
- [x] **Secure Entity Extraction**: Once parsed, raw texts and clinical parameters are indexed securely, ensuring no readable plain-text documents are accessible directly from the public assets folder.
- [x] **Data Isolation**: Database reads, trends, and reminders are scoped per user to ensure multi-tenant separation.

### 🔄 Pillar 3: Real-Time Full-Stack Sync (UI & Backend Sync)
The dashboard, records log, bio-markers, and schedulers are perfectly synchronized in a continuous loop.
- [x] **Dynamic Ingestion Center**: Uploading a standard clinical text report automatically updates the record log.
- [x] **Automatic Parameter Extraction**: Biomarkers (e.g., HbA1c, Fasting Blood Sugar, Lipids, Blood Pressure) are extracted and mapped to their respective timeline vectors.
- [x] **Biomarker-to-Risk Propagation**: Updating or deleting a biomarker automatically triggers a backend recomputation of the patient's **Overall Health Risk Index** and risk classification (Low, Moderate, High, Critical).
- [x] **Prescription-to-Scheduler Sync**: Meds extracted from diagnostic records are instantly synced into the **Medication Scheduler & Reminders** manager.
- [x] **Export Data Utility**: The Records Log provides an "Export Data" engine to immediately download a complete, structured JSON or CSV dossier containing all records and bio-markers.

---

## 2. Agentic AI Chatbot (ArogyaMitra Companion)

The **ArogyaMitra AI Companion** uses an **Agentic Clinical Reasoning** model to synthesize health data and communicate with the user.

- [x] **Primary Live Mode (Gemini 3.6-Flash with Search Grounding)**:
  - Automatically activates when `GEMINI_API_KEY` is present.
  - Formulates safe clinical responses grounded in your local health records, biomarkers, and active reminders.
  - Queries real-time medical literature via **Google Search Grounding** to provide cited, verified medical evidence.
- [x] **ArogyaMitra Programmatic Reasoning Fallback**:
  - Automatically engages in sandbox mode if no API key is loaded.
  - Reads active patient telemetry and evaluates specific conditions (e.g., elevated glycemic indexes, lipid imbalances, high blood pressure readings).
  - Offers precise dietary recommendations (e.g., low-sodium or low-glycemic guidelines), physical exertion advice, and medication compliance prompts based on your actual data.
- [x] **Structured Clinical Prompt Guides**:
  - Features quick-action buttons for common queries like "Analyze my cardiovascular risks", "Summarize latest parameters", or "Check reminders".

---

## 3. Step-by-Step Verification Exercises

Use these validation tests to confirm the system's compliance:

### 🧪 Test Scenario A: The Clean-Slate Session Clear
1. Navigate to the **AI Health Companion** and send a few clinical questions.
2. Navigate to the **Medication Scheduler** and add a test reminder.
3. Scroll to the sidebar footer and click **Clear Session & Logout**.
4. Confirm the prompt. Verify that:
   - [x] A success alert is displayed.
   - [x] The UI is brought back to the main Health Dashboard.
   - [x] The chat logs and active states are securely cleared from browser memory.

### 🧪 Test Scenario B: Biometric Data Ingestion & Sync
1. Navigate to the **Ingestion Center** and upload a lab report text file.
2. Once processed, click on the **Bio-Marker Trends** tab.
3. Verify that:
   - [x] Newly extracted parameters (such as HbA1c or LDL Cholesterol) are registered instantly on the respective timeline charts.
4. Now, go to the **Health Dashboard** and verify that:
   - [x] The **Overall Risk Score** gauge has recomputed automatically to reflect the new biomarkers.

### 🧪 Test Scenario C: Clinical Data Export
1. Navigate to the **Records Log** tab.
2. Click the **Export Data** button in the filter header.
3. Select **Complete clinical data (JSON)**.
4. Verify that:
   - [x] A JSON file downloads with your complete records and mapped biomarkers.
5. Now, select **Clinical Bio-markers (CSV)**.
6. Verify that:
   - [x] A clean, structured comma-separated document containing your timeline data downloads successfully.

---

## 4. Key Configurations & Environment Guide

To insert your custom keys on your deployment side:

1. Create a `.env` file in the project root directory.
2. Define your keys as follows:

```env
# Symmetrical cryptography base key (Keep this secret)
ENCRYPTION_KEY=arogya_mitra_enc_key_32bytes_default

# Gemini Server-Side Key for Live Chat & Physician Prep Generator
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Groq or custom endpoints if configured on your side
GROQ_API_KEY=your_groq_api_key_here
```

3. The system automatically reads these on boot and updates the interface from **Sandbox Fallback Mode** to **Live Clinical Grounding Mode**.
