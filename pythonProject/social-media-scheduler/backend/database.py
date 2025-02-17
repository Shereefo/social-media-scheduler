from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Database connection URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://shereef:password@db/social-media-scheduler"
)

# Create an async engine for SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False to disable logging SQL queries
)

# Create a session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Dependency to get database session
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