from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Database URL (using asyncpg driver)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://shereef:password@db/social-media-scheduler"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

# Create async session factory
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()