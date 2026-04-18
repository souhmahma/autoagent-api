import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def registered_user(client):
    payload = {"email": "test@qa.com", "username": "qauser", "password": "pass1234"}
    client.post("/auth/register", json=payload)
    return payload


@pytest.fixture
def auth_headers(client, registered_user):
    resp = client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "email": "new@test.com", "username": "newuser", "password": "pass123"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@test.com"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, registered_user):
        resp = client.post("/auth/register", json={
            "email": registered_user["email"],
            "username": "different",
            "password": "pass123"
        })
        assert resp.status_code == 400

    def test_register_duplicate_username(self, client, registered_user):
        resp = client.post("/auth/register", json={
            "email": "other@test.com",
            "username": registered_user["username"],
            "password": "pass123"
        })
        assert resp.status_code == 400

    def test_register_invalid_email(self, client):
        resp = client.post("/auth/register", json={
            "email": "not-an-email", "username": "user", "password": "pass"
        })
        assert resp.status_code == 422

    def test_register_missing_fields(self, client):
        resp = client.post("/auth/register", json={"email": "x@x.com"})
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client, registered_user):
        resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post("/auth/login", json={
            "email": "ghost@test.com", "password": "pass"
        })
        assert resp.status_code == 401

    def test_login_returns_jwt(self, client, registered_user):
        resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        token = resp.json()["access_token"]
        assert len(token.split(".")) == 3


class TestRefresh:
    def test_refresh_success(self, client, registered_user):
        login = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        refresh_token = login.json()["refresh_token"]
        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_invalid_token(self, client):
        resp = client.post("/auth/refresh", json={"refresh_token": "bad.token.here"})
        assert resp.status_code == 401

    def test_refresh_with_access_token_fails(self, client, registered_user):
        login = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        access = login.json()["access_token"]
        resp = client.post("/auth/refresh", json={"refresh_token": access})
        assert resp.status_code == 401


class TestMe:
    def test_me_authenticated(self, client, registered_user, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == registered_user["email"]

    def test_me_no_token(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code in (401, 403)

    def test_me_bad_token(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer fake"})
        assert resp.status_code == 401
