import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest

@pytest.fixture
def user_and_headers(client):
    client.post("/auth/register", json={
        "email": "agent@qa.com", "username": "agentqa", "password": "pass1234"
    })
    resp = client.post("/auth/login", json={"email": "agent@qa.com", "password": "pass1234"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def second_user_headers(client):
    client.post("/auth/register", json={
        "email": "other@qa.com", "username": "otherqa", "password": "pass1234"
    })
    resp = client.post("/auth/login", json={"email": "other@qa.com", "password": "pass1234"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestAgentRun:
    def test_run_unauthorized(self, client):
        resp = client.post("/agent/run", json={"task": "test"})
        assert resp.status_code in (401, 403)

    def test_run_bad_token(self, client):
        resp = client.post("/agent/run",
            json={"task": "test"},
            headers={"Authorization": "Bearer fake"}
        )
        assert resp.status_code == 401

    def test_run_saves_session(self, client, user_and_headers):
        client.post("/agent/run", json={"task": "What is AI?", "max_steps": 2},
                    headers=user_and_headers)
        sessions = client.get("/agent/sessions", headers=user_and_headers).json()
        assert len(sessions) >= 1

    def test_run_empty_task(self, client, user_and_headers):
        resp = client.post("/agent/run", json={"task": "", "max_steps": 3},
                            headers=user_and_headers)
        assert resp.status_code in (201, 422)

class TestAgentSessions:
    def _create_session(self, client, headers, task="Test task"):
        return client.post("/agent/run", json={"task": task, "max_steps": 2},
                           headers=headers)

    def test_get_sessions_empty(self, client, user_and_headers):
        resp = client.get("/agent/sessions", headers=user_and_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_sessions_after_run(self, client, user_and_headers):
        self._create_session(client, user_and_headers)
        resp = client.get("/agent/sessions", headers=user_and_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_sessions_isolated_between_users(self, client, user_and_headers, second_user_headers):
        self._create_session(client, user_and_headers, "User 1 task")
        resp = client.get("/agent/sessions", headers=second_user_headers)
        assert resp.json() == []

   

    def test_get_session_not_found(self, client, user_and_headers):
        resp = client.get("/agent/sessions/99999", headers=user_and_headers)
        assert resp.status_code == 404

    