from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PostBase(BaseModel):
    content: str
    scheduled_time: datetime
    platform: Optional[str] = "twitter"

class PostCreate(PostBase):
    pass

class PostUpdate(PostBase):
    content: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    platform: Optional[str] = None

class PostResponse(PostBase):
    id: int
    created_at: datetime
    updated_at: datetime
    status: str

    class Config:
        from_attributes = True