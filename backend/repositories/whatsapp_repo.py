"""
ArogyaMitra AI - WhatsApp Repository (Phase 3)
Per FEATURES_PHASE3.md §2.6
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.whatsapp_session import WhatsAppSession


class WhatsAppRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_phone(self, phone_number: str) -> Optional[WhatsAppSession]:
        result = await self.db.execute(
            select(WhatsAppSession).where(WhatsAppSession.phone_number == phone_number)
        )
        return result.scalars().first()

    async def get_by_user(self, user_id: str) -> Optional[WhatsAppSession]:
        result = await self.db.execute(
            select(WhatsAppSession).where(WhatsAppSession.user_id == user_id)
        )
        return result.scalars().first()

    async def create(self, session: WhatsAppSession) -> WhatsAppSession:
        session.validate()
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def update(self, session: WhatsAppSession) -> WhatsAppSession:
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_or_create(self, user_id: str, phone_number: str) -> WhatsAppSession:
        session = await self.get_by_user(user_id)
        if session:
            session.phone_number = phone_number
            await self.update(session)
            return session
        
        session = await self.get_by_phone(phone_number)
        if session:
            session.user_id = user_id
            await self.update(session)
            return session
            
        session = WhatsAppSession(user_id=user_id, phone_number=phone_number)
        return await self.create(session)
