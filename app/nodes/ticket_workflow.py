"""
PropertySupport AI - app/nodes/ticket_workflow.py

Safe-mode ticket workflow.

This branch never mutates the tickets table. It only writes immutable
TicketEvent suggestions that require human validation.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.application.state import PropertySupportState
from app.config import settings
from app.db.repositories import PropertySupportRepository
from app.domain.enums import ResponseStatus, TicketAction, TicketEventType
from app.domain.policies import decide_ticket_action, validate_safe_ticket_patch
from app.llm.prompt_loader import load_prompt
from app.llm.provider import LLMInvocationError, LLMTaskConfig, llm_service
from app.nodes.common import append_path, warning
from app.schemas.llm import TicketSuggestionDraft


def decide_ticket_action_node(state: PropertySupportState) -> dict:
    """
    Decide whether to suggest updating an existing ticket or creating a new one.

    The decision is deterministic and based on the context returned by
    retrieve_context.
    """
    path = append_path(state, "decide_ticket_action")
    context = state.get("context", {}) or {}
    similar_ticket = context.get("similar_ticket")

    action_type = decide_ticket_action(similar_ticket)

    return {
        "decision": {**state.get("decision", {}), "ticket_action": action_type},
        "graph_path": path,
    }


def generate_ticket_suggestion_node(state: PropertySupportState) -> dict:
    """
    Generate a safe-mode ticket suggestion using deterministic context.

    The LLM drafts human-readable fields, but action_type, ticket_id,
    requires_human_validation and sources are forced by code.
    """
    path = append_path(state, "generate_ticket_suggestion")
    action = state.get("decision", {}).get(
        "ticket_action",
        TicketAction.CREATE_SUGGESTION.value,
    )

    prompt = load_prompt("generate_ticket_suggestion.md")

    user_prompt = (
        prompt.replace("{{ user_message }}", state.get("user_message", ""))
        .replace("{{ context_json }}", json.dumps(state.get("context", {}), ensure_ascii=False))
        .replace("{{ ticket_action }}", action)
    )

    try:
        draft = llm_service.invoke_json(
            system_prompt="Return valid JSON only. Safe mode: no real ticket mutation.",
            user_prompt=user_prompt,
            schema=TicketSuggestionDraft,
            task_config=LLMTaskConfig(
                temperature=settings.llm_temperature_reasoning,
                timeout_seconds=settings.llm_timeout_seconds,
            ),
        )

        suggestion = _normalize_ticket_suggestion(state, draft, action)
        patch = _safe_patch_from_suggestion(suggestion)
        valid, errors = validate_safe_ticket_patch(patch)

        if not valid:
            return {
                "final_response": {
                    "status": ResponseStatus.HUMAN_VALIDATION_REQUIRED.value,
                    "summary": "The ticket suggestion was rejected by safe-mode validation.",
                    "data": {"validation_errors": errors},
                    "sources_used": suggestion["sources_used"],
                },
                "warnings": [
                    *state.get("warnings", []),
                    warning("SAFE_PATCH_REJECTED", "; ".join(errors)),
                ],
                "graph_path": path,
            }

        return {
            "decision": {**state.get("decision", {}), "ticket_suggestion": suggestion},
            "graph_path": path,
        }

    except LLMInvocationError as exc:
        return {
            "final_response": {
                "status": ResponseStatus.HUMAN_VALIDATION_REQUIRED.value,
                "summary": "The ticket suggestion could not be generated safely.",
                "data": {},
                "sources_used": state.get("sources_used", []),
            },
            "warnings": [*state.get("warnings", []), warning("LLM_TICKET_FAILED", str(exc))],
            "graph_path": path,
        }


def _normalize_ticket_suggestion(
    state: PropertySupportState,
    draft: TicketSuggestionDraft,
    action: str,
) -> dict:
    """
    Force LLM ticket suggestions to match deterministic safe-mode decisions.
    """
    suggestion = draft.model_dump()
    context = state.get("context", {}) or {}
    similar_ticket = context.get("similar_ticket")

    suggestion["action_type"] = action
    suggestion["requires_human_validation"] = True
    suggestion["sources_used"] = state.get("sources_used", [])

    if action == TicketAction.UPDATE_SUGGESTION.value:
        suggestion["ticket_id"] = similar_ticket["id"] if similar_ticket else None
    else:
        suggestion["ticket_id"] = None

    if not suggestion.get("priority_suggestion"):
        suggestion["priority_suggestion"] = context.get("priority")

    if not suggestion.get("title"):
        suggestion["title"] = _default_ticket_title(state)

    return suggestion


def _safe_patch_from_suggestion(suggestion: dict) -> dict:
    """
    Extract the additive patch fields that are allowed in safe mode.
    """
    excluded_fields = {
        "sources_used",
        "requires_human_validation",
        "action_type",
        "ticket_id",
    }

    return {
        key: value
        for key, value in suggestion.items()
        if key not in excluded_fields and value is not None
    }


def _default_ticket_title(state: PropertySupportState) -> str:
    context = state.get("context", {}) or {}
    issue_type = context.get("issue_type") or "support_request"
    building = context.get("building") or {}
    building_name = building.get("name") or "Unknown building"

    return f"{issue_type.replace('_', ' ').title()} - {building_name}"


def make_write_ticket_event_node(session: Session):
    """Create the write ticket event node with a DB session closure."""

    def write_ticket_event_node(state: PropertySupportState) -> dict:
        path = append_path(state, "write_ticket_event")
        suggestion = state.get("decision", {}).get("ticket_suggestion")

        if not suggestion:
            return {
                "final_response": {
                    "status": ResponseStatus.HUMAN_VALIDATION_REQUIRED.value,
                    "summary": "No ticket suggestion was available to record.",
                    "data": {},
                    "sources_used": state.get("sources_used", []),
                },
                "warnings": [
                    *state.get("warnings", []),
                    warning("TICKET_SUGGESTION_MISSING", "No ticket suggestion was generated."),
                ],
                "graph_path": path,
            }

        if settings.dry_run or not settings.write_ticket_events:
            return {
                "final_response": {
                    "status": ResponseStatus.SUCCESS.value,
                    "summary": "A ticket suggestion was generated in dry-run mode.",
                    "data": suggestion,
                    "sources_used": suggestion.get("sources_used", state.get("sources_used", [])),
                },
                "graph_path": path,
            }

        repo = PropertySupportRepository(session)
        action_type = suggestion["action_type"]

        event_type = (
            TicketEventType.AI_UPDATE_SUGGESTED
            if action_type == TicketAction.UPDATE_SUGGESTION.value
            else TicketEventType.AI_CREATION_SUGGESTED
        )

        event = repo.append_ticket_event(
            event_type=event_type,
            content=suggestion,
            sources=suggestion.get("sources_used", state.get("sources_used", [])),
            ticket_id=suggestion.get("ticket_id"),
            request_id=state.get("request_id", "REQ-UNKNOWN"),
            trace_id=state.get("trace_id"),
            graph_path=path,
        )

        return {
            "final_response": {
                "status": ResponseStatus.TICKET_EVENT_CREATED.value,
                "summary": "A safe-mode ticket suggestion was recorded.",
                "data": {"event_id": event.id, "suggestion": suggestion},
                "sources_used": event.sources_json,
            },
            "graph_path": path,
        }

    return write_ticket_event_node
