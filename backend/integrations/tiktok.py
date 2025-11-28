import httpx
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Optional, Any
from urllib.parse import urlencode

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

        # Use urlencode to properly encode URL parameters
        query_string = urlencode(params)
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
                    detail=(f"Failed to exchange code for token: " f"{response.text}"),
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

            except Exception:
                # If refresh fails, the user needs to re-authenticate
                return None

        return user.tiktok_access_token

    @staticmethod
    async def post_video(
        db: AsyncSession, user: User, video_file: bytes, caption: str
    ) -> Dict[str, Any]:
        """Post a video to TikTok using Content Posting API v2."""
        access_token = await TikTokAPI.ensure_valid_token(db, user)
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TikTok authentication required",
            )

        # TikTok Content Posting API v2 upload flow:
        # 1. Initialize upload - get upload_url and publish_id
        # 2. Upload video chunks via PUT to upload_url
        # 3. Video processes automatically (no separate publish step)

        import math

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Step 1: Initialize upload with FILE_UPLOAD method
            video_size = len(video_file)
            chunk_size = min(10 * 1024 * 1024, video_size)  # 10MB chunks or file size
            total_chunks = math.ceil(video_size / chunk_size)

            init_payload = {
                "post_info": {
                    "title": caption,
                    "privacy_level": "SELF_ONLY",  # Options: PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                    "video_cover_timestamp_ms": 1000,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_size,
                    "chunk_size": chunk_size,
                    "total_chunk_count": total_chunks,
                }
            }

            init_response = await client.post(
                "https://open.tiktokapis.com/v2/post/publish/video/init/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json; charset=UTF-8"
                },
                json=init_payload,
            )

            if init_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to initialize TikTok upload: {init_response.text}",
                )

            init_data = init_response.json()

            # Check for API errors
            if init_data.get("error", {}).get("code") != "ok":
                error_msg = init_data.get("error", {}).get("message", "Unknown error")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"TikTok API error: {error_msg}",
                )

            upload_url = init_data["data"]["upload_url"]
            publish_id = init_data["data"]["publish_id"]

            # Step 2: Upload video chunks via PUT
            for chunk_index in range(total_chunks):
                start_byte = chunk_index * chunk_size
                end_byte = min(start_byte + chunk_size, video_size) - 1
                chunk_data = video_file[start_byte:end_byte + 1]

                upload_response = await client.put(
                    upload_url,
                    content=chunk_data,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Length": str(len(chunk_data)),
                        "Content-Range": f"bytes {start_byte}-{end_byte}/{video_size}",
                    },
                )

                if upload_response.status_code not in [200, 201, 202]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to upload video chunk {chunk_index + 1}/{total_chunks}: {upload_response.text}",
                    )

            # Step 3: Return success - video will process automatically
            return {
                "data": {
                    "publish_id": publish_id,
                    "status": "processing"
                },
                "message": "Video uploaded successfully and is processing"
            }
