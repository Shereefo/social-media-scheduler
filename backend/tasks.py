# backend/tasks.py
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import BackgroundTasks

from .database import async_session
from .models import Post, User
from .integrations.tiktok import TikTokAPI
from .storage import get_file_content

# Set up logging
logger = logging.getLogger(__name__)

async def check_and_publish_scheduled_posts():
    """Check for posts that need to be published and publish them."""
    async with async_session() as db:
        # Find posts that are scheduled and due for publishing
        now = datetime.utcnow()
        result = await db.execute(
            select(Post, User)
            .join(User)
            .where(
                Post.status == "scheduled",
                Post.scheduled_time <= now
            )
        )
        posts_to_publish = result.fetchall()
        
        for post, user in posts_to_publish:
            if post.platform == "tiktok":
                try:
                    # Get the video file content
                    video_content = await get_file_content(post.video_filename)
                    
                    # Publish to TikTok
                    await TikTokAPI.post_video(db, user, video_content, post.content)
                    
                    # Update post status
                    post.status = "published"
                    await db.commit()
                    
                    logger.info(f"Published scheduled TikTok post with ID: {post.id}")
                except Exception as e:
                    logger.error(f"Error publishing scheduled TikTok post {post.id}: {e}")
                    
                    # Update post status to failed
                    post.status = "failed"
                    await db.commit()

def start_scheduler(background_tasks: BackgroundTasks):
    """Start the background scheduler."""
    background_tasks.add_task(run_scheduler)

async def run_scheduler():
    """Run the scheduler indefinitely."""
    while True:
        try:
            await check_and_publish_scheduled_posts()
        except Exception as e:
            logger.error(f"Error in scheduler: {e}")
        
        # Check every minute
        await asyncio.sleep(60)