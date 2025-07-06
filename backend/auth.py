from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .database import get_db
from .models import User
from .config import settings

# Password hashing configuration
# This uses bcrypt, a secure algorithm for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
# This tells FastAPI to look for a token in the Authorization header with
# Bearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Create a password hash."""
    return pwd_context.hash(password)


async def get_user_by_username(db: AsyncSession, username: str):
    """Get user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str):
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def authenticate_user(db: AsyncSession, username: str, password: str):
    """Authenticate a user."""
    user = await get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token."""
    to_encode = data.copy()

    # Set token expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add expiration time to token data
    to_encode.update({"exp": expire})

    # Create JWT token using the settings from config.py
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """Get the current authenticated user."""
    # Define the error for invalid credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # Extract username from token
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except JWTError:
        # If JWT decoding fails, raise error
        raise credentials_exception

    # Get the user from the database
    user = await get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Verify that the current user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
