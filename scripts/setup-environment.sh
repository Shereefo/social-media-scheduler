#!/bin/bash
# scripts/setup-environment.sh

echo "TikTimer Environment Setup"
echo "========================="

# Check required tools
echo "Checking required tools..."

if command -v docker >/dev/null 2>&1; then
    echo "[SUCCESS] Docker is installed"
else
    echo "[ERROR] Docker not installed - please install Docker first"
    exit 1
fi

if command -v docker-compose >/dev/null 2>&1; then
    echo "[SUCCESS] Docker Compose is installed"
else
    echo "[ERROR] Docker Compose not installed"
    exit 1
fi

if command -v aws >/dev/null 2>&1; then
    echo "[SUCCESS] AWS CLI is installed"
else
    echo "[INFO] AWS CLI not found (optional for local development)"
fi

# Check if .env file exists
echo ""
echo "Setting up environment configuration..."

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "[INFO] Creating .env from template..."
        cp .env.example .env
        echo "[SUCCESS] .env file created from template"
        echo "[WARNING] Please edit .env with your actual configuration values"
    else
        echo "[ERROR] No .env.example found - please create environment configuration"
    fi
else
    echo "[SUCCESS] .env file already exists"
fi

# Check if Docker is running
echo ""
echo "Checking Docker status..."

if docker info >/dev/null 2>&1; then
    echo "[SUCCESS] Docker daemon is running"
else
    echo "[ERROR] Docker daemon is not running - please start Docker"
    exit 1
fi

# Start services
echo ""
echo "[INFO] Starting Docker services..."

if docker-compose up -d; then
    echo "[SUCCESS] Docker services started successfully"

    # Wait a moment for services to initialize
    echo "[INFO] Waiting for services to initialize..."
    sleep 5

    # Check if API is accessible
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "[SUCCESS] API is responding at http://localhost:8000"
        echo "[INFO] API documentation available at http://localhost:8000/docs"
    else
        echo "[WARNING] API may still be starting up - check logs if needed"
        echo "[INFO] Run 'docker-compose logs api' to check API logs"
    fi
else
    echo "[ERROR] Failed to start Docker services"
    exit 1
fi

echo ""
echo "[SUCCESS] Setup complete!"
echo ""
echo "Next steps:"
echo "  - Visit http://localhost:8000 for the API"
echo "  - Visit http://localhost:8000/docs for API documentation"
echo "  - Run './scripts/check-services.py' to verify all services"
echo "  - Run './scripts/view-logs.sh' to view application logs"