import pytest
from app.core.security import get_password_hash, verify_password, create_access_token

def test_password_hashing():
    password = "admin123_test_password"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_create_access_token():
    token = create_access_token(subject="test_user_id")
    assert isinstance(token, str)
    assert len(token) > 10
