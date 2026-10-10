"""
ArogyaMitra AI - Wearable Repository (Phase 3)
Database access for wearable readings.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from backend.models.wearable_reading import WearableReading
from backend.core.cache import ArogyaCache
from backend.exceptions.arogya_errors import RecordNotFoundError

class WearableRepository:
    def __init__(self, db: AsyncSession, cache: ArogyaCache):
        self.db = db
        self.cache = cache

    async def bulk_upsert(self, readings: List[WearableReading]) -> int:
        """Bulk insert wearable readings if they don't already exist."""
        inserted_count = 0
        for reading in readings:
            stmt = select(WearableReading).where(
                and_(
                    WearableReading.profile_id == reading.profile_id,
                    WearableReading.source == reading.source,
                    WearableReading.metric_type == reading.metric_type,
                    WearableReading.recorded_at == reading.recorded_at
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            if not existing:
                self.db.add(reading)
                inserted_count += 1
        
        if inserted_count > 0:
            await self.db.commit()
            
        return inserted_count

    async def list_for_profile(self, profile_id: str, metric_type: Optional[str] = None, limit: int = 100) -> List[WearableReading]:
        stmt = select(WearableReading).where(WearableReading.profile_id == profile_id)
        if metric_type:
            stmt = stmt.where(WearableReading.metric_type == metric_type)
        stmt = stmt.order_by(WearableReading.recorded_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, reading_id: str, profile_id: str) -> WearableReading:
        stmt = select(WearableReading).where(
            and_(
                WearableReading.reading_id == reading_id,
                WearableReading.profile_id == profile_id
            )
        )
        result = await self.db.execute(stmt)
        reading = result.scalar_one_or_none()
        if not reading:
            raise RecordNotFoundError("Wearable reading not found")
        return reading

    async def delete(self, reading_id: str, profile_id: str) -> None:
        stmt = delete(WearableReading).where(
            and_(
                WearableReading.reading_id == reading_id,
                WearableReading.profile_id == profile_id
            )
        )
        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            raise RecordNotFoundError("Wearable reading not found")
        await self.db.commit()

    async def store_wearable_token(self, profile_id: str, source: str, access_encrypted: str, refresh_encrypted: str) -> None:
        await self.cache.set(f"wearable_token:{profile_id}:{source}", access_encrypted)
        await self.cache.set(f"wearable_refresh:{profile_id}:{source}", refresh_encrypted)
        # Clear any reconnect flag
        await self.cache.delete(f"wearable_needs_reconnect:{profile_id}:{source}")

    async def get_wearable_token(self, profile_id: str, source: str) -> Optional[str]:
        return await self.cache.get(f"wearable_token:{profile_id}:{source}")

    async def mark_needs_reconnect(self, profile_id: str, source: str) -> None:
        await self.cache.set(f"wearable_needs_reconnect:{profile_id}:{source}", "1", ttl=86400)
