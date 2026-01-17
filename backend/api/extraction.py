"""
finLine Document Extraction API

Endpoints for uploading documents and extracting financial data.
"""

import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from api.auth import CurrentUser
from database import get_project as db_get_project, update_project as db_update_project
from services.extraction import DocumentExtractor

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for extraction results (replace with DB in production)
EXTRACTION_RESULTS: dict[str, dict[str, Any]] = {}


class ExtractionResponse(BaseModel):
    """Response for extraction status."""
    extraction_id: str
    status: str
    message: str
    progress: int = 0
    result: dict[str, Any] | None = None


class MergeRequest(BaseModel):
    """Request to merge extracted data."""
    merge_strategy: str = "overlay"  # overlay, replace, manual


# ============================================================
# Endpoints
# ============================================================

@router.post("/{project_id}/extract", response_model=ExtractionResponse)
async def extract_from_document(
    project_id: str,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    extract_immediately: bool = Form(True),
):
    """
    Upload and extract financial data from a document.

    Accepts PDF and image files (PNG, JPG).
    Returns extraction ID for tracking progress.
    """
    logger.info(f"Extraction request for project {project_id}: {file.filename}")

    # Verify project exists and user has access
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

    # Validate file type
    allowed_types = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
    }
    content_type = file.content_type or ""
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, PNG, JPG"
        )

    # Read file
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    logger.info(f"Received file: {file.filename} ({file_size_mb:.2f}MB)")

    if file_size_mb > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 50MB."
        )

    extraction_id = str(uuid4())

    if extract_immediately:
        # Run extraction synchronously
        try:
            extractor = DocumentExtractor()
            result = await extractor.extract_from_file(
                file_bytes,
                file.filename or "document.pdf",
                extraction_id
            )

            # Store result
            EXTRACTION_RESULTS[extraction_id] = {
                "status": "completed",
                "progress": 100,
                "project_id": project_id,
                "raw_data": result.raw_data,
                "mapped_data": result.mapped_data,
                "insights_data": result.insights_data,
                "metadata": {
                    "extraction_id": result.metadata.extraction_id,
                    "file_name": result.metadata.file_name,
                    "file_type": result.metadata.file_type,
                    "file_size_mb": result.metadata.file_size_mb,
                    "extraction_time_seconds": result.metadata.extraction_time_seconds,
                },
            }

            return ExtractionResponse(
                extraction_id=extraction_id,
                status="completed",
                message="Extraction completed successfully",
                progress=100,
                result=EXTRACTION_RESULTS[extraction_id]
            )

        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            EXTRACTION_RESULTS[extraction_id] = {
                "status": "failed",
                "progress": 0,
                "error": str(e),
            }
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Extraction failed: {str(e)}"
            )
    else:
        # Store pending extraction
        EXTRACTION_RESULTS[extraction_id] = {
            "status": "pending",
            "progress": 0,
            "project_id": project_id,
            "file_name": file.filename,
        }

        return ExtractionResponse(
            extraction_id=extraction_id,
            status="pending",
            message="Extraction queued. Use GET endpoint to check status.",
            progress=0
        )


@router.get("/{project_id}/extractions/{extraction_id}", response_model=ExtractionResponse)
async def get_extraction_status(
    project_id: str,
    extraction_id: str,
    current_user: CurrentUser,
):
    """Get status of an extraction."""
    # Verify project access
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

    # Get extraction result
    if extraction_id not in EXTRACTION_RESULTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )

    result = EXTRACTION_RESULTS[extraction_id]

    return ExtractionResponse(
        extraction_id=extraction_id,
        status=result.get("status", "unknown"),
        message=result.get("error", ""),
        progress=result.get("progress", 0),
        result=result if result.get("status") == "completed" else None
    )


@router.post("/{project_id}/extractions/{extraction_id}/merge")
async def merge_extraction(
    project_id: str,
    extraction_id: str,
    request: MergeRequest,
    current_user: CurrentUser,
):
    """
    Merge extracted data into the project.

    Strategies:
    - overlay: Add extracted data, keeping existing values
    - replace: Replace case data with extracted data
    - manual: Return data for manual review (no merge)
    """
    logger.info(f"Merge request: project={project_id}, extraction={extraction_id}, strategy={request.merge_strategy}")

    # Verify project access
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

    # Get extraction result
    if extraction_id not in EXTRACTION_RESULTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )

    extraction = EXTRACTION_RESULTS[extraction_id]

    if extraction.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extraction not completed"
        )

    mapped_data = extraction.get("mapped_data", {})

    if request.merge_strategy == "manual":
        # Return data for manual review
        return {
            "status": "review_required",
            "extracted_data": mapped_data,
            "message": "Data ready for manual review"
        }

    # Merge data into project
    project_data = project["data"]

    if request.merge_strategy == "replace":
        # Replace entire cases section
        if "cases" in mapped_data:
            project_data["cases"] = mapped_data["cases"]
        if "meta" in mapped_data:
            # Update meta but keep project-specific fields
            for key, value in mapped_data["meta"].items():
                if key not in ["project_id", "user_id", "created_date"]:
                    project_data["meta"][key] = value
    else:
        # Overlay strategy - merge intelligently
        if "cases" in mapped_data and "base_case" in mapped_data["cases"]:
            extracted_case = mapped_data["cases"]["base_case"]
            existing_case = project_data["cases"].get("base_case", {})

            # Merge financials
            if "financials" in extracted_case:
                if "financials" not in existing_case:
                    existing_case["financials"] = {}

                for statement, data in extracted_case["financials"].items():
                    if statement not in existing_case["financials"]:
                        existing_case["financials"][statement] = data
                    else:
                        # Merge individual metrics
                        for metric, values in data.items():
                            if not existing_case["financials"][statement].get(metric):
                                existing_case["financials"][statement][metric] = values

            # Update deal parameters if not set
            if "deal_parameters" in extracted_case:
                if "deal_parameters" not in existing_case:
                    existing_case["deal_parameters"] = extracted_case["deal_parameters"]
                else:
                    # Only update empty fields
                    for key, value in extracted_case["deal_parameters"].items():
                        if not existing_case["deal_parameters"].get(key):
                            existing_case["deal_parameters"][key] = value

            project_data["cases"]["base_case"] = existing_case

        # Update meta
        if "meta" in mapped_data:
            for key, value in mapped_data["meta"].items():
                if key not in ["project_id", "user_id", "created_date"]:
                    if not project_data["meta"].get(key):
                        project_data["meta"][key] = value

    # Save updated project
    await db_update_project(project_id, project_data)

    logger.info(f"Merged extraction {extraction_id} into project {project_id}")

    return {
        "status": "merged",
        "strategy": request.merge_strategy,
        "message": "Extraction data merged into project"
    }
