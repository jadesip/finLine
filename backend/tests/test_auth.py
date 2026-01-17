"""
Tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestAuthRegister:
    """Tests for POST /api/auth/register"""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        import time
        unique_email = f"newuser{int(time.time()*1000)}@example.com"
        response = await client.post(
            "/api/auth/register",
            json={"email": unique_email, "password": "SecurePass123"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == unique_email
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email fails."""
        # First registration
        await client.post(
            "/api/auth/register",
            json={"email": "duplicate@example.com", "password": "SecurePass123"}
        )

        # Second registration with same email
        response = await client.post(
            "/api/auth/register",
            json={"email": "duplicate@example.com", "password": "AnotherPass123"}
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/api/auth/register",
            json={"email": "not-an-email", "password": "SecurePass123"}
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with short password fails."""
        response = await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "short"}
        )
        assert response.status_code == 422


class TestAuthLogin:
    """Tests for POST /api/auth/login"""

    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # Register first
        await client.post(
            "/api/auth/register",
            json={"email": "logintest@example.com", "password": "SecurePass123"}
        )

        # Login
        response = await client.post(
            "/api/auth/login",
            data={"username": "logintest@example.com", "password": "SecurePass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_password(self, client: AsyncClient):
        """Test login with invalid password fails."""
        # Register first
        await client.post(
            "/api/auth/register",
            json={"email": "wrongpass@example.com", "password": "CorrectPass123"}
        )

        # Login with wrong password
        response = await client.post(
            "/api/auth/login",
            data={"username": "wrongpass@example.com", "password": "WrongPass123"}
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        response = await client.post(
            "/api/auth/login",
            data={"username": "nobody@example.com", "password": "SomePass123"}
        )
        assert response.status_code == 401


class TestAuthMe:
    """Tests for GET /api/auth/me"""

    async def test_me_authenticated(self, client: AsyncClient, auth_headers: dict):
        """Test /me endpoint with valid token."""
        response = await client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert "id" in data

    async def test_me_unauthenticated(self, client: AsyncClient):
        """Test /me endpoint without token fails."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        """Test /me endpoint with invalid token fails."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
