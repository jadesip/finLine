"""
finLine Projects API

CRUD operations for projects with JSON data storage.
Single PATCH endpoint handles all updates.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from api.auth import CurrentUser
from database import (
    create_project as db_create_project,
    get_project as db_get_project,
    get_projects_by_user,
    update_project as db_update_project,
    delete_project as db_delete_project,
)
from models.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectBulkUpdate,
    ProjectResponse,
    ProjectListItem,
    SuccessResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def create_empty_project_data(name: str, user_id: str, company_name: str | None, currency: str, unit: str) -> dict[str, Any]:
    """Create empty project data structure."""
    now = datetime.utcnow().isoformat()
    project_id = str(uuid4())

    return {
        "meta": {
            "user_id": user_id,
            "project_id": project_id,
            "version": "1.0",
            "name": name,
            "company_name": company_name or "",
            "currency": currency,
            "unit": unit,
            "frequency": "annual",
            "financial_year_end": "December",
            "last_historical_period": "",
            "created_date": now,
            "last_modified": now,
        },
        "cases": {
            "base_case": create_empty_case("Base Case")
        }
    }


def create_empty_case(description: str) -> dict[str, Any]:
    """Create empty case structure."""
    return {
        "case_desc": description,
        "deal_parameters": {
            "deal_date": "",
            "exit_date": "",
            "tax_rate": 0.25,
            "minimum_cash": 0.0,
            "entry_fee_percentage": 2.0,
            "exit_fee_percentage": 2.0,
            "entry_valuation": {
                "method": "multiple",
                "metric": "EBITDA",
                "multiple": 8.0
            },
            "exit_valuation": {
                "method": "multiple",
                "metric": "EBITDA",
                "multiple": 8.0
            },
            "capital_structure": {
                "tranches": [],
                "reference_rate_curve": None
            },
            "equity_injection": None
        },
        "financials": {
            "income_statement": {
                "revenue": {},
                "ebitda": [],
                "ebit": [],
                "d_and_a": []
            },
            "cash_flow_statement": {
                "capex": {},
                "working_capital": {}
            }
        }
    }


def set_nested_value(data: dict, path: str, value: Any) -> None:
    """Set a value in a nested dict using dot notation path."""
    keys = path.split(".")
    current = data

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


def get_nested_value(data: dict, path: str) -> Any:
    """Get a value from a nested dict using dot notation path."""
    keys = path.split(".")
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None

    return current


# ============================================================
# Endpoints
# ============================================================

@router.get("", response_model=list[ProjectListItem])
async def list_projects(current_user: CurrentUser):
    """List all projects for current user."""
    logger.info(f"Listing projects for user: {current_user['id']}")
    projects = await get_projects_by_user(current_user["id"])
    return [ProjectListItem(**p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project_data: ProjectCreate, current_user: CurrentUser):
    """Create a new project."""
    logger.info(f"Creating project '{project_data.name}' for user: {current_user['id']}")

    project_id = str(uuid4())
    data = create_empty_project_data(
        name=project_data.name,
        user_id=current_user["id"],
        company_name=project_data.company_name,
        currency=project_data.currency,
        unit=project_data.unit
    )
    # Update the project_id in meta to match
    data["meta"]["project_id"] = project_id

    project = await db_create_project(
        project_id=project_id,
        user_id=current_user["id"],
        name=project_data.name,
        data=data
    )

    logger.info(f"Created project: {project_id}")
    return ProjectResponse(**project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: CurrentUser):
    """Get a project by ID."""
    logger.info(f"Getting project: {project_id}")

    project = await db_get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check ownership
    if project["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return ProjectResponse(**project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, update: ProjectUpdate, current_user: CurrentUser):
    """Update a project field using dot notation path."""
    logger.info(f"Updating project {project_id}: path={update.path}")

    project = await db_get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Apply update
    data = project["data"]
    old_value = get_nested_value(data, update.path)
    set_nested_value(data, update.path, update.value)

    # Update last_modified
    data["meta"]["last_modified"] = datetime.utcnow().isoformat()

    # Check if name changed
    new_name = None
    if update.path == "meta.name":
        new_name = update.value

    updated = await db_update_project(project_id, data, new_name)
    logger.info(f"Updated project {project_id}: {update.path} = {update.value} (was: {old_value})")

    return ProjectResponse(**updated)


@router.patch("/{project_id}/bulk", response_model=ProjectResponse)
async def bulk_update_project(project_id: str, updates: ProjectBulkUpdate, current_user: CurrentUser):
    """Bulk update multiple project fields."""
    logger.info(f"Bulk updating project {project_id}: {len(updates.updates)} updates")

    project = await db_get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Apply all updates
    data = project["data"]
    new_name = None

    for update in updates.updates:
        set_nested_value(data, update.path, update.value)
        if update.path == "meta.name":
            new_name = update.value
        logger.info(f"  - {update.path} = {update.value}")

    # Update last_modified
    data["meta"]["last_modified"] = datetime.utcnow().isoformat()

    updated = await db_update_project(project_id, data, new_name)
    logger.info(f"Bulk update complete for project {project_id}")

    return ProjectResponse(**updated)


@router.delete("/{project_id}", response_model=SuccessResponse)
async def delete_project(project_id: str, current_user: CurrentUser):
    """Delete a project."""
    logger.info(f"Deleting project: {project_id}")

    project = await db_get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    await db_delete_project(project_id)
    logger.info(f"Deleted project: {project_id}")

    return SuccessResponse(success=True, message="Project deleted")


@router.post("/{project_id}/cases/{case_id}", response_model=ProjectResponse)
async def add_case(project_id: str, case_id: str, current_user: CurrentUser):
    """Add a new case to a project."""
    logger.info(f"Adding case '{case_id}' to project {project_id}")

    project = await db_get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    data = project["data"]
    if case_id in data["cases"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case '{case_id}' already exists"
        )

    # Create new case
    case_desc = case_id.replace("_", " ").title()
    data["cases"][case_id] = create_empty_case(case_desc)
    data["meta"]["last_modified"] = datetime.utcnow().isoformat()

    updated = await db_update_project(project_id, data)
    logger.info(f"Added case '{case_id}' to project {project_id}")

    return ProjectResponse(**updated)


@router.delete("/{project_id}/cases/{case_id}", response_model=ProjectResponse)
async def delete_case(project_id: str, case_id: str, current_user: CurrentUser):
    """Delete a case from a project."""
    logger.info(f"Deleting case '{case_id}' from project {project_id}")

    project = await db_get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    data = project["data"]
    if case_id not in data["cases"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found"
        )

    if len(data["cases"]) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the only case"
        )

    del data["cases"][case_id]
    data["meta"]["last_modified"] = datetime.utcnow().isoformat()

    updated = await db_update_project(project_id, data)
    logger.info(f"Deleted case '{case_id}' from project {project_id}")

    return ProjectResponse(**updated)


# ============================================================
# LBO Analysis Endpoints
# ============================================================

@router.post("/{project_id}/analyze")
async def analyze_project(project_id: str, current_user: CurrentUser, case_id: str = "base_case"):
    """Run LBO analysis on a project case.

    Returns comprehensive analysis including:
    - Sources & Uses
    - Cash flow projections
    - Debt schedules
    - Returns (IRR, MOIC)
    """
    from engine import run_lbo_analysis

    logger.info(f"Running LBO analysis for project {project_id}, case {case_id}")

    project = await db_get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Run analysis
    result = await run_lbo_analysis(project["data"], case_id)

    if not result.get("success", False):
        logger.warning(f"Analysis failed: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Analysis failed")
        )

    logger.info(f"Analysis complete: MOIC={result['summary']['moic']:.2f}x, IRR={result['summary']['irr']:.1%}")
    return result


@router.post("/{project_id}/analyze/all")
async def analyze_all_cases(project_id: str, current_user: CurrentUser):
    """Run LBO analysis on all cases in a project."""
    from engine import run_lbo_analysis_all_cases

    logger.info(f"Running LBO analysis for all cases in project {project_id}")

    project = await db_get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Run analysis for all cases
    results = await run_lbo_analysis_all_cases(project["data"])

    # Summarize results
    summary = {}
    for case_id, result in results.items():
        if result.get("success", False):
            summary[case_id] = {
                "moic": result["summary"]["moic"],
                "irr": result["summary"]["irr"],
                "entry_equity": result["summary"]["entry_equity"],
                "exit_proceeds": result["summary"]["exit_proceeds"],
            }
        else:
            summary[case_id] = {"error": result.get("error", "Analysis failed")}

    logger.info(f"Analysis complete for {len(results)} cases")
    return {"cases": results, "summary": summary}


# ============================================================
# Export Endpoints
# ============================================================

@router.post("/{project_id}/export")
async def export_project(project_id: str, current_user: CurrentUser, case_id: str = "base_case"):
    """Export project analysis to Excel.

    Returns an Excel file with:
    - Summary sheet (key metrics, sources & uses)
    - Financials sheet (P&L, cash flow)
    - Debt Schedule sheet
    - Returns sheet
    """
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    from engine import run_lbo_analysis
    from services.excel import export_project_to_excel

    logger.info(f"Exporting project {project_id}, case {case_id} to Excel")

    project = await db_get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Run analysis first
    analysis_result = await run_lbo_analysis(project["data"], case_id)

    if not analysis_result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis failed: {analysis_result.get('error', 'Unknown error')}"
        )

    # Generate Excel
    excel_bytes = export_project_to_excel(project["data"], analysis_result, case_id)

    # Create filename
    project_name = project["name"].replace(" ", "_").lower()
    filename = f"{project_name}_{case_id}_analysis.xlsx"

    logger.info(f"Excel export complete: {filename}")

    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
