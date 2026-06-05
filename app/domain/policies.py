"""
PropertySupport AI - app/domain/policies.py

Deterministic business rules.

This module must stay pure:
- no LLM calls;
- no database access;
- no FastAPI dependency;
- no LangGraph dependency.

The workflow can use LLMs to classify, extract and draft, but sensitive routing
and safety decisions must remain deterministic and testable.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.enums import IncidentAction, TicketAction

CRITICAL_ISSUE_TYPES = {
    "elevator_blocked_with_person",
    "major_water_leak",
    "electrical_hazard",
    "fire_risk",
    "gas_leak",
}

HIGH_PRIORITY_ISSUE_TYPES = {
    "heating_outage",
    "hot_water_outage",
    "water_leak",
    "elevator_outage",
    "elevator_blocked",
    "elevator_blocked_with_person",
    "access_blocked",
}

SAFE_TICKET_PATCH_FIELDS = {
    "summary_addition",
    "recommended_actions",
    "priority_suggestion",
    "provider_contact_suggestion",
    "resident_message_draft",
    "title",
}


def issue_domain(issue_type: str | None) -> str | None:
    """Map an issue type to a provider domain."""
    if not issue_type:
        return None

    if issue_type in {"heating_outage", "hot_water_outage"}:
        return "heating"

    if issue_type in {"elevator_outage", "elevator_blocked", "elevator_blocked_with_person"}:
        return "elevator"

    if issue_type in {"water_leak", "major_water_leak"}:
        return "plumbing"

    if issue_type == "electrical_hazard":
        return "electrical"

    if issue_type in {"access_badge", "access_blocked"}:
        return "access"

    if issue_type == "cleaning_issue":
        return "cleaning"

    return "general"


def is_critical_emergency(
    issue_type: str | None,
    priority: str | None,
    life_safety_risk: bool = False,
) -> bool:
    """Return True when an incident requires emergency escalation."""
    if life_safety_risk:
        return True

    if priority == "critical":
        return True

    return issue_type in CRITICAL_ISSUE_TYPES


def normalize_priority(issue_type: str | None, requested_priority: str | None = None) -> str:
    """Normalize priority to one of critical, high, medium or low."""
    allowed = {"critical", "high", "medium", "low"}

    if requested_priority in allowed:
        return requested_priority

    if issue_type in CRITICAL_ISSUE_TYPES:
        return "critical"

    if issue_type in HIGH_PRIORITY_ISSUE_TYPES:
        return "high"

    return "medium"


def can_suggest_provider_contact(
    active_contract_found: bool,
    provider_found: bool,
    provider_has_contact: bool,
) -> bool:
    """
    Return True when the system can safely suggest contacting a provider.

    The provider must come from the deterministic business context. The LLM must
    never invent provider names, phone numbers or emergency contacts.
    """
    return active_contract_found and provider_found and provider_has_contact


def decide_ticket_action(similar_open_ticket: Any | None) -> str:
    """
    Decide whether the safe-mode workflow should suggest an update or creation.

    Both outcomes are suggestions only. The `tickets` table is never directly
    mutated by the GenAI workflow.
    """
    if similar_open_ticket:
        return TicketAction.UPDATE_SUGGESTION.value

    return TicketAction.CREATE_SUGGESTION.value


def validate_safe_ticket_patch(patch: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate that an AI-generated ticket patch is safe.

    The LLM may propose additive content only. It cannot close, delete,
    reassign or directly modify a ticket status.
    """
    errors: list[str] = []

    for field in patch:
        if field not in SAFE_TICKET_PATCH_FIELDS:
            errors.append(f"Field '{field}' is not allowed in safe mode.")

    if "status" in patch:
        errors.append("Direct status changes are not allowed in safe mode.")

    if "assigned_provider_id" in patch:
        errors.append("Direct provider reassignment is not allowed in safe mode.")

    return len(errors) == 0, errors


def response_needs_sources(intent: str | None) -> bool:
    """Return True when a final response should include deterministic sources."""
    return intent in {"lookup", "communication", "ticket_workflow", "incident_analysis"}


def decide_incident_action(
    building_found: bool,
    issue_type: str | None,
    priority: str,
    active_contract_found: bool,
    provider_found: bool,
    provider_has_contact: bool,
    life_safety_risk: bool = False,
) -> str:
    """
    Decide the internal incident-analysis action.

    Rules:
    - missing building or issue type -> clarification;
    - critical incident + provider contact available -> emergency escalation;
    - critical incident without safe provider context -> human validation;
    - standard incident + provider contact available -> provider action plan;
    - otherwise -> human validation.
    """
    if not building_found or not issue_type:
        return IncidentAction.CLARIFICATION.value

    if is_critical_emergency(issue_type, priority, life_safety_risk):
        if can_suggest_provider_contact(
            active_contract_found,
            provider_found,
            provider_has_contact,
        ):
            return IncidentAction.EMERGENCY_ESCALATION.value

        return IncidentAction.HUMAN_VALIDATION_REQUIRED.value

    if can_suggest_provider_contact(
        active_contract_found,
        provider_found,
        provider_has_contact,
    ):
        return IncidentAction.PROVIDER_ACTION_PLAN.value

    return IncidentAction.HUMAN_VALIDATION_REQUIRED.value


def is_duplicate_ticket_candidate(
    existing_ticket: dict[str, Any],
    building_id: str,
    issue_type: str,
    now: datetime | None = None,
    duplicate_window_hours: int = 72,
) -> bool:
    """Simple duplicate detection for tests and future extension."""
    now = now or datetime.now(UTC)

    if existing_ticket.get("building_id") != building_id:
        return False

    if existing_ticket.get("issue_type") != issue_type:
        return False

    if existing_ticket.get("status") not in {"open", "in_progress", "waiting_provider"}:
        return False

    raw = existing_ticket.get("updated_at") or existing_ticket.get("created_at")

    if not raw:
        return True

    try:
        updated_at = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return True

    return now - updated_at <= timedelta(hours=duplicate_window_hours)
