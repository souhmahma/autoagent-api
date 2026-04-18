"""
Unit tests — security (JWT + password hashing)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from datetime import timedelta
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("secret123")
        assert hashed != "secret123"

    def test_hash_is_bcrypt(self):
        hashed = hash_password("secret123")
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_different_hashes(self):
        h1 = hash_password("samepass")
        h2 = hash_password("samepass")
        assert h1 != h2  # bcrypt salts

    def test_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True

    def test_long_password(self):
        long_pw = "a" * 100
        hashed = hash_password(long_pw)
        assert verify_password(long_pw, hashed) is True


class TestJWTTokens:
    def test_create_access_token_returns_string(self):
        token = create_access_token({"sub": "1", "role": "user"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        data = {"sub": "42", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded["sub"] == "42"
        assert decoded["role"] == "admin"
        assert decoded["type"] == "access"

    def test_create_refresh_token(self):
        token = create_refresh_token({"sub": "1"})
        decoded = decode_token(token)
        assert decoded["type"] == "refresh"

    def test_access_and_refresh_differ(self):
        data = {"sub": "1"}
        access = create_access_token(data)
        refresh = create_refresh_token(data)
        assert access != refresh

    def test_expired_token_returns_none(self):
        token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
        result = decode_token(token)
        assert result is None

    def test_invalid_token_returns_none(self):
        assert decode_token("not.a.valid.token") is None

    def test_tampered_token_returns_none(self):
        token = create_access_token({"sub": "1"})
        tampered = token[:-5] + "XXXXX"
        assert decode_token(tampered) is None

    def test_empty_token_returns_none(self):
        assert decode_token("") is None
