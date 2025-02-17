from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, select
from backend.database import get_db, engine  
from contextlib import asynccontextmanager
from pydantic import BaseModel

# Base Class for SQLAlchemy
class Base(DeclarativeBase):
    pass

# ORM Model for Database
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    scheduled_time = Column(String, nullable=False)

# Pydantic Model for API Validation
class PostCreate(BaseModel):
    content: str
    scheduled_time: str

# Lifespan handler to initialize the database
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

# Create FastAPI app instance with lifespan
app = FastAPI(lifespan=lifespan)

# Create - Schedule a new post
@app.post("/posts/")
async def create_post(post: PostCreate, db: AsyncSession = Depends(get_db)):
    db_post = Post(content=post.content, scheduled_time=post.scheduled_time)
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)
    return db_post

# Read - Get all scheduled posts
@app.get("/posts/")
async def get_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post))  # ✅ Use `select(Post)`
    return result.scalars().all()  # ✅ Properly extract results

# Read - Get a specific post by ID
@app.get('/posts/{post_id}')
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))  
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# Update - Edit a scheduled post
@app.put("/posts/{post_id}")
async def update_post(post_id: int, updated_post: PostCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id)) 
    post = result.scalars().first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.content = updated_post.content
    post.scheduled_time = updated_post.scheduled_time
    await db.commit()
    await db.refresh(post)
    return post

# Delete - Remove a scheduled post
@app.delete("/posts/{post_id}")
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))  
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await db.delete(post)
    await db.commit()
    return {"message": "Post deleted successfully"}

@app.get("/")
async def read_root():
    return {"message": "Hello, Social Media Scheduler!"}