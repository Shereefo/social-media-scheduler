# TikTimer - TikTok Social Media Scheduler 📅

> **Note:** This project currently focuses on production-ready backend services and AWS infrastructure. The frontend interface is planned for Phase 2 development - this showcase demonstrates cloud architecture, API development, and DevOps practices.

![image alt](https://github.com/Shereefo/social-media-scheduler/blob/bea4c94258fcc33c28c02bfcecad91f0d4533fac/TikTimer%20logo.png)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0+-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat&logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?style=flat&logo=postgresql)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-20.10+-blue?style=flat&logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

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
10. [Database Schema](#database-schema)
11. [Development Notes](#development-notes)
12. [Implementation Challenges & Solutions](#implementation-challenges--solutions)
13. [Project Journey & Development Timeline](#project-journey--development-timeline)
14. [Deployment Guide](#deployment-guide)
    - [Netlify Deployment for TikTok OAuth Callback](#netlify-deployment-for-tiktok-oauth-callback)
    - [Docker-based Deployment](#docker-based-deployment)
    - [Cloud Infrastructure](#cloud-infrastructure)
15. [Current Project Status](#current-project-status)
16. [Troubleshooting](#troubleshooting)
17. [Next Steps](#next-steps)
18. [License](#license)

---

## Project Overview

This application provides a RESTful API for scheduling and managing social media posts. It uses modern asynchronous Python with FastAPI and SQLAlchemy for database operations. The entire application is containerized with Docker for easy deployment and development.

### **Inspiration & Motivation**

As a TikTok creator and social media enthusiast, I noticed a significant gap in the market for TikTok-specific scheduling tools. While platforms like Instagram and Twitter had numerous scheduling solutions, TikTok creators were left manually posting content or using generic tools that didn't integrate properly with TikTok's unique API requirements.

Having a passion for optimizing systems and streamlining workflows, I saw this as the perfect opportunity to solve a real pain point in the creator economy. The challenge of building a robust OAuth integration with TikTok's API, combined with the need for reliable scheduling infrastructure, made this an ideal project to showcase full-stack development skills while creating something genuinely useful for the creator community.

This project represents the intersection of my interests in social media, system optimization, and modern web development practices.

### **Key Features:**
- User authentication with JWT tokens
- Post scheduling and management 
- TikTok integration for video uploads
- Background task processing for automatic publishing
- Modular and scalable architecture

---

## Tech Stack
- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Database:** PostgreSQL with async support (via asyncpg)
- **Authentication:** JWT-based with bcrypt password hashing
- **External APIs:** TikTok API integration
- **Containerization:** Docker & Docker Compose
- **API Documentation:** Swagger UI (auto-generated)
- **Background Tasks:** Async task processing for scheduled posts
- **Database Migrations:** Alembic for schema versioning
- **Error Handling:** Middleware-based consistent error handling
- **Configuration:** Environment-based with pydantic-settings

---

## Features

- **User Management:**
  - Registration and authentication
  - Secure password handling with bcrypt
  - JWT token-based sessions
  - User profile management

- **Post Management:**
  - Create, retrieve, update, and delete posts
  - Schedule posts for future publishing
  - Filter posts by user and platform
  - Post status tracking (scheduled, published, failed)

- **TikTok Integration:**
  - OAuth authentication flow with TikTok
  - Video upload and publishing
  - Token refresh handling and automatic renewal
  - Timezone-aware token expiration
  - Secure storage of platform credentials
  - API error handling and retry mechanisms

- **File Storage System:**
  - Local file storage with unique identifiers
  - Async file operations with aiofiles
  - Organized upload directory structure
  - Support for various media formats

- **Scheduling System:**
  - Background task processing
  - Automatic publishing of scheduled content
  - Failure handling and status tracking
  - Retry mechanisms for failed posts

- **System Health and Monitoring:**
  - Health check endpoint for monitoring
  - Database connectivity validation
  - Exponential backoff for database connection retries
  - Detailed logging for debugging and auditing

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
│   ├── middleware.py         # Custom middleware
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
├── migrations/               # Alembic database migrations
│   ├── versions/             # Migration versions
│   ├── env.py                # Migration environment
│   ├── README                # Migration documentation
│   └── script.py.mako        # Migration template
├── tiktimer-infrastructure/  # Terraform infrastructure as code
│   ├── modules/              # Terraform modules
│   │   ├── networking/       # VPC, subnets, security groups
│   │   ├── database/         # RDS PostgreSQL configuration
│   │   ├── storage/          # S3 buckets and policies
│   │   ├── compute/          # ECS Fargate and ALB
│   │   └── security/         # WAF, GuardDuty, Security Hub
│   ├── main.tf               # Main Terraform configuration
│   ├── variables.tf          # Input variables
│   ├── outputs.tf            # Output values
│   └── providers.tf          # AWS provider configuration
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose setup
├── requirements.txt          # Python dependencies
├── alembic.ini               # Alembic configuration
├── setup.py                  # Package setup
└── .env.example              # Example environment variables
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

6. Run database migrations:
   ```bash
   alembic upgrade head
   ```

7. Run the application:
   ```bash
   uvicorn backend.main:app --reload
   ```

---

## Environment Variables

Create a `.env` file in the project root based on the provided `.env.example`:

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

# AWS Settings (for future deployment)
# AWS_ACCESS_KEY_ID=your-aws-access-key
# AWS_SECRET_ACCESS_KEY=your-aws-secret-key
# AWS_REGION=us-east-1
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
- `GET /health` - Check API and database health

### TikTok Integration
- `GET /api/v1/auth/tiktok/authorize` - Get TikTok authorization URL
- `GET /api/v1/auth/tiktok/callback` - Handle TikTok OAuth callback
- `DELETE /api/v1/auth/tiktok/disconnect` - Disconnect TikTok account
- `POST /api/v1/auth/tiktok/exchange-token` - Exchange authorization code for token
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

### Authentication Flow

1. **User Registration:**
   ```bash
   curl -X POST http://localhost:8000/register \
        -H "Content-Type: application/json" \
        -d '{"username":"example_user","email":"user@example.com","password":"securepassword123"}'
   ```

2. **User Login:**
   ```bash
   curl -X POST http://localhost:8000/token \
        -d "username=example_user&password=securepassword123" \
        -H "Content-Type: application/x-www-form-urlencoded"
   ```

3. **Using the Token:**
   ```bash
   curl -X GET http://localhost:8000/posts/ \
        -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```

4. **Logout (Client-side):** Simply discard the token on the client-side. The server doesn't store token state.

---

## TikTok Integration

This application supports integration with TikTok's API for posting content. The integration is handled through OAuth 2.0 flow.

### Setting Up TikTok API

1. Create a TikTok Developer Account at [TikTok for Developers](https://developers.tiktok.com/)
2. Create a new application in the TikTok Developer Portal
3. Set the redirect URI to match your `TIKTOK_REDIRECT_URI` environment variable
4. Obtain your Client Key and Client Secret and add them to your environment variables

### TikTok OAuth Callback Page

The TikTok OAuth flow requires a callback page that handles the authorization code. We've created a custom HTML page hosted on Netlify to handle this callback:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Authorization Successful</title>
    <style>
        /* TikTok-themed styling with gradient background */
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #25f4ee 0%, #fe2c55 100%);
            /* Additional styling... */
        }
        /* More styling... */
    </style>
</head>
<body>
    <div class="container">
        <h1>TikTok Authorization Successful</h1>
        <p>TikTok authorization has been completed successfully.</p>
        
        <!-- Code display section -->
        <div id="code-section">
            <h2>Authorization Code</h2>
            <div class="code-box" id="code-display">Loading...</div>
        </div>
        
        <!-- Token exchange section -->
        <div id="exchange-section">
            <h2>Token Exchange</h2>
            <p>Sending authorization code to your application...</p>
            <div id="exchange-status" class="status hidden"></div>
        </div>
    </div>

    <script>
        // Script to extract code from URL and send to backend
        // ...
    </script>
</body>
</html>
```

This page:
1. Extracts the authorization code from the URL
2. Displays it to the user
3. Automatically sends it to our backend endpoint
4. Shows the status of the token exchange process

To use this approach:
1. Create an HTML file with the above template
2. Deploy it to Netlify or another static hosting service
3. Set the deployed URL as your `TIKTOK_REDIRECT_URI` in your TikTok Developer Portal and environment variables

### TikTok Authentication Flow

1. **Start OAuth Flow:**
   ```
   GET /api/v1/auth/tiktok/authorize
   ```
   This endpoint will redirect the user to TikTok's authorization page

2. **Handle Callback:**
   ```
   GET /api/v1/auth/tiktok/callback?code=<AUTH_CODE>
   ```
   TikTok redirects back to your Netlify-hosted callback page with an auth code

3. **Exchange for Access Token:**
   The callback page sends the code to your backend endpoint:
   ```
   POST /api/v1/auth/tiktok/exchange-token
   ```

4. **Store Tokens:**
   Tokens are securely stored and associated with the user account, with proper timezone handling for expiration times

### Publishing TikTok Content

1. **Create a TikTok Post:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/tiktok/posts/ \
        -H "Authorization: Bearer <JWT_TOKEN>" \
        -H "Content-Type: multipart/form-data" \
        -F "content=Check out my new video!" \
        -F "scheduled_time=2025-04-10T15:30:00Z" \
        -F "video=@/path/to/video.mp4"
   ```

2. **Publish Immediately:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/tiktok/posts/1/publish \
        -H "Authorization: Bearer <JWT_TOKEN>"
   ```

---

## Database Schema

The current database schema includes the following tables:

### Users Table
```
Table: users
- id (Integer, Primary Key)
- username (String, Unique)
- email (String, Unique)
- hashed_password (String)
- is_active (Boolean)
- is_superuser (Boolean)
- created_at (DateTime)
- updated_at (DateTime)
- tiktok_access_token (String, Nullable)
- tiktok_refresh_token (String, Nullable)
- tiktok_open_id (String, Nullable)
- tiktok_token_expires_at (DateTime with timezone, Nullable)
```

### Posts Table
```
Table: posts
- id (Integer, Primary Key)
- content (Text)
- scheduled_time (DateTime)
- created_at (DateTime)
- updated_at (DateTime)
- platform (String)
- status (String) - "scheduled", "published", "failed"
- user_id (Integer, Foreign Key to users.id)
- video_filename (String, Nullable)
```

### Database Migration

The project uses Alembic for database migrations:

```bash
# Generate a new migration
alembic revision --autogenerate -m "description of changes"

# Apply all pending migrations
alembic upgrade head

# Revert to a specific migration
alembic downgrade <revision>
```

---

## Development Notes

- The application uses async/await for non-blocking database operations
- SQLAlchemy 2.0 syntax is used throughout the project
- Database tables are automatically created at startup with retry logic for reliability
- Failed connection attempts to the database will be retried with exponential backoff
- All endpoints follow RESTful principles
- The application uses Pydantic for data validation and serialization

### Code Style

This project follows these coding standards:
- PEP 8 style guide for Python code
- Type hints for function parameters and return values
- Docstrings for all functions, classes, and modules
- Consistent error handling with try/except blocks
- Async/await patterns for database operations and external API calls

### Error Handling

The application implements a consistent error handling strategy:
- Custom middleware for centralized error handling
- HTTP exceptions with appropriate status codes
- Detailed error messages with proper security considerations
- Logging of errors with contextual information
- Database transaction rollback in case of errors

### Dependency Injection

The project uses FastAPI's dependency injection system for:
- Database session management
- User authentication
- Authorization checks
- Configuration loading

---

## Implementation Challenges & Solutions

During the development of the TikTok integration, I encountered several significant challenges. Documenting these issues and their solutions may help others implementing similar OAuth flows.

### TikTok OAuth Challenges

#### 1. Redirect URI Requirements
- **Issue**: TikTok rejected localhost URLs for OAuth redirects, preventing local testing
- **Solution**: Set up a Netlify site with HTTPS for the callback page
- **Implementation**: Created a static HTML page that handles the OAuth callback, deployed on Netlify

#### 2. Token Storage Timezone Issues
- **Issue**: Encountered database errors with timezone-aware datetimes
- **Error**: "can't subtract offset-naive and offset-aware datetimes"
- **Solution**: 
  - Created a migration script to update the database column type
  - Modified the User model to use DateTime(timezone=True)
  - Updated all datetime handling to be consistently timezone-aware
- **Code Example**:
  ```python
  # Before
  expires_at = Column(DateTime)
  
  # After
  expires_at = Column(DateTime(timezone=True))
  ```

#### 3. CORS Limitations
- **Issue**: Browser security prevented the Netlify callback page from making direct requests to localhost
- **Solution**: Implemented a manual code exchange process instead of automatic
- **Implementation**: 
  - Created a mechanism for users to copy and paste the authorization code
  - Added an API endpoint specifically for manual code exchange

#### 4. Authentication Challenges
- **Issue**: Needed to locate and update test user credentials for API authentication
- **Solution**: Used direct database access to verify and update user information
- **Implementation**:
  - Created admin scripts to manage test user accounts
  - Added logging to track authentication flow

#### 5. Environment Variables and Configuration
- **Issue**: Initial issues with environment variables not being properly loaded
- **Solutions**:
  - Fixed configuration problems with the lifespan parameter in FastAPI setup
  - Implemented a more robust environment variable loading system
  - Added validation to ensure all required variables are present
- **Code Example**:
  ```python
  # Check for required environment variables on startup
  @app.on_event("startup")
  async def validate_env_vars():
      required_vars = [
          "TIKTOK_CLIENT_KEY", 
          "TIKTOK_CLIENT_SECRET",
          "TIKTOK_REDIRECT_URI"
      ]
      
      missing = [var for var in required_vars if not os.getenv(var)]
      if missing:
          raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
  ```

These challenges are typical when implementing OAuth integrations, especially when dealing with the complexities of secure authentication flows, timezone handling, and cross-domain communications between different environments (development vs. production).

---

## Project Journey & Development Timeline

This project has evolved through several key phases and milestones:

- **Initial Development (2 months ago)**
  - Added initial version of social media scheduler API
  - Set up basic FastAPI structure and endpoints
  - Established core model structure for social media posts
  - Implemented PostgreSQL integration with SQLAlchemy async ORM

- **TikTok Integration (last month)**
  - Added TikTok OAuth integration with user authentication
  - Configured environment variables for TikTok API integration
  - Created custom OAuth callback page for TikTok authorization
  - Deployed OAuth callback page to Netlify for production use
  - Implemented token exchange and storage mechanism

- **Optimization & Fixes (2 weeks ago)**
  - Fixed timezone handling in TikTok token storage and exchange
  - Improved error handling for API requests to TikTok
  - Implemented token refresh mechanism for expired TikTok tokens
  - Enhanced logging for debugging OAuth flow

- **Recent Additions**
  - Completed TikTok integration testing with real accounts
  - Added .gitignore for video files and uploads directory
  - Fixed edge cases in OAuth error handling
  - Improved Docker configuration for development environment
  - Documented API endpoints and TikTok integration process
  - Added setup instructions for local and Docker environments

This development timeline reflects our iterative approach, with a focus first on core functionality, followed by platform-specific integrations, and continuous improvement based on testing and real-world usage.

---

## Deployment Guide

### Netlify Deployment for TikTok OAuth Callback

The TikTok OAuth callback page is deployed on Netlify for reliable hosting:

1. **Create a Netlify account** at [netlify.com](https://www.netlify.com/)

2. **Deploy the callback page:**
   - Option 1: Drag and drop the HTML file directly into Netlify's dashboard
   - Option 2: Push the HTML file to a GitHub repository and connect it to Netlify

3. **Configure domain settings:**
   - Use the default Netlify subdomain (e.g., `your-app-name.netlify.app`) or
   - Set up a custom domain in the Netlify dashboard

4. **Update your environment variables:**
   ```
   TIKTOK_REDIRECT_URI=https://your-app-name.netlify.app
   ```

5. **Update TikTok Developer Portal:**
   - Add the Netlify URL to the allowed redirect URIs in your TikTok application settings

### Docker-based Deployment

1. **Clone the repository on your server:**
   ```bash
   git clone https://github.com/yourusername/social-media-scheduler.git
   cd social-media-scheduler
   ```

2. **Create production .env file with secure credentials**

3. **Start the application:**
   ```bash
   docker-compose up -d
   ```

### Cloud Infrastructure with AWS and Terraform

TikTimer's cloud infrastructure is built on AWS using Terraform for Infrastructure as Code (IaC). This approach ensures consistent, reproducible deployments and simplifies infrastructure management. The infrastructure is designed to be scalable, secure, and cost-efficient.

### Infrastructure Architecture

Our AWS infrastructure consists of the following components:

#### Networking
- VPC with public and private subnets across multiple Availability Zones
- Internet Gateway for public subnet internet access
- NAT Gateway (cost-optimized with a single instance) for private subnet outbound traffic
- Route Tables for controlling traffic flow
- Security Groups for network traffic control
- VPC Endpoints for S3 and DynamoDB to reduce data transfer costs

#### Database
- RDS PostgreSQL for persistent data storage
- Database Subnet Group in private subnets for security
- Parameter Group for database configuration
- Security Group restricting access to the application tier only

#### Storage
- S3 Bucket for video uploads and media storage
- Server-side encryption for data protection
- Lifecycle policies for cost-efficient storage management
- CORS configuration for frontend access

#### Compute
- ECS Fargate for containerized application deployment
- Task Definition for the FastAPI application
- ECS Service for managing container deployment
- Application Load Balancer for traffic distribution
- Target Groups for routing requests to containers
- IAM Roles with appropriate permissions

#### Security
- Security Groups for network isolation
- IAM Roles following the principle of least privilege
- Encryption for data at rest and in transit
- Private Subnets for sensitive resources

### Terraform Implementation

The infrastructure is defined as code using Terraform and organized into modular components:

```
tiktimer-infrastructure/
├── terraform-backend/       # Terraform state backend
├── modules/                 # Terraform modules
│   ├── networking/          # VPC, subnets, security groups
│   ├── database/            # RDS PostgreSQL
│   ├── storage/             # S3 buckets
│   ├── compute/             # ECS, ALB
│   └── security/            # Additional security resources
├── main.tf                  # Main Terraform configuration
├── variables.tf             # Input variables
├── outputs.tf               # Output values
└── terraform.tfvars         # Variable values
```

### Module Details

#### Networking Module
- Creates VPC with CIDR block 10.0.0.0/16
- Provisions public and private subnets across availability zones
- Sets up Internet Gateway and NAT Gateway
- Configures route tables for each subnet tier
- Implements security groups for web, application, and database tiers
- Creates VPC Endpoints for S3 and DynamoDB

#### Database Module
- Provisions RDS PostgreSQL instance
- Creates database subnet group in private subnets
- Sets up parameter group for PostgreSQL configuration
- Implements security group allowing access only from application tier
- Configures backups and storage settings

#### Storage Module
- Creates S3 bucket for video uploads
- Implements server-side encryption
- Sets up lifecycle policies for cost management
- Configures CORS for frontend access
- Blocks public access for security

#### Compute Module
- Creates ECS Fargate cluster
- Defines task definition for the FastAPI application
- Sets up ECS service with desired task count
- Provisions Application Load Balancer in public subnets
- Configures target groups and health checks
- Implements IAM roles for task execution and task permissions

#### Security Module
- Creates additional security resources
- Implements WAF for web application protection (optional)
- Sets up GuardDuty for threat detection (optional)
- Configures Security Hub for security standards compliance (optional)

### Cost Optimization

Several cost optimization measures have been implemented:

- **Single NAT Gateway**: Using one NAT Gateway instead of one per AZ (saves ~$65-70/month)
- **Free VPC Endpoints**: S3 and DynamoDB endpoints to reduce NAT Gateway data transfer costs
- **Right-sized Resources**: Appropriate instance sizes for development environment
- **Lifecycle Policies**: Automatic transition to cheaper storage classes for older data
- **Fargate Spot (planned)**: For non-critical workloads to reduce compute costs

### Deployment Instructions

#### Prerequisites
- AWS CLI configured with appropriate credentials
- Terraform v1.5.0+ installed
- Git for version control

#### Setting Up the Backend
First, set up the Terraform backend for state management:

```bash
# Clone the repository
git clone https://github.com/Shereefo/social-media-scheduler.git
cd social-media-scheduler/tiktimer-infrastructure/terraform-backend

# Initialize and apply Terraform
terraform init
terraform apply
```

#### Deploying the Main Infrastructure
After setting up the backend, deploy the main infrastructure:

```bash
# Navigate to the main infrastructure directory
cd ..

# Initialize Terraform with the S3 backend
terraform init

# Review the execution plan
terraform plan

# Apply the configuration
terraform apply
```

#### Clean Up Resources
To avoid ongoing charges when not using the infrastructure:

```bash
terraform destroy
```

### Implementation Challenges & Solutions

During the implementation of the AWS infrastructure with Terraform, we encountered and solved several challenges:

#### NAT Gateway Cost Management
- **Challenge**: NAT Gateways are relatively expensive ($32-35/month per gateway).
- **Solution**: Implemented a single NAT Gateway architecture, reducing costs by approximately 66% compared to one per AZ, while maintaining reasonable availability for development.

#### Terraform State Management
- **Challenge**: Team collaboration on infrastructure code requires shared state.
- **Solution**: Set up S3 backend with DynamoDB locking, allowing multiple team members to work on the infrastructure safely.

#### Database Security
- **Challenge**: Ensuring the database is not exposed to the public internet.
- **Solution**: Placed RDS in private subnets and configured security groups to only allow connections from the application tier.

#### Container Configuration
- **Challenge**: Passing sensitive configuration securely to containers.
- **Solution**: Used AWS Systems Manager Parameter Store for secrets and configured the ECS task definition to retrieve them securely at runtime.

### Future Enhancements

The following infrastructure components are planned for future implementation:

#### CI/CD Pipeline
- GitHub Actions workflow for automated deployments
- Staging and production environments
- Infrastructure validation tests

#### Advanced Monitoring
- CloudWatch dashboards for key metrics
- CloudWatch alarms for critical thresholds
- Log metric filters for application insights

#### DNS and SSL
- Route 53 for domain management
- ACM for SSL/TLS certificates
- HTTPS enforcement

#### Enhanced Security
- WAF for web application protection
- GuardDuty for threat detection
- Security Hub for compliance monitoring

#### Cost Management
- Reserved Instances for production workloads
- Auto-scaling based on usage patterns
- Scheduled scaling for predictable workloads

---

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running and accessible
- Check database credentials in your `.env` file
- Verify that Docker containers are on the same network
- Examine Docker logs: `docker-compose logs db`
- Check for database initialization errors: `docker-compose logs api`

### API Connection Issues
- Verify the API container is running: `docker ps`
- Check logs for API initialization errors: `docker-compose logs api`
- Verify that port 8000 is not being used by another application
- Test a basic endpoint with curl: `curl http://localhost:8000/`

### TikTok Authentication Issues
- Verify your TikTok API credentials in `.env`
- Ensure your redirect URI matches what's configured in the TikTok developer console
- Check application logs for detailed error messages from TikTok API calls
- Verify scope permissions in your TikTok developer console
- If the callback page isn't receiving the code, check your browser console for errors
- Verify the Netlify deployment is working by visiting the URL directly
- Check that CORS is properly configured in your FastAPI application:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://your-netlify-app.netlify.app", "http://localhost:3000"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

### Docker Issues
- Restart Docker: `docker-compose down && docker-compose up --build`
- Remove Docker volumes to start fresh: `docker-compose down -v`
- Check Docker logs: `docker-compose logs`
- Verify Docker and Docker Compose versions are up to date

### Alembic Migration Issues
- Check that your alembic.ini file points to the correct database URL
- Verify that all model changes are imported in the migrations/env.py file
- For complex migrations, consider writing manual migration scripts

---

## Current Project Status

The project is currently in active development with the following components implemented:
- ✅ Core API framework with FastAPI
- ✅ Database models and migrations with SQLAlchemy and Alembic
- ✅ User authentication system
- ✅ TikTok OAuth integration
- ✅ Post scheduling and management
- ✅ File upload and storage system
- ✅ Background task processing
- ✅ Docker containerization
- ✅ Error handling middleware
- ✅ Health check endpoints
- ✅ AWS infrastructure code with Terraform modules

## Next Steps

### Phase 1: Core Infrastructure & Operations
- [ ] Set up CI/CD pipeline with GitHub Actions
- [ ] Migrate file storage from local to S3 for production
- [ ] Add comprehensive test suite (unit, integration, E2E)
- [ ] Implement rate limiting and request throttling
- [ ] Optimize AWS infrastructure costs and implement auto-scaling

### Phase 2: User Experience & Frontend
- [ ] Create a frontend interface using React or Vue.js
- [ ] Add proper user management with roles and permissions
- [ ] Add admin dashboard for user management
- [ ] Enhance documentation with examples and usage scenarios

### Phase 3: Feature Expansion
- [ ] Implement advanced scheduling features (recurring posts, post series)
- [ ] Add additional social media platform integrations (Twitter, Instagram, etc.)
- [ ] Implement analytics for post performance

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
