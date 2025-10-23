# File: upgrade_datetime_columns.py

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text
from backend.config import settings


async def upgrade_database():
    # Create connection to your database
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    # Create a session
    async with engine.begin() as conn:
        # Alter users table columns to support timezone
        await conn.execute(
            text(
                "ALTER TABLE users ALTER COLUMN tiktok_token_expires_at "
                "TYPE TIMESTAMP WITH TIME ZONE"
            )
        )
        print(
            "Successfully updated tiktok_token_expires_at column "
            "to TIMESTAMP WITH TIME ZONE"
        )

        await conn.execute(
            text(
                "ALTER TABLE users ALTER COLUMN created_at "
                "TYPE TIMESTAMP WITH TIME ZONE"
            )
        )
        print("Successfully updated users.created_at to TIMESTAMP WITH TIME ZONE")

        await conn.execute(
            text(
                "ALTER TABLE users ALTER COLUMN updated_at "
                "TYPE TIMESTAMP WITH TIME ZONE"
            )
        )
        print("Successfully updated users.updated_at to TIMESTAMP WITH TIME ZONE")

        # Alter posts table columns to support timezone
        await conn.execute(
            text(
                "ALTER TABLE posts ALTER COLUMN scheduled_time "
                "TYPE TIMESTAMP WITH TIME ZONE"
            )
        )
        print("Successfully updated posts.scheduled_time to TIMESTAMP WITH TIME ZONE")

        await conn.execute(
            text(
                "ALTER TABLE posts ALTER COLUMN created_at "
                "TYPE TIMESTAMP WITH TIME ZONE"
            )
        )
        print("Successfully updated posts.created_at to TIMESTAMP WITH TIME ZONE")

        await conn.execute(
            text(
                "ALTER TABLE posts ALTER COLUMN updated_at "
                "TYPE TIMESTAMP WITH TIME ZONE"
            )
        )
        print("Successfully updated posts.updated_at to TIMESTAMP WITH TIME ZONE")


if __name__ == "__main__":
    asyncio.run(upgrade_database())
