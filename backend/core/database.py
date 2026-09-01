"""
DRISHTI-LENS Database Setup
Async SQLAlchemy engine, session factory, and Base.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from core.config import settings


# SQLite doesn't support pool_size / max_overflow — use minimal config
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    **({"pool_size": 10, "max_overflow": 20} if not _is_sqlite else {}),
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables. Called on app startup."""
    async with engine.begin() as conn:
        from models import user, patient, screening, referral, hospital, doctor, notification, officer  # noqa
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose engine. Called on app shutdown."""
    await engine.dispose()
