"""
Shared test fixtures.

The os.environ assignments MUST come before any backend imports because
pydantic-settings reads environment variables at class instantiation time
(i.e. on first import of backend.config). Setting them here ensures the
app starts cleanly with a test SECRET_KEY and an in-memory SQLite URL.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-purposes-only-abc123")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import APIRouter, Depends

from backend.main import app
from backend.database import get_db, Base
from backend.auth import get_current_admin_user

# ---------------------------------------------------------------------------
# Test-only admin endpoint
#
# Registers a single route used by the 1d admin guard tests. Adding it here
# (rather than in main.py) keeps production code clean. The route persists
# for the full pytest process, which is fine — other tests simply don't call it.
# ---------------------------------------------------------------------------
_test_router = APIRouter(tags=["test-only"])


@_test_router.get("/test/admin-only")
async def _admin_only_endpoint(user=Depends(get_current_admin_user)):
    return {"message": "admin access granted", "username": user.username}


app.include_router(_test_router)

# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """
    Fresh in-memory SQLite database for every test.

    Creates all tables via SQLAlchemy metadata (bypasses Alembic migrations,
    which is correct for unit tests — we test app logic, not migrations).
    Drops all tables after the test completes to guarantee isolation.
    """
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """
    AsyncClient pointed at the FastAPI app with the DB dependency overridden.

    Using httpx.AsyncClient with ASGITransport means the lifespan handler
    does NOT run — the scheduler background task never starts, and table
    creation is handled by the db_session fixture above.
    """
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
