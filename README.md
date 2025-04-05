# Social Media Scheduler 🗕️

A scalable, asynchronous FastAPI application designed to schedule and manage posts across social media platforms. The project leverages Docker for containerization, PostgreSQL for data storage, and is structured for long-term maintainability and growth into a SaaS product.

---

## ✨ [Overview](#overview)

This RESTful API lets users create, view, update, and delete scheduled social media posts. It is built with modern Python tooling and designed to be containerized for easy deployment.

**New updates include:**

- Restructured as a proper Python package
- Dockerized with PostgreSQL and retry logic
- Added async SQLAlchemy integration
- JWT authentication via OAuth2
- Pushed to GitHub with clean version control and `.gitignore`

---

## 📊 [Tech Stack](#tech-stack)

- **Framework:** FastAPI (async Python)
- **Database:** PostgreSQL (via SQLAlchemy async ORM)
- **Auth:** OAuth2 with JWT Tokens
- **Containerization:** Docker + Docker Compose
- **Docs:** Auto-generated Swagger UI
- **Version Control:** GitHub

---

## 🔄 [Directory Structure](#directory-structure)

```
social-media-scheduler/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schema.py
│   ├── crud.py
│   └── auth.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── setup.py
└── README.md
```

---

## 📁 [Setup & Installation](#setup--installation)

### Using Docker (Recommended)

```bash
git clone https://github.com/Shereefo/social-media-scheduler.git
cd social-media-scheduler
docker-compose up --build
```

Access the API:

- API Base: [http://localhost:8000](http://localhost:8000)
- Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Manual Local Setup

```bash
git clone https://github.com/Shereefo/social-media-scheduler.git
cd social-media-scheduler
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .
uvicorn backend.main:app --reload
```

> **Note:** Ensure PostgreSQL is installed and running. Update credentials in `backend/database.py` if needed.

---

## 👥 [Authentication](#authentication)

The app now includes a secure OAuth2 system with JWT tokens. Users can log in via the `/token` route.

```bash
curl -X POST http://localhost:8000/token \
     -d "username=example_user&password=password123" \
     -H "Content-Type: application/x-www-form-urlencoded"
```

Token must be passed as a Bearer token in future requests.

---

## 📊 [API Endpoints](#api-endpoints)

### General

- `GET /` - Welcome message

### Posts

- `POST /posts/` - Create a new post
- `GET /posts/` - View all posts
- `GET /posts/{id}` - View one post
- `PUT /posts/{id}` - Update a post
- `DELETE /posts/{id}` - Delete a post

### Auth

- `POST /token` - Login and get access token (OAuth2)
- `GET /users/me` - (Coming soon) View logged-in user profile

---

## 🪄 [Docker Configuration](#docker-configuration)

- **Dockerfile**: Defines the FastAPI app image
- **docker-compose.yml**: Orchestrates both FastAPI and PostgreSQL containers

To stop:

```bash
docker-compose down
```

---

## 🚀 [Next Steps](#next-steps)

- Add basic error handling and logging
- Create a simple demo script
- Document API endpoints
- Implement basic security measures
- Create a simple Postman collection

---

## 🔧 [Troubleshooting](#troubleshooting)

- Ensure PostgreSQL is running properly (use `docker ps`)
- Rebuild container: `docker-compose down && docker-compose up --build`
- Check `.env` or `settings.py` if tokens/keys are missing
- Clear Python cache: `find . -name '__pycache__' -exec rm -r {} +`

---

## 👏 [Acknowledgements](#acknowledgements)

Thanks to the DevOps and open source community for tools like FastAPI, Docker, and async SQLAlchemy that make this project possible.

> ⭐ Star the repo to follow its evolution!

