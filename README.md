# Social Media Scheduler 📅

A scalable FastAPI-based application designed to schedule and manage posts across social media platforms with TikTok integration. This project uses modern async Python with FastAPI, SQLAlchemy for ORM functionality, and JWT-based authentication to provide a secure and responsive API.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Features](#features)
4. [Directory Structure](#directory-structure)
5. [Setup & Installation](#setup--installation)
    - [Using Docker (Recommended)](#using-docker-recommended)
    - [Local Development](#local-development)
6. [Environment Variables](#environment-variables)
7. [API Endpoints](#api-endpoints)
8. [Authentication](#authentication)
9. [TikTok Integration](#tiktok-integration)
10. [Development Notes](#development-notes)
11. [Next Steps](#next-steps)
12. [Troubleshooting](#troubleshooting)

---

## Project Overview

This application provides a RESTful API for scheduling and managing social media posts. It uses modern asynchronous Python with FastAPI and SQLAlchemy for database operations. The entire application is containerized with Docker for easy deployment and development.

### **Key Features:**
- User authentication with JWT tokens
- Post scheduling and management 
- TikTok integration for video uploads
- Background task processing for automatic publishing
- Modular and scalable architecture

---

## Tech Stack
- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Database:** PostgreSQL with async support
- **Authentication:** JWT-based with bcrypt password hashing
- **External APIs:** TikTok API integration
- **Containerization:** Docker & Docker Compose
- **API Documentation:** Swagger UI (auto-generated)
- **Background Tasks:** Async task processing for scheduled posts

---

## Features

- **User Management:**
  - Registration and authentication
  - Secure password handling
  - JWT token-based sessions

- **Post Management:**
  - Create, retrieve, update, and delete posts
  - Schedule posts for future publishing
  - Filter posts by user and platform

- **TikTok Integration:**
  - OAuth authentication flow with TikTok
  - Video upload and publishing
  - Token refresh handling

- **Scheduling System:**
  - Background task processing
  - Automatic publishing of scheduled content
  - Failure handling and status tracking

---

## Directory Structure

```
social-media-scheduler/
├── backend/
│   ├── __init__.py
│   ├── auth.py               # Authentication module
│   ├── config.py             # Centralized configuration
│   ├── database.py           # Database connection
│   ├── main.py               # FastAPI application
│   ├── models.py             # SQLAlchemy models
│   ├── schema.py             # Pydantic schemas
│   ├── storage.py            # File storage system
│   ├── tasks.py              # Background task scheduler
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── tiktok.py         # TikTok API integration
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── tiktok.py         # TikTok authentication routes
│   │   └── tiktok_posts.py   # TikTok post management routes
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── setup.py
```

---

## Setup & Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/social-media-scheduler.git
   cd social-media-scheduler
   ```

2. Create a `.env` file with the necessary environment variables (see [Environment Variables](#environment-variables))

3. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

4. Access the API:
   - API interface: [http://localhost:8000](http://localhost:8000)
   - Swagger documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/social-media-scheduler.git
   cd social-media-scheduler
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install the package in development mode
   ```

4. Create a `.env` file with the necessary environment variables

5. Set up PostgreSQL and update the database connection string in `.env` if needed

6. Run the application:
   ```bash
   uvicorn backend.main:app --reload
   ```

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

```
# API Settings
SECRET_KEY=your-secret-key-needs-to-be-updated
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database Settings
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/scheduler

# TikTok API Settings
TIKTOK_CLIENT_KEY=your-tiktok-client-key
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret
TIKTOK_REDIRECT_URI=http://localhost:8000/api/v1/auth/tiktok/callback
```

---

## API Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /token` - Login and get access token
- `GET /users/me` - Get current user information

### Posts
- `POST /posts/` - Create a new post
- `GET /posts/` - List all posts for current user
- `GET /posts/{post_id}` - Get a specific post
- `PATCH /posts/{post_id}` - Update a post
- `DELETE /posts/{post_id}` - Delete a post

### TikTok Integration
- `GET /api/v1/auth/tiktok/authorize` - Get TikTok authorization URL
- `GET /api/v1/auth/tiktok/callback` - Handle TikTok OAuth callback
- `DELETE /api/v1/auth/tiktok/disconnect` - Disconnect TikTok account
- `POST /api/v1/tiktok/posts/` - Create a new TikTok post
- `POST /api/v1/tiktok/posts/{post_id}/publish` - Manually publish a TikTok post

---

## Authentication

The application uses JWT-based authentication:

1. Register a user with `POST /register`
2. Obtain a token with `POST /token` (using username and password)
3. Include the token in the Authorization header for protected endpoints:
   ```
   Authorization: Bearer your-access-token
   ```

---

## TikTok Integration

To use the TikTok integration:

1. Create a TikTok developer account and app at [TikTok for Developers](https://developers.tiktok.com/)
2. Set the `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, and `TIKTOK_REDIRECT_URI` environment variables
3. Connect your TikTok account through the API:
   - Get the authorization URL with `GET /api/v1/auth/tiktok/authorize`
   - Complete the OAuth flow which will handle the callback
   - Create and schedule TikTok posts using the provided endpoints

The application handles token refresh automatically when tokens expire.

---

## Development Notes

- The application uses async/await for non-blocking database operations
- Database tables are automatically created at startup
- Failed connection attempts to the database will be retried with exponential backoff
- Video files for TikTok posts are stored in the `uploads` directory
- The background scheduler checks for posts to publish every minute

---

## Next Steps

- [ ] Add additional social media platform integrations (Twitter, Instagram, etc.)
- [ ] Implement analytics for post performance
- [ ] Create a frontend interface
- [ ] Add admin dashboard for user management
- [ ] Implement rate limiting
- [ ] Add comprehensive test suite
- [ ] Set up CI/CD pipeline

---

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running and accessible
- Check database credentials in your `.env` file
- Verify that Docker containers are on the same network

### TikTok Authentication Issues
- Verify your TikTok API credentials
- Ensure your redirect URI matches exactly what's configured in the TikTok developer console
- Check the application logs for detailed error messages

### File Upload Problems
- Ensure the `uploads` directory exists and is writable
- Check file size limits (may need to adjust FastAPI's limits for larger videos)

---

This project is designed to provide a solid foundation for a production-ready social media scheduling application with secure authentication and TikTok integration.
