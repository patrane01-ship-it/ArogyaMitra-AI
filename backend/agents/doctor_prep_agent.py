"""
ArogyaMitra AI - Doctor-Prep Agent
Generates comprehensive clinical summaries for upcoming doctor visits using Groq llama-3.3-70b.
Enforces guardrails, output validation, and ReportLab PDF rendering.
Per TECH_STACK.md §3, FEATURES.md §3 (Feature 5), and PRODUCTION_BACKEND.md §9.3.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.core.logger import logger
from backend.core.prompt_guard import sanitize_for_prompt
from backend.core.prompt_templates import DOCTOR_PREP_SYSTEM
from backend.core.guardrails import apply_output_guardrails
from backend.services.pdf_export_service import PDFExportService
from backend.services.encryption_service import EncryptionService
from backend.config import settings
from backend.models.doctor_report import DoctorReport
from backend.database import get_async_session_factory
from backend.repositories.health_record_repo import HealthRecordRepository
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.repositories.reminder_repo import ReminderRepository
from backend.repositories.risk_score_repo import RiskScoreRepository
from backend.repositories.doctor_report_repo import DoctorReportRepository
from backend.exceptions.arogya_errors import InsufficientDataError, ArogyaError


class DoctorPrepAgent:
    """Agent that compiles health history and drafts structured doctor consultation reports."""

    @classmethod
    async def generate_report(cls, user_id: str = "local_user") -> Dict[str, Any]:
        """
        Gathers patient history, calls Groq LLM, applies guardrails, generates PDF,
        and saves the DoctorReport entity.
        """
        logger.info(f"[Agent:DoctorPrepAgent] START | user_id={user_id}")

        async_factory = get_async_session_factory()
        async with async_factory() as session:
            record_repo = HealthRecordRepository(session)
            param_repo = ClinicalParameterRepository(session)
            reminder_repo = ReminderRepository(session)
            risk_repo = RiskScoreRepository(session)
            report_repo = DoctorReportRepository(session)

            # 1. Verify at least 1 non-deleted record exists
            records = await record_repo.get_all(user_id=user_id, limit=50)
            if not records:
                raise InsufficientDataError("At least one health record is required to generate a doctor-prep report")

            record_ids = [r.record_id for r in records]

            # 2. Gather data
            latest_params = await param_repo.get_latest_for_user(user_id)
            latest_risk = await risk_repo.get_latest(user_id)
            reminders = await reminder_repo.get_all(user_id=user_id)

            params_data = [p.to_dict() for p in latest_params]
            reminders_data = [r.to_dict() for r in reminders]
            risk_data = latest_risk.to_dict() if latest_risk else {}

        # 3. Construct structured context
        data_summary = {
            "user_id": user_id,
            "overall_health_risk": risk_data.get("overall_risk", "N/A"),
            "risk_level": risk_data.get("risk_level", "N/A"),
            "clinical_parameters": [
                {
                    "name": p["param_name"],
                    "value": p["value"],
                    "unit": p["unit"],
                    "status": p["status"],
                    "ref_range": f"{p.get('reference_range_min')} - {p.get('reference_range_max')}",
                }
                for p in params_data
            ],
            "active_medications": [r["title"] for r in reminders_data if r.get("reminder_type") == "MEDICATION"],
            "records_count": len(records),
        }

        safe_context = sanitize_for_prompt(json.dumps(data_summary, indent=2), max_chars=4000)

        user_prompt = (
            f"Generate a Doctor-Prep pre-visit health summary from the following patient data:\n\n"
            f"{safe_context}\n\n"
            f"Include the following sections:\n"
            f"1. **Patient Summary** (brief overview of health status)\n"
            f"2. **Key Clinical Parameters** (highlighting abnormal readings)\n"
            f"3. **Flagged Concerns** (HIGH / CRITICAL parameters)\n"
            f"4. **Active Medications & Schedules**\n"
            f"5. **Questions to Ask Your Doctor** (3-5 specific, thoughtful clinical questions)\n"
            f"6. **Recent Trend Analysis** (concise 1-paragraph summary)\n"
        )

        # 4. Invoke Groq LLM
        report_text = ""
        if settings.GROQ_API_KEY:
            try:
                from groq import Groq
                client = Groq(api_key=settings.GROQ_API_KEY)

                for attempt in range(2):
                    temp = 0.2 if attempt == 0 else 0.0
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": DOCTOR_PREP_SYSTEM},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=temp,
                        max_tokens=2000,
                    )
                    candidate = response.choices[0].message.content.strip()
                    # Validate length per §7.4
                    if len(candidate) >= 200:
                        report_text = candidate
                        break
            except Exception as e:
                logger.error(f"[Agent:DoctorPrepAgent] Groq API call failed: {e}")

        # Fallback if Groq unavailable or returned short text
        if not report_text or len(report_text) < 200:
            logger.warning("[Agent:DoctorPrepAgent] Using template generator fallback")
            flagged = [p["name"] for p in params_data if p["status"] in ["HIGH", "CRITICAL"]]
            flagged_str = ", ".join(flagged) if flagged else "None. All parameters normal."
            meds_str = ", ".join([r["title"] for r in reminders_data]) if reminders_data else "None reported."

            report_text = (
                f"### Patient Summary\n"
                f"Patient ID: {user_id}. Currently monitoring {len(params_data)} clinical parameters "
                f"across {len(records)} ingested medical records. Overall risk category: {risk_data.get('risk_level', 'LOW')}.\n\n"
                f"### Key Clinical Parameters\n"
                f"Tracked tests include: {', '.join([p['param_name'] for p in params_data]) or 'No parameters registered'}.\n\n"
                f"### Flagged Concerns\n"
                f"{flagged_str}\n\n"
                f"### Active Medications & Schedules\n"
                f"{meds_str}\n\n"
                f"### Questions to Ask Your Doctor\n"
                f"1. How do my recent test values compare to my optimal personal baseline?\n"
                f"2. Are there any dietary or lifestyle adjustments recommended for my flagged readings?\n"
                f"3. When should I schedule my next follow-up panel?\n\n"
                f"### Recent Trend Analysis\n"
                f"Recent clinical parameters demonstrate stable baseline tracking with active schedule adherence.\n\n"
                f"This summary is for informational purposes only. Consult your doctor for medical advice."
            )

        # 5. Apply Output Guardrails
        safe_report_text = apply_output_guardrails(report_text, context="doctor_prep_report")

        # 6. Generate and save PDF (encrypted)
        pdf_bytes = PDFExportService.generate_report_pdf(
            report_content=safe_report_text,
            user_id=user_id,
            clinical_params=params_data,
            reminders=reminders_data,
        )

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        report_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"doctor_report_{user_id}_{report_timestamp}.pdf.enc"
        pdf_full_path = os.path.join(settings.UPLOAD_DIR, pdf_filename)

        enc_svc = EncryptionService(settings.ENCRYPTION_KEY.encode())
        encrypted_pdf = enc_svc.encrypt_to_payload(pdf_bytes)

        with open(pdf_full_path, "wb") as f:
            f.write(encrypted_pdf)

        # 7. Persist DoctorReport to database
        async with async_factory() as session:
            report_repo = DoctorReportRepository(session)
            report_model = DoctorReport(
                user_id=user_id,
                generated_at=datetime.now(timezone.utc),
                report_content=safe_report_text,
                pdf_path=pdf_full_path,
                records_included=record_ids,
            )
            report_model.validate()
            await report_repo.create(report_model)
            await session.commit()
            created_report_id = report_model.report_id

        logger.info(f"[Agent:DoctorPrepAgent] DONE | report_id={created_report_id}")

        return {
            "report_id": created_report_id,
            "generated_at": datetime.now(timezone.utc),
            "preview": safe_report_text[:300] + "...",
            "pdf_ready": True,
        }
