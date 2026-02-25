from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# Read DATABASE_URL strictly from config — no hardcoded fallback.
# If the ECS Secrets Manager injection fails, settings.DATABASE_URL
# raises a ValidationError at startup rather than connecting silently
# to a nonexistent host.
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Create session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create base class for declarative models
Base = declarative_base()


# Dependency to get DB session
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
