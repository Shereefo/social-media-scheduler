# Social Media Scheduler 📅

A scalable FastAPI-based application designed to schedule and manage posts across social media platforms. This project integrates Docker for containerization and PostgreSQL for persistent data storage, ensuring smooth deployment and scalability.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Directory Structure](#directory-structure)
4. [Setup & Installation](#setup--installation)
    - [Using Docker (Recommended)](#using-docker-recommended)
    - [Local Development](#local-development)
5. [API Endpoints](#api-endpoints)
6. [Database Configuration](#database-configuration)
7. [Docker Configuration](#docker-configuration)
8. [Development Notes](#development-notes)
9. [Next Steps](#next-steps)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview

This application provides a RESTful API for scheduling and managing social media posts. It uses modern asynchronous Python with FastAPI and SQLAlchemy for database operations. The entire application is containerized with Docker for easy deployment and development.

### **Recent Enhancements:**
- ✅ Created a proper Python package structure with necessary files.
- ✅ Set up a FastAPI application with CRUD operations for posts.
- ✅ Configured SQLAlchemy with async support for PostgreSQL.
- ✅ Dockerized the application with proper configuration.
- ✅ Added retry logic for database connections.
- ✅ Set up proper imports and package structure.
- ✅ Pushed everything to GitHub with appropriate `.gitignore` settings.

---

## Tech Stack
- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Database:** PostgreSQL
- **Containerization:** Docker & Docker Compose
- **API Documentation:** Swagger UI (auto-generated)

---

## Directory Structure

```
social-media-scheduler/
├── backend/
│   ├── __init__.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schema.py
│   ├── crud.py
│   ├── dependencies.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── setup.py
└── README.md
```

---

## Setup & Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/Shereefo/social-media-scheduler.git
   cd social-media-scheduler
   ```

2. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

3. Access the API:
   - API interface: [http://localhost:8000](http://localhost:8000)
   - Swagger documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/Shereefo/social-media-scheduler.git
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

4. Set up PostgreSQL and update the database connection string in `backend/database.py` if needed.

5. Run the application:
   ```bash
   uvicorn backend.main:app --reload
   ```

---

## API Endpoints

- `GET /` - Welcome message
- `POST /posts/` - Create a new post
- `GET /posts/` - List all posts
- `GET /posts/{post_id}` - Get a specific post
- `PATCH /posts/{post_id}` - Update a post
- `DELETE /posts/{post_id}` - Delete a post

---

## Database Configuration

The application uses PostgreSQL with SQLAlchemy's async features. The database connection is configured in `backend/database.py`.

---

## Docker Configuration

- `Dockerfile`: Defines the container for the FastAPI application.
- `docker-compose.yml`: Orchestrates the API and PostgreSQL services.

---

## Development Notes

- The application uses async/await for non-blocking database operations.
- Database tables are automatically created at startup.
- Failed connection attempts to the database will be retried with exponential backoff.

---

## Next Steps

- [ ] Add authentication system (OAuth2, JWT-based authentication).
- [ ] Implement social media platform integrations (TikTok API, etc.).
- [ ] Add scheduling functionality to automatically publish posts.
- [ ] Create a frontend interface.
- [ ] Implement user roles and permissions.
- [ ] Add analytics for post performance.

---

## Troubleshooting

If you encounter database connection issues:
1. Ensure PostgreSQL is running and accessible.
2. Check database credentials in `backend/database.py`.
3. Verify that Docker containers are on the same network.

---

This project structure was designed to provide a solid foundation for a production-ready social media scheduling application.

