# backend/routes/tiktok_posts.py
from fastapi import (
    APIRouter, Depends, HTTPException, status, File, UploadFile, Form
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging
from datetime import datetime

from ..database import get_db
from ..models import User, Post
from ..schema import PostResponse
from ..auth import get_current_active_user
from ..integrations.tiktok import TikTokAPI
from ..storage import save_upload, get_file_content

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/tiktok", tags=["tiktok"])


@router.post("/posts/", response_model=PostResponse)
async def create_tiktok_post(
    content: str = Form(...),
    scheduled_time: datetime = Form(...),
    video: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new TikTok post."""
    # Check if user has connected TikTok
    if not current_user.tiktok_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TikTok account not connected",
        )

    try:
        # Save the video file
        filename = await save_upload(video, current_user.id)

        # Create a new post in the database
        post = Post(
            content=content,
            scheduled_time=scheduled_time,
            platform="tiktok",
            user_id=current_user.id,
            status="scheduled",
            video_filename=filename,  # Save the filename
        )

        db.add(post)
        await db.commit()
        await db.refresh(post)

        logger.info(
            f"Created TikTok post with ID: {post.id} "
            f"for user: {current_user.username}"
        )

        return post
    except Exception as e:
        logger.error(f"Error creating TikTok post: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating TikTok post: {str(e)}",
        )


@router.post("/posts/{post_id}/publish")
async def publish_tiktok_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Manually publish a TikTok post."""
    # Get the post
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == current_user.id)
    )
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if post.platform != "tiktok":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Not a TikTok post"
        )

    try:
        # Get the video file content
        video_content = await get_file_content(post.video_filename)

        # Publish to TikTok
        result = await TikTokAPI.post_video(
            db, current_user, video_content, post.content
        )

        # Update post status
        post.status = "published"
        await db.commit()

        logger.info(f"Published TikTok post with ID: {post.id}")

        return {
            "message": "Post published successfully",
            "tiktok_post_id": result["data"]["post_id"],
        }
    except Exception as e:
        logger.error(f"Error publishing TikTok post: {e}")

        # Update post status to failed
        post.status = "failed"
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error publishing TikTok post: {str(e)}",
        )
