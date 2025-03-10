# backend/routes/tiktok.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ..models import User
from ..auth import get_current_active_user
from ..integrations.tiktok import TikTokAPI

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth/tiktok", tags=["tiktok"])

@router.get("/authorize")
async def authorize_tiktok():
    # For testing only
    """Get TikTok authorization URL."""
    authorization_url = TikTokAPI.get_authorization_url()
    return {"authorization_url": authorization_url}

@router.get("/callback")
async def tiktok_callback(
    code: str, 
    state: str, 
    request: Request, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Handle TikTok OAuth callback."""
    try:
        # Exchange code for token
        token_data = await TikTokAPI.exchange_code_for_token(code)
        
        # Update user with TikTok token info
        current_user.tiktok_access_token = token_data["access_token"]
        current_user.tiktok_refresh_token = token_data["refresh_token"]
        current_user.tiktok_open_id = token_data["open_id"]
        current_user.tiktok_token_expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        
        await db.commit()
        await db.refresh(current_user)
        
        logger.info(f"User {current_user.username} connected TikTok account")
        
        # In a real app, you might redirect to a frontend page
        return {"message": "TikTok account connected successfully"}
        
    except Exception as e:
        logger.error(f"Error connecting TikTok account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect TikTok account: {str(e)}"
        )

@router.delete("/disconnect")
async def disconnect_tiktok(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Disconnect TikTok account."""
    current_user.tiktok_access_token = None
    current_user.tiktok_refresh_token = None
    current_user.tiktok_open_id = None
    current_user.tiktok_token_expires_at = None
    
    await db.commit()
    await db.refresh(current_user)
    
    logger.info(f"User {current_user.username} disconnected TikTok account")
    
    return {"message": "TikTok account disconnected successfully"}