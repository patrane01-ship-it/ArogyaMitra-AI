from typing import List, Optional
from datetime import datetime, timezone
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from backend.models.api_key import APIKey
from backend.exceptions.arogya_errors import APIKeyNotFoundError, DatabaseError
from backend.core.logger import logger

class APIKeyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, api_key: APIKey) -> APIKey:
        try:
            api_key.validate()
            self.db.add(api_key)
            await self.db.flush()
            await self.db.refresh(api_key)
            return api_key
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[APIKeyRepo] Error creating API key: {e}")
            raise DatabaseError("Failed to create API key")

    async def get_by_hash(self, plain_key: str) -> APIKey:
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        stmt = select(APIKey).where(
            APIKey.api_key_hash == key_hash,
            APIKey.is_active == True
        )
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()
        if not api_key:
            raise APIKeyNotFoundError("API key not found or inactive")
        return api_key

    async def list_for_user(self, user_id: str) -> List[APIKey]:
        stmt = select(APIKey).where(
            APIKey.user_id == user_id
        ).order_by(APIKey.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def revoke(self, key_id: str, user_id: str) -> None:
        stmt = select(APIKey).where(
            APIKey.key_id == key_id,
            APIKey.user_id == user_id
        )
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()
        if not api_key:
            raise APIKeyNotFoundError("API key not found")
        
        api_key.is_active = False
        try:
            await self.db.flush()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[APIKeyRepo] Error revoking API key {key_id}: {e}")
            raise DatabaseError("Failed to revoke API key")

    async def update_last_used(self, key_id: str) -> None:
        stmt = (
            update(APIKey)
            .where(APIKey.key_id == key_id)
            .values(last_used_at=datetime.now(timezone.utc))
        )
        try:
            await self.db.execute(stmt)
            await self.db.flush()
        except Exception as e:
            logger.error(f"[APIKeyRepo] Error updating last_used_at for API key {key_id}: {e}")

    async def log_audit(self, key_id: str, endpoint: str, status_code: int, profile_id: Optional[str] = None) -> None:
        stmt = text("""
            INSERT INTO api_key_audit (key_id, endpoint, status_code, profile_id, accessed_at)
            VALUES (:key_id, :endpoint, :status_code, :profile_id, :accessed_at)
        """)
        try:
            await self.db.execute(stmt, {
                "key_id": key_id,
                "endpoint": endpoint,
                "status_code": status_code,
                "profile_id": profile_id,
                "accessed_at": datetime.now(timezone.utc)
            })
            await self.db.flush()
        except Exception as e:
            logger.error(f"[APIKeyRepo] Error logging audit for API key {key_id}: {e}")
