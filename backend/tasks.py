# backend/tasks.py
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.future import select

from .database import async_session
from .models import Post, User
from .integrations.tiktok import TikTokAPI
from .storage import get_file_content

# Set up logging
logger = logging.getLogger(__name__)


async def check_and_publish_scheduled_posts():
    """Check for posts that need to be published and publish them."""
    async with async_session() as db:
        try:
            # Find posts that are scheduled and due for publishing
            # Use timezone-aware datetime to match database column type
            now = datetime.now(timezone.utc)

            result = await db.execute(
                select(Post, User)
                .join(User)
                .where(Post.status == "scheduled", Post.scheduled_time <= now)
            )
            posts_to_publish = result.fetchall()

            if posts_to_publish:
                logger.info(f"Found {len(posts_to_publish)} posts ready to publish")

            for post, user in posts_to_publish:
                if post.platform == "tiktok":
                    await publish_tiktok_post(db, post, user)
                else:
                    logger.warning(
                        f"Post {post.id} has unsupported platform: {post.platform}"
                    )

        except Exception as e:
            logger.error(f"Error in check_and_publish_scheduled_posts: {e}", exc_info=True)


async def publish_tiktok_post(db, post: Post, user: User):
    """Publish a single TikTok post."""
    try:
        logger.info(f"Attempting to publish TikTok post {post.id} for user {user.username}")

        # Check if user has valid TikTok token
        if not user.tiktok_access_token:
            logger.error(f"User {user.username} has no TikTok access token")
            post.status = "failed"
            await db.commit()
            return

        # Check if we're in simulation mode (for testing without actual API calls)
        import os
        SIMULATION_MODE = os.getenv("SCHEDULER_SIMULATION_MODE", "false").lower() == "true"

        if SIMULATION_MODE:
            # Simulation mode - just mark as published without calling TikTok API
            logger.info(
                f"🧪 SIMULATION MODE: Would publish post {post.id} to TikTok\n"
                f"   User: {user.username}\n"
                f"   Content: {post.content[:100]}...\n"
                f"   Video file: {post.video_filename or 'None'}"
            )
            post.status = "published"
            await db.commit()
            logger.info(f"✅ SIMULATION: Post {post.id} marked as published")
            return

        # Real publishing mode
        if post.video_filename:
            # Get the video file content
            video_content = await get_file_content(post.video_filename)

            # Publish to TikTok with video
            result = await TikTokAPI.post_video(db, user, video_content, post.content)

            logger.info(f"Published TikTok post {post.id} with video. TikTok ID: {result.get('data', {}).get('post_id')}")
        else:
            # For text-only posts, we'll mark as failed
            # In production, you'd need to require video or create a placeholder image
            logger.warning(
                f"Post {post.id} has no video file. "
                "TikTok requires video content. Marking as failed."
            )
            post.status = "failed"
            await db.commit()
            return

        # Update post status to published
        post.status = "published"
        await db.commit()

        logger.info(f"Successfully published scheduled TikTok post {post.id}")

    except Exception as e:
        logger.error(
            f"Error publishing scheduled TikTok post {post.id}: {e}",
            exc_info=True
        )

        # Update post status to failed
        post.status = "failed"
        await db.commit()


async def run_scheduler_loop():
    """Run the scheduler indefinitely in a background loop."""
    logger.info("Scheduler loop started - checking for scheduled posts every 60 seconds")

    while True:
        try:
            await check_and_publish_scheduled_posts()
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}", exc_info=True)

        # Check every 60 seconds
        await asyncio.sleep(60)
