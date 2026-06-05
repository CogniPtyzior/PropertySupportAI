"""
PropertySupport AI - app/schemas/responses.py

Shared API response schemas.
"""

from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import Intent, ResponseStatus
from app.schemas.errors import AppIssue


class SourceReference(BaseModel):
    source_type: str
    source_id: str
    label: str | None = None

    def compact(self) -> str:
        return f"{self.source_type}:{self.source_id}"


class ApiResponse(BaseModel):
    request_id: str
    status: ResponseStatus
    intent: Intent | None = None
    selected_branch: str | None = None
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    sources_used: list[str] = Field(default_factory=list)
    warnings: list[AppIssue] = Field(default_factory=list)
    errors: list[AppIssue] = Field(default_factory=list)
    trace_id: str | None = None
    debug: dict[str, Any] | None = None
