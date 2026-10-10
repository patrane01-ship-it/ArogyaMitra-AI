from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.doctor_access import DoctorAccess
from backend.exceptions.arogya_errors import WorkspaceNotFoundError, WorkspaceAccessExpiredError

class DoctorAccessRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, access: DoctorAccess) -> DoctorAccess:
        access.validate()
        self.db.add(access)
        await self.db.flush()
        await self.db.refresh(access)
        return access

    async def get_by_token(self, token: str) -> DoctorAccess:
        result = await self.db.execute(
            select(DoctorAccess).where(DoctorAccess.access_token == token)
        )
        access = result.scalars().first()
        if not access:
            raise WorkspaceNotFoundError("Workspace not found")
        
        if access.is_expired():
            raise WorkspaceAccessExpiredError("Workspace access has expired")
            
        return access

    async def get_by_id(self, access_id: str, owner_user_id: str) -> DoctorAccess:
        result = await self.db.execute(
            select(DoctorAccess)
            .where(DoctorAccess.access_id == access_id)
            .where(DoctorAccess.granted_by_user_id == owner_user_id)
        )
        access = result.scalars().first()
        if not access:
            raise WorkspaceNotFoundError("Workspace not found")
        return access

    async def list_for_profile(self, profile_id: str, owner_user_id: str) -> List[DoctorAccess]:
        result = await self.db.execute(
            select(DoctorAccess)
            .where(DoctorAccess.patient_profile_id == profile_id)
            .where(DoctorAccess.granted_by_user_id == owner_user_id)
            .order_by(DoctorAccess.granted_at.desc())
        )
        return list(result.scalars().all())

    async def record_access(self, access: DoctorAccess) -> None:
        access.last_accessed_at = datetime.now(timezone.utc)
        access.access_count += 1
        await self.db.flush()

    async def revoke(self, access_id: str, owner_user_id: str) -> None:
        access = await self.get_by_id(access_id, owner_user_id)
        access.is_active = False
        await self.db.flush()

    async def count_active_for_user(self, owner_user_id: str) -> int:
        result = await self.db.execute(
            select(func.count(DoctorAccess.access_id))
            .where(DoctorAccess.granted_by_user_id == owner_user_id)
            .where(DoctorAccess.is_active == True)
            .where(DoctorAccess.expires_at > datetime.now(timezone.utc))
        )
        return result.scalar_one_or_none() or 0
