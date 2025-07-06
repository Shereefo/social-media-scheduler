import httpx
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Optional, Any

from ..models import User
from ..config import settings


class TikTokAPI:
    """TikTok API integration class."""

    BASE_URL = "https://open.tiktokapis.com/v2"
    AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"

    @staticmethod
    def get_authorization_url() -> str:
        """Get the TikTok authorization URL."""
        params = {
            "client_key": settings.TIKTOK_CLIENT_KEY,
            "response_type": "code",
            "scope": "user.info.basic,video.publish",
            "redirect_uri": settings.TIKTOK_REDIRECT_URI,
            "state": "state",  # You should generate a secure random state
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{TikTokAPI.AUTH_URL}?{query_string}"

    @staticmethod
    async def exchange_code_for_token(code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TikTokAPI.BASE_URL}/oauth/token/",
                data={
                    "client_key": settings.TIKTOK_CLIENT_KEY,
                    "client_secret": settings.TIKTOK_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.TIKTOK_REDIRECT_URI,
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange code for token: {response.text}",
                )

            return response.json()

    @staticmethod
    async def refresh_token(refresh_token: str) -> Dict[str, Any]:
        """Refresh the TikTok access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TikTokAPI.BASE_URL}/oauth/token/",
                data={
                    "client_key": settings.TIKTOK_CLIENT_KEY,
                    "client_secret": settings.TIKTOK_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to refresh token: {response.text}",
                )

            return response.json()

    @staticmethod
    async def ensure_valid_token(db: AsyncSession, user: User) -> Optional[str]:
        """Ensure the user has a valid TikTok token."""
        if not user.tiktok_access_token:
            return None

        # Check if token is expired or about to expire
        if (
            user.tiktok_token_expires_at
            and user.tiktok_token_expires_at
            <= datetime.now(timezone.utc) + timedelta(minutes=5)
        ):

            if not user.tiktok_refresh_token:
                return None

            # Refresh the token
            try:
                token_data = await TikTokAPI.refresh_token(user.tiktok_refresh_token)

                # Update user with new token data
                user.tiktok_access_token = token_data["access_token"]
                user.tiktok_refresh_token = token_data["refresh_token"]
                user.tiktok_token_expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=token_data["expires_in"]
                )

                await db.commit()
                await db.refresh(user)

            except Exception as e:
                # If refresh fails, the user needs to re-authenticate
                return None

        return user.tiktok_access_token

    @staticmethod
    async def post_video(
        db: AsyncSession, user: User, video_file: bytes, caption: str
    ) -> Dict[str, Any]:
        """Post a video to TikTok."""
        access_token = await TikTokAPI.ensure_valid_token(db, user)
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TikTok authentication required",
            )

        # TikTok video upload is a multi-step process
        # 1. Initialize upload
        # 2. Upload video chunks
        # 3. Complete upload and publish

        # This is a simplified version - in reality, you'd need to handle
        # large file uploads with chunking, etc.

        async with httpx.AsyncClient() as client:
            # Step 1: Initialize upload
            init_response = await client.post(
                f"{TikTokAPI.BASE_URL}/video/init/",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"post_info": {"title": caption, "privacy_level": "PUBLIC"}},
            )

            if init_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to initialize TikTok upload: {init_response.text}",
                )

            upload_data = init_response.json()
            upload_id = upload_data["data"]["upload_id"]

            # Step 2: Upload video (simplified - in reality you'd chunk large videos)
            upload_response = await client.post(
                f"{TikTokAPI.BASE_URL}/video/upload/",
                headers={"Authorization": f"Bearer {access_token}"},
                files={"video": ("video.mp4", video_file, "video/mp4")},
                data={"upload_id": upload_id},
            )

            if upload_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to upload video to TikTok: {upload_response.text}",
                )

            # Step 3: Complete upload
            complete_response = await client.post(
                f"{TikTokAPI.BASE_URL}/video/publish/",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"upload_id": upload_id},
            )

            if complete_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to publish video to TikTok: {complete_response.text}",
                )

            return complete_response.json()
