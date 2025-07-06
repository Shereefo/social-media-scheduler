"""Tests for authentication functionality."""
import pytest
from backend.auth import verify_password, get_password_hash, create_access_token


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = get_password_hash(password)
    
    # Hash should not be the same as original password
    assert hashed != password
    
    # Verification should work
    assert verify_password(password, hashed) is True
    
    # Wrong password should not verify
    assert verify_password("wrong_password", hashed) is False


def test_create_access_token():
    """Test JWT token creation."""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    # Token should be a string
    assert isinstance(token, str)
    
    # Token should have JWT structure (3 parts separated by dots)
    parts = token.split(".")
    assert len(parts) == 3


def test_password_hash_different_each_time():
    """Test that password hashes are different each time."""
    password = "same_password"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    # Hashes should be different due to salt
    assert hash1 != hash2
    
    # But both should verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True