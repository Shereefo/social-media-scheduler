# File: upgrade_datetime_columns.py

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.sql import text
from backend.config import settings

async def upgrade_database():
    # Create connection to your database
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    # Create a session
    async with engine.begin() as conn:
        # Alter the column to support timezone
        await conn.execute(
            text(
                'ALTER TABLE users ALTER COLUMN tiktok_token_expires_at '
                'TYPE TIMESTAMP WITH TIME ZONE'
            )
        )
        print(
            "Successfully updated tiktok_token_expires_at column "
            "to TIMESTAMP WITH TIME ZONE"
        )

if __name__ == "__main__":
    asyncio.run(upgrade_database())