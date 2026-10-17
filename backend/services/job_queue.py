"""
ArogyaMitra AI - Phase 4 Background Job Queue System
Async-native job dispatcher and queue worker interface.
Per PHASE4_IMPLEMENTATION.md F4.
"""

import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from backend.core.logger import logger
from backend.exceptions.arogya_errors import JobNotFoundError


class JobQueue:
    """
    In-process and Redis-compatible asynchronous background job runner.
    Provides idempotency, state tracking, and failure handling.
    """

    _handlers: Dict[str, Callable] = {}
    _in_memory_jobs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_handler(cls, job_type: str, handler: Callable):
        """Registers an asynchronous job processing function."""
        cls._handlers[job_type] = handler

    @classmethod
    async def enqueue(
        cls,
        job_type: str,
        owner_user_id: str,
        profile_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> str:
        """Enqueues a job for background processing."""
        # 1. Check idempotency
        if idempotency_key:
            for j_id, j_data in cls._in_memory_jobs.items():
                if j_data.get("idempotency_key") == idempotency_key:
                    logger.info(f"[JobQueue] Deduplicated job with idempotency key: {idempotency_key}")
                    return j_id

        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "type": job_type,
            "owner_user_id": owner_user_id,
            "profile_id": profile_id,
            "status": "QUEUED",
            "attempts": 0,
            "max_attempts": 3,
            "payload": payload or {},
            "idempotency_key": idempotency_key,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "last_error": None
        }
        cls._in_memory_jobs[job_id] = job_data
        
        # Fire async execution task
        asyncio.create_task(cls._execute_job(job_id))
        return job_id

    @classmethod
    async def _execute_job(cls, job_id: str):
        job = cls._in_memory_jobs.get(job_id)
        if not job:
            return

        job_type = job["type"]
        handler = cls._handlers.get(job_type)
        if not handler:
            logger.error(f"[JobQueue] No handler registered for job type: {job_type}")
            job["status"] = "FAILED"
            job["last_error"] = f"No handler registered for {job_type}"
            job["finished_at"] = datetime.now(timezone.utc).isoformat()
            return

        job["status"] = "RUNNING"
        job["attempts"] += 1

        try:
            # Execute worker handler
            await handler(job)
            job["status"] = "COMPLETED"
            job["finished_at"] = datetime.now(timezone.utc).isoformat()
            logger.info(f"[JobQueue] Job {job_id} ({job_type}) completed successfully")
        except Exception as e:
            logger.error(f"[JobQueue] Job {job_id} ({job_type}) failed attempt {job['attempts']}: {e}")
            job["last_error"] = str(e)
            if job["attempts"] >= job["max_attempts"]:
                job["status"] = "DEAD_LETTER"
                job["finished_at"] = datetime.now(timezone.utc).isoformat()
            else:
                job["status"] = "QUEUED"
                # Exponential backoff retry
                await asyncio.sleep(2 ** job["attempts"])
                asyncio.create_task(cls._execute_job(job_id))

    @classmethod
    def get_job_status(cls, job_id: str, owner_user_id: str) -> Dict[str, Any]:
        """Returns owner-scoped job details."""
        job = cls._in_memory_jobs.get(job_id)
        if not job or job.get("owner_user_id") != owner_user_id:
            raise JobNotFoundError("Job not found or access denied")
        return job
