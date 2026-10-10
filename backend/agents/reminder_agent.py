"""
ArogyaMitra AI - Reminder Agent
LangGraph node: Parses prescriptions, extracts medications and dosage schedules,
and generates automated reminder entries.
Per TECH_STACK.md §3 and FEATURES.md §3 (Feature 4).
"""

import re
import json
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from backend.core.logger import logger
from backend.models.reminder import Reminder, ReminderType, RecurrenceType
from backend.database import get_async_session_factory
from backend.repositories.reminder_repo import ReminderRepository
from backend.config import settings
from backend.core.prompt_guard import sanitize_for_prompt


MEDICATION_REGEX = re.compile(
    r"(?:Tab|Cap|Syp|Inj|Tablet|Capsule|Syrup)?\.?\s*([A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)?)\s+(\d+(?:\.\d+)?\s*(?:mg|ml|mcg|g))",
    re.IGNORECASE
)


async def reminder_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Reminder Agent node in LangGraph state machine."""
    record_id = state.get("record_id", "")
    user_id = state.get("user_id", "local_user")
    raw_text = state.get("raw_text", "")
    record_type = state.get("record_type", "")

    logger.info(f"[Agent:ReminderAgent] START | record_id={record_id}")
    state["current_step"] = "reminder_running"

    reminders_created = []

    try:
        # 1. Regex-based medication extraction
        matches = MEDICATION_REGEX.findall(raw_text)
        detected_meds = []
        for name, dose in matches:
            clean_name = name.strip()
            if len(clean_name) >= 3 and clean_name.lower() not in ["take", "daily", "after", "before", "food"]:
                detected_meds.append(f"{clean_name} {dose.strip()}")

        # 2. LLM fallback for prescriptions if regex found nothing and Groq key available
        if not detected_meds and settings.GROQ_API_KEY and len(raw_text.strip()) > 20:
            try:
                from groq import Groq
                safe_text = sanitize_for_prompt(raw_text, max_chars=1500)
                client = Groq(api_key=settings.GROQ_API_KEY)
                resp = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Extract prescription medications and follow-up visits. "
                                "Return JSON only: {\"medications\": [str], \"follow_up_days\": int or null}"
                            )
                        },
                        {"role": "user", "content": f"Prescription text:\n{safe_text}"}
                    ],
                    temperature=0.1,
                    max_tokens=300
                )
                content = resp.choices[0].message.content.strip()
                cleaned = re.sub(r"^```(?:json)?\s*", "", content)
                cleaned = re.sub(r"\s*```$", "", cleaned).strip()
                parsed = json.loads(cleaned)
                detected_meds = parsed.get("medications", [])
            except Exception as e:
                logger.warning(f"[Agent:ReminderAgent] Groq medication extraction skipped: {e}")

        # 3. Create Reminder database records
        now = datetime.now(timezone.utc)
        models_to_save: List[Reminder] = []

        # Deduplicate
        unique_meds = list(dict.fromkeys(detected_meds))[:10]

        for med in unique_meds:
            rem = Reminder(
                user_id=user_id,
                reminder_type=ReminderType.MEDICATION.value,
                title=f"Take {med}",
                due_date=now + timedelta(hours=12),
                recurrence=RecurrenceType.DAILY.value,
                is_active=True,
                is_acknowledged=False,
                created_from_record_id=record_id,
            )
            rem.validate()
            models_to_save.append(rem)

        if models_to_save:
            async_factory = get_async_session_factory()
            async with async_factory() as session:
                rem_repo = ReminderRepository(session)
                saved_rems = await rem_repo.create_many(models_to_save)
                await session.commit()
                reminders_created = [r.to_dict() for r in saved_rems]

        state["reminders_created"] = reminders_created
        state["current_step"] = "reminder_success"
        logger.info(f"[Agent:ReminderAgent] DONE | created={len(reminders_created)}")

    except Exception as e:
        logger.exception(f"[Agent:ReminderAgent] FAIL | record_id={record_id} | {type(e).__name__}: {e}")
        state["errors"].append({"agent": "reminder", "error": "UNEXPECTED", "message": str(e)})
        state["current_step"] = "reminder_failed"

    return state
