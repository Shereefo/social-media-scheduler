"""Basic tests for the application."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Import the app
from backend.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Social Media Scheduler API"}


def test_health_endpoint():
    """Test the health check endpoint."""
    with patch("backend.database.async_session") as mock_session:
        # Mock the database session
        mock_session.return_value.__aenter__.return_value.execute = AsyncMock()
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "api_version" in data
        assert "timestamp" in data
        assert "database" in data


def test_posts_endpoint_requires_auth():
    """Test that posts endpoint requires authentication."""
    response = client.get("/posts/")
    assert response.status_code == 401


def test_register_endpoint_validation():
    """Test user registration endpoint with invalid data."""
    response = client.post("/register", json={})
    assert response.status_code == 422  # Validation error