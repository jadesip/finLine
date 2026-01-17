"""
Tests for project endpoints.
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestProjectCRUD:
    """Tests for project CRUD operations."""

    async def test_create_project(self, client: AsyncClient, auth_headers: dict):
        """Test creating a new project."""
        response = await client.post(
            "/api/projects",
            json={
                "name": "My LBO Model",
                "company_name": "Acme Corp",
                "currency": "USD",
                "unit": "millions"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My LBO Model"
        assert "id" in data
        assert "data" in data
        assert data["data"]["meta"]["company_name"] == "Acme Corp"
        assert "base_case" in data["data"]["cases"]

    async def test_list_projects(self, client: AsyncClient, auth_headers: dict):
        """Test listing user's projects."""
        # Create some projects
        for i in range(3):
            await client.post(
                "/api/projects",
                json={"name": f"Project {i}"},
                headers=auth_headers
            )

        response = await client.get("/api/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_get_project(self, client: AsyncClient, auth_headers: dict):
        """Test getting a specific project."""
        # Create project
        create_response = await client.post(
            "/api/projects",
            json={"name": "Test Project"},
            headers=auth_headers
        )
        project_id = create_response.json()["id"]

        # Get project
        response = await client.get(f"/api/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["id"] == project_id

    async def test_get_nonexistent_project(self, client: AsyncClient, auth_headers: dict):
        """Test getting a nonexistent project returns 404."""
        response = await client.get(
            "/api/projects/nonexistent-id",
            headers=auth_headers
        )
        assert response.status_code == 404

    async def test_delete_project(self, client: AsyncClient, auth_headers: dict):
        """Test deleting a project."""
        # Create project
        create_response = await client.post(
            "/api/projects",
            json={"name": "To Delete"},
            headers=auth_headers
        )
        project_id = create_response.json()["id"]

        # Delete project
        response = await client.delete(f"/api/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 200

        # Verify deleted
        get_response = await client.get(f"/api/projects/{project_id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestProjectUpdates:
    """Tests for project update operations."""

    async def test_patch_project(self, client: AsyncClient, auth_headers: dict):
        """Test patching a single field."""
        # Create project
        create_response = await client.post(
            "/api/projects",
            json={"name": "Patch Test"},
            headers=auth_headers
        )
        project_id = create_response.json()["id"]

        # Patch
        response = await client.patch(
            f"/api/projects/{project_id}",
            json={
                "path": "cases.base_case.deal_parameters.tax_rate",
                "value": 0.30
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["cases"]["base_case"]["deal_parameters"]["tax_rate"] == 0.30

    async def test_bulk_update(self, client: AsyncClient, auth_headers: dict):
        """Test bulk updating multiple fields."""
        # Create project
        create_response = await client.post(
            "/api/projects",
            json={"name": "Bulk Test"},
            headers=auth_headers
        )
        project_id = create_response.json()["id"]

        # Bulk update
        response = await client.patch(
            f"/api/projects/{project_id}/bulk",
            json={
                "updates": [
                    {"path": "cases.base_case.deal_parameters.tax_rate", "value": 0.25},
                    {"path": "cases.base_case.deal_parameters.minimum_cash", "value": 10.0},
                    {"path": "meta.company_name", "value": "Updated Corp"}
                ]
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["cases"]["base_case"]["deal_parameters"]["tax_rate"] == 0.25
        assert data["data"]["cases"]["base_case"]["deal_parameters"]["minimum_cash"] == 10.0
        assert data["data"]["meta"]["company_name"] == "Updated Corp"


class TestCaseManagement:
    """Tests for case management."""

    async def test_add_case(self, client: AsyncClient, auth_headers: dict):
        """Test adding a new case."""
        # Create project
        create_response = await client.post(
            "/api/projects",
            json={"name": "Case Test"},
            headers=auth_headers
        )
        project_id = create_response.json()["id"]

        # Add case
        response = await client.post(
            f"/api/projects/{project_id}/cases/upside_case",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "upside_case" in data["data"]["cases"]
        assert "base_case" in data["data"]["cases"]

    async def test_delete_case(self, client: AsyncClient, auth_headers: dict):
        """Test deleting a case."""
        # Create project with multiple cases
        create_response = await client.post(
            "/api/projects",
            json={"name": "Delete Case Test"},
            headers=auth_headers
        )
        project_id = create_response.json()["id"]

        # Add a case first
        await client.post(
            f"/api/projects/{project_id}/cases/downside_case",
            headers=auth_headers
        )

        # Delete case
        response = await client.delete(
            f"/api/projects/{project_id}/cases/downside_case",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "downside_case" not in data["data"]["cases"]
        assert "base_case" in data["data"]["cases"]

    async def test_cannot_delete_only_case(self, client: AsyncClient, auth_headers: dict):
        """Test that deleting the only case fails."""
        # Create project
        create_response = await client.post(
            "/api/projects",
            json={"name": "Single Case"},
            headers=auth_headers
        )
        project_id = create_response.json()["id"]

        # Try to delete base_case
        response = await client.delete(
            f"/api/projects/{project_id}/cases/base_case",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "only case" in response.json()["detail"].lower()
