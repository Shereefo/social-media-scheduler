# backend/storage.py
import os
import uuid
from fastapi import UploadFile
import logging
import aiofiles

# Set up logging
logger = logging.getLogger(__name__)

# Define storage directory
UPLOAD_DIR = "uploads"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_upload(file: UploadFile, user_id: int) -> str:
    """Save an uploaded file to disk and return the filename."""
    # Generate a unique filename
    filename = f"{user_id}_{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # Save the file
        async with aiofiles.open(filepath, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        logger.info(f"Saved uploaded file: {filepath}")
        return filename
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise

async def get_file_content(filename: str) -> bytes:
    """Get the content of a file."""
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    try:
        async with aiofiles.open(filepath, 'rb') as in_file:
            content = await in_file.read()
        return content
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        raise