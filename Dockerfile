FROM python:3.12-slim

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create __init__.py files if they don't exist
RUN touch backend/__init__.py

# Install the app in development mode to resolve import issues
RUN pip install -e .

# Command to run the FastAPI app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]