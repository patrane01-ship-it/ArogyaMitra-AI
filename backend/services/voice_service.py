"""
ArogyaMitra AI - Voice Service (Phase 3)
Per FEATURES_PHASE3.md §2.7
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import UploadFile
import httpx
from groq import AsyncGroq

from backend.core.cache import ArogyaCache
from backend.config import Settings
from backend.core.sanitizer import sanitize_string
from backend.core.guardrails import apply_output_guardrails
from backend.exceptions.arogya_errors import (
    UnsupportedAudioFormatError,
    AudioFileTooLargeError,
    TranscriptionFailedError,
    RecordNotFoundError,
)
from backend.repositories.clinical_param_repo import ClinicalParameterRepository
from backend.repositories.reminder_repo import ReminderRepository
from backend.models.clinical_parameter import ClinicalParameter
from backend.models.reminder import Reminder
from backend.models.health_record import HealthRecord
from backend.core.logger import logger

class VoiceService:
    MAX_DURATION = 60
    MAX_SIZE = 25 * 1024 * 1024
    SUPPORTED_FORMATS = {'audio/webm', 'audio/mpeg', 'audio/mp4', 'audio/wav', 'audio/ogg'}

    def __init__(
        self,
        param_repo: ClinicalParameterRepository,
        reminder_repo: ReminderRepository,
        cache: ArogyaCache,
        settings: Settings,
    ):
        self.param_repo = param_repo
        self.reminder_repo = reminder_repo
        self.cache = cache
        self.settings = settings
        self.groq = AsyncGroq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

    async def transcribe(self, audio_file: UploadFile, profile_id: str) -> Dict[str, Any]:
        """Transcribe audio and parse intent via Groq."""
        if audio_file.content_type not in self.SUPPORTED_FORMATS:
            raise UnsupportedAudioFormatError("Unsupported audio format")

        content = await audio_file.read()
        if len(content) > self.MAX_SIZE:
            raise AudioFileTooLargeError("Audio file exceeds the 25MB limit")

        transcript = ""
        if self.settings.GROQ_API_KEY:
            try:
                # Groq API requires form data: file, model
                headers = {"Authorization": f"Bearer {self.settings.GROQ_API_KEY}"}
                files = {"file": (audio_file.filename or "audio.webm", content, audio_file.content_type)}
                data = {"model": "whisper-large-v3"}

                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=30.0
                    )
                    
                if resp.status_code == 200:
                    transcript = resp.json().get("text", "").strip()
                
                if not transcript:
                    # retry once
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/audio/transcriptions",
                            headers=headers,
                            files=files,
                            data=data,
                            timeout=30.0
                        )
                    if resp.status_code == 200:
                        transcript = resp.json().get("text", "").strip()

            except Exception as e:
                logger.error(f"[Voice] Transcription request failed: {e}")

        if not transcript:
            raise TranscriptionFailedError("Audio transcription failed")

        sanitized_transcript = sanitize_string(transcript)

        parsed_data = {"type": "UNKNOWN"}
        if self.groq:
            prompt = (
                "Extract health data from this transcript. Return JSON only with keys: "
                "type (READING|REMINDER|UNKNOWN), param_name (string), value (number|null), "
                "unit (string|null), reminder_title (string|null), reminder_date (ISO string|null)"
            )
            try:
                res = await self.groq.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": sanitized_transcript}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                parsed_json = json.loads(res.choices[0].message.content)
                expected_keys = {"type", "param_name", "value", "unit", "reminder_title", "reminder_date"}
                if all(k in parsed_json for k in expected_keys) and parsed_json["type"] in ("READING", "REMINDER", "UNKNOWN"):
                    parsed_data = parsed_json
            except Exception as e:
                logger.error(f"[Voice] Intent parsing failed: {e}")

        session_id = str(uuid.uuid4())
        cache_key = f"voice_transcript:{profile_id}:{session_id}"
        await self.cache.set(
            cache_key,
            json.dumps({"transcript": sanitized_transcript, "parsed_data": parsed_data}),
            ex=300
        )

        return {
            "session_id": session_id,
            "transcript": sanitized_transcript,
            "parsed_data": parsed_data
        }

    async def confirm_and_save(self, profile_id: str, session_id: str, confirmed_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save confirmed parsed data to DB."""
        cache_key = f"voice_transcript:{profile_id}:{session_id}"
        cached = await self.cache.get(cache_key)
        if not cached:
            raise RecordNotFoundError("Voice session not found or expired")

        data = json.loads(cached)
        final_data = confirmed_data if confirmed_data else data.get("parsed_data", {})
        
        # Apply guardrails if there's any text to check
        if final_data.get("reminder_title"):
            final_data["reminder_title"] = apply_output_guardrails(final_data["reminder_title"])

        record_type = final_data.get("type", "UNKNOWN")
        saved_id = None
        
        if record_type == "READING":
            # Create a dummy HealthRecord for the parameter
            record = HealthRecord(
                user_id=profile_id,
                record_type="MANUAL_ENTRY",
                report_date=datetime.now(timezone.utc),
                is_processed=True,
                raw_text="Voice Input"
            )
            self.param_repo.db.add(record)
            await self.param_repo.db.flush()

            param = ClinicalParameter(
                record_id=record.record_id,
                param_name=final_data.get("param_name", "Unknown"),
                value=float(final_data.get("value") or 0.0),
                unit=final_data.get("unit") or "units",
                report_date=datetime.now(timezone.utc)
            )
            await self.param_repo.create(param)
            saved_id = param.param_id

        elif record_type == "REMINDER":
            rem_date_str = final_data.get("reminder_date")
            rem_date = datetime.fromisoformat(rem_date_str) if rem_date_str else datetime.now(timezone.utc)
            rem = Reminder(
                user_id=profile_id,
                reminder_type="MEDICATION",
                title=final_data.get("reminder_title", "Voice Reminder"),
                due_date=rem_date,
                recurrence="NONE"
            )
            # Create through reminder_repo
            self.reminder_repo.db.add(rem)
            await self.reminder_repo.db.flush()
            saved_id = rem.reminder_id

        else:
            await self.cache.delete(cache_key)
            return {"saved": False, "message": "Could not parse health data from voice"}

        await self.cache.delete(cache_key)
        return {"saved": True, "type": record_type, "id": saved_id}

    async def discard(self, profile_id: str, session_id: str) -> None:
        """Discard a voice session."""
        cache_key = f"voice_transcript:{profile_id}:{session_id}"
        await self.cache.delete(cache_key)
