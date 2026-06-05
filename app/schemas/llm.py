"""
PropertySupport AI - app/schemas/llm.py

Pydantic schemas expected from LLM prompts.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import Intent, Priority, TicketAction


class ClassificationResult(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class ExtractedEntities(BaseModel):
    building_name: str | None = None
    resident_name: str | None = None
    unit_reference: str | None = None
    issue_type: str | None = None
    affected_scope: str | None = None
    time_hint: str | None = None
    life_safety_risk: bool = False
    requested_action: str | None = None


class LookupAnswerDraft(BaseModel):
    summary: str
    answer_found: bool
    sources_used: list[str]


class MessageDraft(BaseModel):
    message_type: str
    draft_message: str
    missing_information: list[str] = Field(default_factory=list)
    sources_used: list[str]


class TicketSuggestionDraft(BaseModel):
    action_type: TicketAction
    ticket_id: str | None = None
    title: str | None = None
    summary_addition: str | None = None
    priority_suggestion: Priority | None = None
    recommended_actions: list[str] = Field(default_factory=list)
    requires_human_validation: bool = True
    sources_used: list[str]


class IncidentResponseDraft(BaseModel):
    status: str
    summary: str
    priority: Priority
    recommended_actions: list[str] = Field(default_factory=list)
    provider_to_contact: dict | None = None
    ticket_recommendation: dict | None = None
    resident_message_draft: str | None = None
    warnings: list[str] = Field(default_factory=list)
    sources_used: list[str]


class EmergencyResponseDraft(BaseModel):
    status: str = "success"
    priority: str = "critical"
    summary: str
    immediate_actions: list[str] = Field(default_factory=list)
    provider_to_contact: dict[str, Any] | None = None
    safety_warning: str | None = None
    requires_human_validation: bool = False
    sources_used: list[str] = Field(default_factory=list)

    @field_validator("provider_to_contact", mode="before")
    @classmethod
    def normalize_provider_to_contact(cls, value: Any) -> dict[str, Any] | None:
        if value is None or isinstance(value, dict):
            return value

        return {"label": str(value)}

    @field_validator("immediate_actions", mode="before")
    @classmethod
    def normalize_immediate_actions(cls, value: Any) -> list[str]:
        """
        Accept either a list of strings or a list of small action objects.

        Local LLMs often return:
        {"action": "...", "phone": "..."}
        even when the schema asks for strings. For this demo, we normalize these
        objects into readable strings instead of failing the whole emergency flow.
        """
        if value is None:
            return []

        if not isinstance(value, list):
            return [str(value)]

        normalized: list[str] = []

        for item in value:
            if isinstance(item, str):
                normalized.append(item)
                continue

            if isinstance(item, dict):
                action = item.get("action") or item.get("description") or item.get("step")
                details = [
                    str(detail)
                    for key, detail in item.items()
                    if key not in {"action", "description", "step"} and detail
                ]

                if action and details:
                    normalized.append(f"{action} ({', '.join(details)})")
                elif action:
                    normalized.append(str(action))
                else:
                    normalized.append(str(item))

                continue

            normalized.append(str(item))

        return normalized


class SafeResponseDraft(BaseModel):
    status: str
    summary: str
    clarifying_question: str | None = None
    warnings: list[str] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)
