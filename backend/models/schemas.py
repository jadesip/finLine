"""
finLine Pydantic Schemas

All schemas use snake_case naming convention.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field


# ============================================================
# Auth Schemas
# ============================================================

class UserCreate(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response (no password)."""
    id: str
    email: str
    is_active: bool = True
    created_at: str
    last_login: str | None = None


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ============================================================
# Project Schemas
# ============================================================

class ProjectCreate(BaseModel):
    """Create project request."""
    name: str = Field(..., min_length=1, max_length=200)
    company_name: str | None = None
    currency: str = "USD"
    unit: str = "millions"


class ProjectUpdate(BaseModel):
    """Update project request - partial updates via path."""
    path: str = Field(..., description="Dot-notation path to update, e.g., 'cases.base_case.financials.revenue.2024'")
    value: Any = Field(..., description="New value to set")


class ProjectBulkUpdate(BaseModel):
    """Bulk update multiple paths."""
    updates: list[ProjectUpdate]


class ProjectListItem(BaseModel):
    """Project list item (without full data)."""
    id: str
    name: str
    user_id: str
    created_at: str
    updated_at: str


class ProjectResponse(BaseModel):
    """Full project response."""
    id: str
    name: str
    user_id: str
    created_at: str
    updated_at: str
    data: dict[str, Any]


# ============================================================
# Analysis Schemas
# ============================================================

class AnalysisRequest(BaseModel):
    """Analysis request."""
    case_id: str = "base_case"


class AnalysisResult(BaseModel):
    """LBO analysis result."""
    success: bool
    case_id: str
    irr: float | None = None
    moic: float | None = None
    entry_value: float | None = None
    exit_value: float | None = None
    equity_invested: float | None = None
    equity_returned: float | None = None
    debt_schedule: dict[str, Any] | None = None
    cash_flows: dict[str, Any] | None = None
    error: str | None = None


# ============================================================
# Chat Schemas
# ============================================================

class ChatRequest(BaseModel):
    """Chat request for natural language updates."""
    message: str = Field(..., min_length=1)
    case_id: str = "base_case"
    image_data: str | None = Field(None, description="Base64 encoded image for number extraction")


class ChatChange(BaseModel):
    """Single change proposed by chat."""
    path: str
    old_value: Any
    new_value: Any


class ChatResponse(BaseModel):
    """Chat response."""
    understood: bool
    message: str
    changes: list[ChatChange] | None = None
    applied: bool = False
    clarification_needed: str | None = None


# ============================================================
# Extraction Schemas
# ============================================================

class ExtractionStatus(BaseModel):
    """Extraction status response."""
    id: str
    project_id: str
    status: str  # pending, processing, completed, failed
    source_files: list[str]
    created_at: str
    completed_at: str | None = None


class ExtractionResult(BaseModel):
    """Extraction result with data."""
    id: str
    project_id: str
    status: str
    extracted_data: dict[str, Any] | None = None
    error: str | None = None


# ============================================================
# Generic Response Schemas
# ============================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str | None = None
    data: Any | None = None


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    message: str
    field: str | None = None
