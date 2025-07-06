# Standard library imports
from datetime import timedelta
from typing import List
import logging
import asyncio
from contextlib import asynccontextmanager

# FastAPI imports
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

# Middleware imports
from .middleware import error_handling_middleware

# Database imports
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

# Local application imports
from .config import settings
from .database import get_db, engine
from .models import Base, Post, User
from .schema import (
    PostCreate,
    PostResponse,
    PostUpdate,
    UserCreate,
    UserResponse,
    Token,
)
from .auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_active_user,
)
from .tasks import start_scheduler
from .routes import tiktok, tiktok_posts

# CORS support for frontend
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create a lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Add retry mechanism for database connection
    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            break
        except Exception as e:
            retry_count += 1
            wait_time = 2**retry_count  # Exponential backoff
            logger.error(
                f"Error connecting to database "
                f"(attempt {retry_count}/{max_retries}): {e}"
            )
            logger.info(f"Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)

    if retry_count == max_retries:
        logger.error("Failed to connect to the database after multiple attempts")
        raise Exception("Database connection failed")

    # Start the scheduler
    background_tasks = BackgroundTasks()
    start_scheduler(background_tasks)

    yield  # This is where FastAPI serves requests

    # Shutdown logic can go here
    logger.info("Shutting down application")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Social Media Scheduler API",
    description="Schedule and manage social media posts",
    version="0.1.0",
    lifespan=lifespan,
)

app.middleware("http")(error_handling_middleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://lovely-kangaroo-628d2a.netlify.app",  # Your Netlify domain
        "http://localhost:3000",  # React development server
        "http://localhost:5173",  # Vite development server
        "http://127.0.0.1:5173",  # Vite on local IP
        "http://127.0.0.1:3000",  # React on local IP
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include the TikTok routers
app.include_router(tiktok.router, prefix=settings.API_PREFIX)
app.include_router(tiktok_posts.router, prefix=settings.API_PREFIX)


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Social Media Scheduler API"}


# Create - Schedule a new post
@app.post("/posts/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new scheduled post."""
    try:
        db_post = Post(
            content=post.content,
            scheduled_time=post.scheduled_time,
            platform=post.platform,
            user_id=current_user.id,
        )
        db.add(db_post)
        await db.commit()
        await db.refresh(db_post)
        logger.info(f"Created post with ID: {db_post.id}")
        return db_post
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating post: {str(e)}",
        )


# Read - Get all scheduled posts
@app.get("/posts/", response_model=List[PostResponse])
async def get_posts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all posts for the current user."""
    try:
        # Update the query to filter by user_id
        result = await db.execute(
            select(Post)
            .where(Post.user_id == current_user.id)
            .order_by(Post.scheduled_time)
        )
        posts = result.scalars().all()
        logger.info(
            f"Retrieved {
                len(posts)} posts for user: {
                current_user.username}"
        )
        return posts
    except Exception as e:
        logger.error(f"Error retrieving posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving posts: {str(e)}",
        )


# Read - Get a specific post by ID
@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific post."""
    try:
        # Update the query to filter by user_id and post_id
        result = await db.execute(
            select(Post).where(Post.id == post_id, Post.user_id == current_user.id)
        )
        post = result.scalars().first()

        if not post:
            logger.warning(
                f"Post with ID {post_id} not found for user {
                    current_user.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        logger.info(
            f"Retrieved post with ID: {post_id} for user: {
                current_user.username}"
        )
        return post
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving post: {str(e)}",
        )


# Update - Edit a scheduled post
@app.patch("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    updated_post: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a post."""
    try:
        # Update the query to filter by user_id and post_id
        result = await db.execute(
            select(Post).where(Post.id == post_id, Post.user_id == current_user.id)
        )
        post = result.scalars().first()

        if not post:
            logger.warning(
                f"Post with ID {post_id} not found for update by user {
                    current_user.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        # Update post fields if provided
        if updated_post.content is not None:
            post.content = updated_post.content
        if updated_post.scheduled_time is not None:
            post.scheduled_time = updated_post.scheduled_time
        if updated_post.platform is not None:
            post.platform = updated_post.platform

        await db.commit()
        await db.refresh(post)
        logger.info(
            f"Updated post with ID: {post_id} by user: {
                current_user.username}"
        )
        return post
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating post {post_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating post: {str(e)}",
        )


# Delete - Remove a scheduled post
@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a post."""
    try:
        # Update the query to filter by user_id and post_id
        result = await db.execute(
            select(Post).where(Post.id == post_id, Post.user_id == current_user.id)
        )
        post = result.scalars().first()

        if not post:
            logger.warning(
                f"Post with ID {post_id} not found for deletion by user {
                    current_user.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        await db.delete(post)
        await db.commit()
        logger.info(
            f"Deleted post with ID: {post_id} by user: {
                current_user.username}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting post {post_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting post: {str(e)}",
        )


@app.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    try:
        # Check if user with the same email or username already exists
        result = await db.execute(
            select(User).where(
                or_(User.email == user.email, User.username == user.username)
            )
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists",
            )

        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email, username=user.username, hashed_password=hashed_password
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        logger.info(f"Registered new user: {db_user.username}")
        return db_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering user: {str(e)}",
        )


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Login to get access token."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring system status.
    Returns:
        dict: Status information including version and timestamp
    """
    from datetime import datetime, timezone
    from .database import async_session

    try:
        # Try to connect to the database
        async with async_session() as session:
            await session.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"

    return {
        "status": "healthy",
        "api_version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
    }


@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user
