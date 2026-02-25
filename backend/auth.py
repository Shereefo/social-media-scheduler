import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .database import get_db
from .models import User, UserRole
from .config import settings

# Password hashing — bcrypt for passwords and refresh token hashes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme: reads Bearer token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ---------------------------------------------------------------------------
# User lookups
# ---------------------------------------------------------------------------

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# ---------------------------------------------------------------------------
# Access token
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Mint a short-lived JWT access token.

    Always embeds the caller's token_version so that revocation (logout /
    password change) is enforced on every request via get_current_user.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------

def _generate_refresh_token() -> str:
    """Return a cryptographically random opaque token (URL-safe base64)."""
    return secrets.token_urlsafe(32)


async def create_refresh_token(db: AsyncSession, user: User) -> str:
    """Generate a refresh token, store its bcrypt hash in the DB, return raw value."""
    raw = _generate_refresh_token()
    user.refresh_token_hash = pwd_context.hash(raw)
    user.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return raw


async def rotate_refresh_token(db: AsyncSession, user: User, raw_token: str) -> str:
    """Validate the presented refresh token and issue a new one (rotation).

    Raises HTTP 401 if the token is invalid or expired.
    Returns the new raw refresh token on success.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Must have a stored hash to compare against
    if not user.refresh_token_hash:
        raise credentials_exception

    # Check expiry before doing bcrypt comparison (cheap path first).
    # Normalise to UTC-aware before comparing: SQLite returns naive datetimes
    # for DateTime(timezone=True) columns; PostgreSQL returns aware ones.
    expires_at = user.refresh_token_expires_at
    if expires_at is None:
        raise credentials_exception
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        raise credentials_exception

    if not pwd_context.verify(raw_token, user.refresh_token_hash):
        raise credentials_exception

    # Issue a new token (rotation: old hash is overwritten)
    return await create_refresh_token(db, user)


async def revoke_tokens(db: AsyncSession, user: User) -> None:
    """Invalidate all outstanding tokens for a user.

    Bumps token_version (invalidates all JWTs that embed the old version)
    and clears the refresh token hash.
    """
    user.token_version = (user.token_version or 0) + 1
    user.refresh_token_hash = None
    user.refresh_token_expires_at = None
    db.add(user)
    await db.commit()


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """Decode and validate the JWT; enforce token_version to support revocation."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        token_version: int = payload.get("version")
        if username is None or token_version is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception

    # Revocation check: token_version must match the current DB value
    if token_version != user.token_version:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Dependency that restricts access to users with the admin role."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
