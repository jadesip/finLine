"""
Pytest configuration and fixtures for finLine tests.
"""

import asyncio
import os
import pytest
from httpx import AsyncClient, ASGITransport

# Set test environment before importing app
os.environ["DATABASE_PATH"] = ":memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"

from main import app
from database import init_db


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def client():
    """Create test client with fresh database."""
    # Initialize fresh database for each test
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient):
    """Create authenticated user and return headers with token."""
    # Register user
    await client.post(
        "/api/auth/register",
        json={"email": "testuser@example.com", "password": "TestPass123"}
    )

    # Login
    response = await client.post(
        "/api/auth/login",
        data={"username": "testuser@example.com", "password": "TestPass123"}
    )
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def sample_project(client: AsyncClient, auth_headers: dict):
    """Create a sample project with financial data."""
    # Create project
    response = await client.post(
        "/api/projects",
        json={
            "name": "Test LBO",
            "company_name": "TestCorp",
            "currency": "USD",
            "unit": "millions"
        },
        headers=auth_headers
    )
    project = response.json()
    project_id = project["id"]

    # Add financial data
    await client.patch(
        f"/api/projects/{project_id}/bulk",
        json={
            "updates": [
                {
                    "path": "cases.base_case.financials.income_statement.revenue",
                    "value": [
                        {"year": "2024", "value": 100},
                        {"year": "2025", "value": 110},
                        {"year": "2026", "value": 121},
                        {"year": "2027", "value": 133},
                        {"year": "2028", "value": 146}
                    ]
                },
                {
                    "path": "cases.base_case.financials.income_statement.ebitda",
                    "value": [
                        {"year": "2024", "value": 25},
                        {"year": "2025", "value": 28},
                        {"year": "2026", "value": 31},
                        {"year": "2027", "value": 34},
                        {"year": "2028", "value": 37}
                    ]
                },
                {
                    "path": "cases.base_case.financials.cash_flow_statement.capex",
                    "value": [
                        {"year": "2024", "value": 5},
                        {"year": "2025", "value": 5},
                        {"year": "2026", "value": 6},
                        {"year": "2027", "value": 6},
                        {"year": "2028", "value": 7}
                    ]
                },
                {
                    "path": "cases.base_case.deal_parameters.deal_date",
                    "value": "2024-01-01"
                },
                {
                    "path": "cases.base_case.deal_parameters.exit_date",
                    "value": "2028-12-31"
                },
                {
                    "path": "cases.base_case.deal_parameters.entry_valuation",
                    "value": {"method": "multiple", "metric": "EBITDA", "multiple": 8.0}
                },
                {
                    "path": "cases.base_case.deal_parameters.exit_valuation",
                    "value": {"method": "multiple", "metric": "EBITDA", "multiple": 9.0}
                },
                {
                    "path": "cases.base_case.deal_parameters.capital_structure.tranches",
                    "value": [
                        {
                            "tranche_id": "senior",
                            "label": "Senior Debt",
                            "type": "term_loan",
                            "currency": "USD",
                            "original_size": 100,
                            "amount": 100,
                            "interest_rate": 0.06,
                            "amortization_rate": 0.10
                        }
                    ]
                }
            ]
        },
        headers=auth_headers
    )

    # Fetch updated project
    response = await client.get(f"/api/projects/{project_id}", headers=auth_headers)
    return response.json()
