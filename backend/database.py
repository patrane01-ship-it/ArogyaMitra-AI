"""
ArogyaMitra AI - Database Configuration
SQLAlchemy async engine setup for PostgreSQL or SQLite.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.config import settings

Base = declarative_base()

_async_engine = None
_async_session_factory = None


def get_async_engine():
    """Get or create the async SQLAlchemy engine."""
    global _async_engine
    if _async_engine is None:
        # Convert postgresql:// to postgresql+asyncpg:// for the async driver
        # Convert sqlite:// to sqlite+aiosqlite:// for async support
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            async_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
            _async_engine = create_async_engine(
                async_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.DEBUG,
            )
        elif db_url.startswith("sqlite://"):
            async_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
            _async_engine = create_async_engine(
                async_url,
                echo=settings.DEBUG,
            )
        else:
            raise ValueError(f"Unsupported DATABASE_URL scheme: {db_url}")
    return _async_engine


def get_async_session_factory():
    """Get or create the async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_async_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _async_session_factory


async def get_db():
    """Dependency for getting async DB sessions in FastAPI routes."""
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
