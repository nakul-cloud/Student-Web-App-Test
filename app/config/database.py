import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config.settings import settings
from app.utils.logger import logger

if os.environ.get("VERCEL"):
    engine = create_async_engine(
        settings.database_url,
        echo=(settings.env == "development"),
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        settings.database_url,
        echo=(settings.env == "development"),
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db_session():
    """Dependency for providing database session with error handling."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"[Database] Session error occurred: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
