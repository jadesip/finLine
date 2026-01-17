"""
Tests for LBO analysis functionality.
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestLBOAnalysis:
    """Tests for LBO analysis endpoint."""

    async def test_analyze_project(self, client: AsyncClient, auth_headers: dict, sample_project: dict):
        """Test running LBO analysis on a project."""
        project_id = sample_project["id"]

        response = await client.post(
            f"/api/projects/{project_id}/analyze?case_id=base_case",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "summary" in data
        assert "sources_uses" in data
        assert "debt_schedules" in data  # Note: plural
        assert "annual_cash_flows" in data  # Note: different key

        # Check summary metrics exist and are reasonable
        summary = data["summary"]
        assert "moic" in summary
        assert "irr" in summary
        assert "entry_equity" in summary
        assert "exit_proceeds" in summary

        # MOIC should be > 1 for a profitable deal
        assert summary["moic"] > 1.0

        # IRR should be positive for a profitable deal
        assert summary["irr"] > 0

    async def test_analyze_returns_reasonable_values(self, client: AsyncClient, auth_headers: dict, sample_project: dict):
        """Test that analysis returns reasonable financial values."""
        project_id = sample_project["id"]

        response = await client.post(
            f"/api/projects/{project_id}/analyze?case_id=base_case",
            headers=auth_headers
        )
        data = response.json()
        summary = data["summary"]

        # Entry: 8x EBITDA of 25 = 200, less 100 debt = 100 equity (roughly)
        assert 80 < summary["entry_equity"] < 150

        # IRR for a 5-year ~3x MOIC should be ~25-35%
        assert 0.20 < summary["irr"] < 0.50

        # MOIC should be 2-5x for this deal
        assert 2.0 < summary["moic"] < 5.0

    async def test_analyze_missing_data(self, client: AsyncClient, auth_headers: dict):
        """Test analysis fails gracefully with missing data."""
        # Create empty project
        create_response = await client.post(
            "/api/projects",
            json={"name": "Empty Project"},
            headers=auth_headers
        )
        project_id = create_response.json()["id"]

        response = await client.post(
            f"/api/projects/{project_id}/analyze?case_id=base_case",
            headers=auth_headers
        )
        # Should return error, not crash
        assert response.status_code in [200, 400]
        data = response.json()
        if response.status_code == 200:
            # If 200, should indicate failure
            assert data.get("success") is False or "error" in data
        else:
            # If 400, should have detail
            assert "detail" in data

    async def test_analyze_nonexistent_case(self, client: AsyncClient, auth_headers: dict, sample_project: dict):
        """Test analyzing nonexistent case returns error."""
        project_id = sample_project["id"]

        response = await client.post(
            f"/api/projects/{project_id}/analyze?case_id=nonexistent_case",
            headers=auth_headers
        )
        assert response.status_code in [200, 400]
        data = response.json()
        # Should indicate failure somehow
        if response.status_code == 200:
            assert data.get("success") is False
        else:
            assert "detail" in data


class TestSourcesUses:
    """Tests for Sources & Uses calculations."""

    async def test_sources_uses_balance(self, client: AsyncClient, auth_headers: dict, sample_project: dict):
        """Test that sources equal uses."""
        project_id = sample_project["id"]

        response = await client.post(
            f"/api/projects/{project_id}/analyze?case_id=base_case",
            headers=auth_headers
        )
        data = response.json()
        sources_uses = data["sources_uses"]

        # Sources should equal uses (within floating point tolerance)
        # Note: The API returns totals inside the sources/uses dicts
        total_sources = sources_uses["sources"].get("total_sources", sum(
            v for k, v in sources_uses["sources"].items() if k != "total_sources"
        ))
        total_uses = sources_uses["uses"].get("total_uses", sum(
            v for k, v in sources_uses["uses"].items() if k != "total_uses"
        ))
        assert abs(total_sources - total_uses) < 0.01

    async def test_sources_includes_debt_and_equity(self, client: AsyncClient, auth_headers: dict, sample_project: dict):
        """Test that sources include both debt and equity."""
        project_id = sample_project["id"]

        response = await client.post(
            f"/api/projects/{project_id}/analyze?case_id=base_case",
            headers=auth_headers
        )
        data = response.json()
        sources = data["sources_uses"]["sources"]

        # Should have debt (100M) and equity
        total_debt = sum(v for k, v in sources.items() if "debt" in k.lower() or "loan" in k.lower() or "senior" in k.lower())
        total_equity = sum(v for k, v in sources.items() if "equity" in k.lower())

        assert total_debt > 0
        assert total_equity > 0


class TestDebtSchedule:
    """Tests for debt schedule calculations."""

    async def test_debt_schedule_structure(self, client: AsyncClient, auth_headers: dict, sample_project: dict):
        """Test debt schedule has correct structure."""
        project_id = sample_project["id"]

        response = await client.post(
            f"/api/projects/{project_id}/analyze?case_id=base_case",
            headers=auth_headers
        )
        data = response.json()
        debt_schedules = data["debt_schedules"]

        # Should have at least one tranche
        assert len(debt_schedules) >= 1

        # Check first tranche has required fields
        first_tranche = list(debt_schedules.values())[0]
        required_fields = ["starting_balance", "balances", "principal_payments"]
        for field in required_fields:
            assert field in first_tranche, f"Missing {field} in debt schedule"

    async def test_debt_amortization(self, client: AsyncClient, auth_headers: dict, sample_project: dict):
        """Test that debt amortizes correctly."""
        project_id = sample_project["id"]

        response = await client.post(
            f"/api/projects/{project_id}/analyze?case_id=base_case",
            headers=auth_headers
        )
        data = response.json()
        debt_schedules = data["debt_schedules"]

        # Get first tranche balances
        first_tranche = list(debt_schedules.values())[0]
        balances = first_tranche.get("balances", {})
        years = sorted(balances.keys())

        if len(years) >= 2:
            # Balance should decrease over time with amortization
            first_balance = balances[years[0]]
            last_balance = balances[years[-1]]

            # With amortization, debt should decrease
            assert last_balance < first_balance


class TestExport:
    """Tests for Excel export functionality."""

    async def test_export_excel(self, client: AsyncClient, auth_headers: dict, sample_project: dict):
        """Test exporting project to Excel."""
        project_id = sample_project["id"]

        response = await client.post(
            f"/api/projects/{project_id}/export?case_id=base_case",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Check content length
        content = response.content
        assert len(content) > 1000  # Should be a reasonable size Excel file

    async def test_export_empty_project_fails(self, client: AsyncClient, auth_headers: dict):
        """Test that exporting empty project returns error."""
        # Create empty project
        create_response = await client.post(
            "/api/projects",
            json={"name": "Empty Export Test"},
            headers=auth_headers
        )
        project_id = create_response.json()["id"]

        response = await client.post(
            f"/api/projects/{project_id}/export?case_id=base_case",
            headers=auth_headers
        )
        # Should fail because analysis fails
        assert response.status_code == 400
