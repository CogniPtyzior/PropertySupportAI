"""
PropertySupport AI - app/schemas/api.py

FastAPI request and response DTOs.
"""

from pydantic import BaseModel, Field, field_validator

from app.config import settings
from app.schemas.responses import ApiResponse


class AskRequest(BaseModel):
    message: str = Field(
        min_length=3,
        max_length=settings.api_max_message_length,
        description="Natural language property support request.",
    )
    user_id: str | None = Field(default=None, max_length=80)
    conversation_id: str | None = Field(default=None, max_length=120)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty.")
        return cleaned


class AskResponse(ApiResponse):
    pass
