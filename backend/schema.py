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

# User registration, login and token response schemas  
class UserBase(BaseModel):
    email: str
    username: str
    
class UserCreate(UserBase):
    password: str
    
class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    username: Optional[str] = None