"""
PropertySupport AI - app/schemas/errors.py

Structured warning and error payloads.
"""

from typing import Any

from pydantic import BaseModel, Field


class AppIssue(BaseModel):
    code: str
    message: str
    recoverable: bool = True
    details: dict[str, Any] = Field(default_factory=dict)
