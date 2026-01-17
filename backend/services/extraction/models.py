"""
Extraction data models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ConflictSeverity(str, Enum):
    """Severity levels for extraction conflicts."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ConflictRecord:
    """Represents a conflict or issue found during extraction."""
    field: str
    extracted_value: Any
    calculated_value: Any | None
    severity: ConflictSeverity
    message: str
    resolution_hint: str


@dataclass
class ExtractionMetadata:
    """Metadata about the extraction process."""
    extraction_id: str
    timestamp: datetime
    file_name: str
    file_type: str
    file_size_mb: float
    provider: str
    model: str
    total_tokens: int
    extraction_time_seconds: float
    confidence_threshold: float = 0.7


@dataclass
class ExtractionResponse:
    """Raw response from LLM provider."""
    raw_data: dict[str, Any]
    confidence_scores: dict[str, float]
    tokens_used: int
    processing_notes: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """Complete extraction result."""
    raw_data: dict[str, Any]
    mapped_data: dict[str, Any] | None
    conflicts: list[ConflictRecord]
    confidence_scores: dict[str, float]
    metadata: ExtractionMetadata
    insights_data: dict[str, Any] | None = None
    status: str = "complete"
