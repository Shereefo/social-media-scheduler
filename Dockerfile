FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create __init__.py files if they don't exist
RUN touch backend/__init__.py
RUN touch backend/integrations/__init__.py
RUN touch backend/routes/__init__.py

# Install the app
RUN pip install -e .

# Create upload directory
RUN mkdir -p uploads && chmod 777 uploads

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the FastAPI app (without reload in production)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]