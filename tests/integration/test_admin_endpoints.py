import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from sqlalchemy.orm import sessionmaker
from app.models.user import User, UserRole
from app.core.security import hash_password


@pytest.fixture
def admin_headers(client, db_engine):
    Session = sessionmaker(bind=db_engine)
    db = Session()
    try:
        admin = db.query(User).filter(User.email == "admin@qa.com").first()
        if not admin:
            admin = User(
                email="admin@qa.com",
                username="adminqa",
                hashed_password=hash_password("adminpass"),
                role=UserRole.admin,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
    finally:
        db.close()

    resp = client.post("/auth/login", json={
        "email": "admin@qa.com",
        "password": "adminpass"
    })
    
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(client):
    client.post("/auth/register", json={
        "email": "user@qa.com", "username": "userqa", "password": "userpass"
    })
    resp = client.post("/auth/login", json={"email": "user@qa.com", "password": "userpass"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestAdminAccess:
    def test_admin_can_list_users(self, client, admin_headers):
        resp = client.get("/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_user_cannot_access_admin(self, client, user_headers):
        resp = client.get("/admin/users", headers=user_headers)
        assert resp.status_code == 403

    def test_unauthenticated_cannot_access_admin(self, client):
        resp = client.get("/admin/users")
        assert resp.status_code in (401, 403)

    def test_admin_sees_all_users(self, client, admin_headers, user_headers):
        resp = client.get("/admin/users", headers=admin_headers)
        assert len(resp.json()) >= 2

    def test_admin_can_get_stats(self, client, admin_headers):
        resp = client.get("/admin/stats", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "total_sessions" in data
        assert "success_rate" in data

    def test_admin_can_get_all_sessions(self, client, admin_headers):
        resp = client.get("/admin/sessions", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAdminUserManagement:
    def test_admin_can_deactivate_user(self, client, admin_headers, user_headers):
        users = client.get("/admin/users", headers=admin_headers).json()
        regular_user = next(u for u in users if u["role"] == "user")
        resp = client.patch(f"/admin/users/{regular_user['id']}",
                            json={"is_active": False}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_admin_can_promote_user(self, client, admin_headers, user_headers):
        users = client.get("/admin/users", headers=admin_headers).json()
        regular_user = next(u for u in users if u["role"] == "user")
        resp = client.patch(f"/admin/users/{regular_user['id']}",
                            json={"role": "admin"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_admin_can_delete_user(self, client, admin_headers, user_headers):
        users = client.get("/admin/users", headers=admin_headers).json()
        regular_user = next(u for u in users if u["role"] == "user")
        resp = client.delete(f"/admin/users/{regular_user['id']}", headers=admin_headers)
        assert resp.status_code == 204


    def test_update_nonexistent_user(self, client, admin_headers):
        resp = client.patch("/admin/users/99999", json={"is_active": False},
                            headers=admin_headers)
        assert resp.status_code == 404
