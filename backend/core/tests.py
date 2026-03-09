"""Tests for core views: auth, health check, change password."""

import pytest


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_check(self, client):
        res = client.get("/api/health/")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ("ok", "degraded")
        assert "database" in data
        assert "version" in data


@pytest.mark.django_db
class TestAuth:
    def test_login_success(self, client, user):
        res = client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "testpass123"},
            content_type="application/json",
        )
        assert res.status_code == 200
        assert res.json()["username"] == "testuser"

    def test_login_invalid(self, client, user):
        res = client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "wrong"},
            content_type="application/json",
        )
        assert res.status_code == 401

    def test_session_authenticated(self, auth_client):
        res = auth_client.get("/api/auth/session/")
        assert res.status_code == 200
        assert res.json()["username"] == "testuser"

    def test_session_unauthenticated(self, client):
        res = client.get("/api/auth/session/")
        assert res.status_code == 403


@pytest.mark.django_db
class TestChangePassword:
    def test_change_password_success(self, auth_client, user):
        res = auth_client.post(
            "/api/auth/change-password/",
            {"current_password": "testpass123", "new_password": "newpass456!"},
            content_type="application/json",
        )
        assert res.status_code == 200
        user.refresh_from_db()
        assert user.check_password("newpass456!")

    def test_change_password_wrong_current(self, auth_client):
        res = auth_client.post(
            "/api/auth/change-password/",
            {"current_password": "wrong", "new_password": "newpass456!"},
            content_type="application/json",
        )
        assert res.status_code == 400

    def test_change_password_too_short(self, auth_client):
        res = auth_client.post(
            "/api/auth/change-password/",
            {"current_password": "testpass123", "new_password": "short"},
            content_type="application/json",
        )
        assert res.status_code == 400
