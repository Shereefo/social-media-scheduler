from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import logging
import asyncio
import time

from .database import get_db, engine
from .models import Base, Post
from .schema import PostCreate, PostResponse, PostUpdate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Social Media Scheduler API",
    description="Schedule and manage social media posts",
    version="0.1.0"
)

# Startup event to create tables
@app.on_event("startup")
async def startup():
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
            wait_time = 2 ** retry_count  # Exponential backoff
            logger.error(f"Error connecting to database (attempt {retry_count}/{max_retries}): {e}")
            logger.info(f"Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
    
    if retry_count == max_retries:
        logger.error("Failed to connect to the database after multiple attempts")
        raise Exception("Database connection failed")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Social Media Scheduler API"}

# Create - Schedule a new post
@app.post("/posts/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_post = Post(
            content=post.content,
            scheduled_time=post.scheduled_time,
            platform=post.platform
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
            detail=f"Error creating post: {str(e)}"
        )

# Read - Get all scheduled posts
@app.get("/posts/", response_model=List[PostResponse])
async def get_posts(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Post).order_by(Post.scheduled_time))
        posts = result.scalars().all()
        logger.info(f"Retrieved {len(posts)} posts")
        return posts
    except Exception as e:
        logger.error(f"Error retrieving posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving posts: {str(e)}"
        )

# Read - Get a specific post by ID
@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalars().first()
        
        if not post:
            logger.warning(f"Post with ID {post_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
            
        logger.info(f"Retrieved post with ID: {post_id}")
        return post
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving post: {str(e)}"
        )

# Update - Edit a scheduled post
@app.patch("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int, 
    updated_post: PostUpdate, 
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalars().first()
        
        if not post:
            logger.warning(f"Post with ID {post_id} not found for update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
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
        logger.info(f"Updated post with ID: {post_id}")
        return post
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating post {post_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating post: {str(e)}"
        )

# Delete - Remove a scheduled post
@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalars().first()
        
        if not post:
            logger.warning(f"Post with ID {post_id} not found for deletion")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
            
        await db.delete(post)
        await db.commit()
        logger.info(f"Deleted post with ID: {post_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting post {post_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting post: {str(e)}"
        )