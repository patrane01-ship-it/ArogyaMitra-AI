"""
ArogyaMitra AI - User Repository
Data access layer for User entity with authentication helpers.
Per FEATURES_PHASE2.md §2.1 and TECH_STACK_PHASE2.md §3.
"""

from typing import Optional, List
from datetime import datetime, date, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from backend.models.user import User
from backend.core.logger import logger
from backend.exceptions.arogya_errors import (
    ArogyaError,
    DatabaseError,
    EmailAlreadyExistsError,
)


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        """Create a new registered user."""
        try:
            user.validate()
            self.db.add(user)
            await self.db.flush()
            return user
        except IntegrityError:
            await self.db.rollback()
            raise EmailAlreadyExistsError(f"User with email {user.email} already exists")
        except ArogyaError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:User] Error creating user: {e}")
            raise DatabaseError("Failed to register user")

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Fetch user by ID."""
        try:
            stmt = select(User).where(User.user_id == user_id, User.is_active.is_(True))
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:User] Error fetching user by ID {user_id}: {e}")
            raise DatabaseError("Database error during user lookup")

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email (case-insensitive)."""
        try:
            stmt = select(User).where(User.email == email.strip().lower(), User.is_active.is_(True))
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[Repo:User] Error fetching user by email: {e}")
            raise DatabaseError("Database error during user lookup")

    async def update_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        gender: Optional[str] = None,
    ) -> Optional[User]:
        """Update personal profile fields."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        if full_name is not None:
            user.full_name = full_name
        if date_of_birth is not None:
            user.date_of_birth = date_of_birth
        if gender is not None:
            user.gender = gender

        try:
            user.validate()
            await self.db.flush()
            return user
        except ArogyaError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Repo:User] Error updating profile for {user_id}: {e}")
            raise DatabaseError("Failed to update user profile")

    async def update_last_login(self, user_id: str):
        """Update last login timestamp."""
        user = await self.get_by_id(user_id)
        if user:
            user.last_login = datetime.now(timezone.utc)
            await self.db.flush()

    async def set_refresh_token_hash(self, user_id: str, token_hash: Optional[str]):
        """Store or clear refresh token hash."""
        user = await self.get_by_id(user_id)
        if user:
            user.refresh_token_hash = token_hash
            await self.db.flush()

    async def deactivate(self, user_id: str) -> bool:
        """Soft deactivate user account."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        user.is_active = False
        user.refresh_token_hash = None
        await self.db.flush()
        return True
