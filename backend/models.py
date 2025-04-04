from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # You can add platform-specific fields here
    platform = Column(String, nullable=True, default="twitter")
    status = Column(String, nullable=False, default="scheduled")  # scheduled, published, failed

    # Add user relationship 
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="posts")

    # Add video filename
    video_filename = Column(String, nullable=True)


class User(Base): 
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # TikTok integration fields
    tiktok_access_token = Column(String, nullable=True)
    tiktok_refresh_token = Column(String, nullable=True) 
    tiktok_open_id = Column(String, nullable=True)
    
    # Added to explicitly set the timezone
    tiktok_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship with posts
    posts = relationship("Post", back_populates="user")