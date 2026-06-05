"""
PropertySupport AI - app/nodes/incident_analysis.py

Incident analysis branch.

Policies decide the safe internal action based on deterministic context produced
by retrieve_context. This file must use `context.issue_type` because the context
node may infer it even when the LLM extraction missed it.
"""

from __future__ import annotations

import json

from app.application.state import PropertySupportState
from app.config import settings
from app.domain.enums import IncidentAction, ResponseStatus
from app.domain.policies import decide_incident_action
from app.llm.prompt_loader import load_prompt
from app.llm.provider import LLMInvocationError, LLMTaskConfig, llm_service
from app.nodes.common import append_path, warning
from app.schemas.llm import EmergencyResponseDraft, IncidentResponseDraft, SafeResponseDraft


def decide_incident_action_node(state: PropertySupportState) -> dict:
    """Decide the safe incident action from deterministic context."""
    path = append_path(state, "decide_incident_action")
    context = state.get("context", {}) or {}
    entities = state.get("entities", {}) or {}

    provider = context.get("provider")
    issue_type = context.get("issue_type")
    priority = context.get("priority") or "medium"

    life_safety_risk = bool(entities.get("life_safety_risk")) or (
        issue_type == "elevator_blocked_with_person"
    )

    action = decide_incident_action(
        building_found=bool(context.get("building")),
        issue_type=issue_type,
        priority=priority,
        active_contract_found=bool(context.get("active_contract")),
        provider_found=bool(provider),
        provider_has_contact=bool(
            provider and (provider.get("phone") or provider.get("emergency_phone"))
        ),
        life_safety_risk=life_safety_risk,
    )

    return {
        "decision": {**state.get("decision", {}), "incident_action": action},
        "graph_path": path,
    }


def generate_incident_response_node(state: PropertySupportState) -> dict:
    """Generate the final incident response according to the deterministic action."""
    action = state.get("decision", {}).get("incident_action")

    if action == IncidentAction.EMERGENCY_ESCALATION.value:
        return _generate_emergency_response(state)

    if action == IncidentAction.HUMAN_VALIDATION_REQUIRED.value:
        return _generate_safe_response(
            state,
            ResponseStatus.HUMAN_VALIDATION_REQUIRED.value,
        )

    if action == IncidentAction.CLARIFICATION.value:
        return _generate_safe_response(
            state,
            ResponseStatus.NEEDS_CLARIFICATION.value,
        )

    return _generate_standard_incident_response(state)


def _generate_standard_incident_response(state: PropertySupportState) -> dict:
    path = append_path(state, "generate_incident_response")
    prompt = load_prompt("generate_incident_response.md")

    user_prompt = (
        prompt.replace("{{ user_message }}", state.get("user_message", ""))
        .replace("{{ incident_action }}", state.get("decision", {}).get("incident_action", ""))
        .replace("{{ context_json }}", json.dumps(state.get("context", {}), ensure_ascii=False))
    )

    try:
        draft = llm_service.invoke_json(
            system_prompt="Return valid JSON only. Use only provided context.",
            user_prompt=user_prompt,
            schema=IncidentResponseDraft,
            task_config=LLMTaskConfig(
                temperature=settings.llm_temperature_reasoning,
                timeout_seconds=settings.llm_timeout_seconds,
            ),
        )

        return {
            "final_response": {
                "status": ResponseStatus.SUCCESS.value,
                "summary": draft.summary,
                "data": draft.model_dump(),
                "sources_used": draft.sources_used,
            },
            "graph_path": path,
        }

    except LLMInvocationError as exc:
        return _fallback_response(state, path, "LLM_INCIDENT_FAILED", str(exc))


def _generate_emergency_response(state: PropertySupportState) -> dict:
    path = append_path(state, "generate_emergency_response")
    prompt = load_prompt("generate_emergency_response.md")

    user_prompt = prompt.replace("{{ user_message }}", state.get("user_message", "")).replace(
        "{{ context_json }}", json.dumps(state.get("context", {}), ensure_ascii=False)
    )

    try:
        draft = llm_service.invoke_json(
            system_prompt="Return valid JSON only. Safety first.",
            user_prompt=user_prompt,
            schema=EmergencyResponseDraft,
            task_config=LLMTaskConfig(
                temperature=settings.llm_temperature_reasoning,
                timeout_seconds=settings.llm_timeout_seconds,
            ),
        )

        return {
            "final_response": {
                "status": ResponseStatus.SUCCESS.value,
                "summary": draft.summary,
                "data": draft.model_dump(),
                "sources_used": draft.sources_used,
            },
            "graph_path": path,
        }

    except LLMInvocationError as exc:
        return _fallback_response(state, path, "LLM_EMERGENCY_FAILED", str(exc))


def _generate_safe_response(state: PropertySupportState, status: str) -> dict:
    path = append_path(state, "generate_safe_response")
    prompt = load_prompt("generate_safe_response.md")

    missing_fields = _missing_fields_for_safe_response(state)

    user_prompt = (
        prompt.replace("{{ user_message }}", state.get("user_message", ""))
        .replace("{{ context_json }}", json.dumps(state.get("context", {}), ensure_ascii=False))
        .replace("{{ missing_fields }}", json.dumps(missing_fields, ensure_ascii=False))
    )

    try:
        draft = llm_service.invoke_json(
            system_prompt="Return valid JSON only. Do not invent context.",
            user_prompt=user_prompt,
            schema=SafeResponseDraft,
            task_config=LLMTaskConfig(
                temperature=settings.llm_temperature_reasoning,
                timeout_seconds=settings.llm_timeout_seconds,
            ),
        )

        return {
            "final_response": {
                "status": status,
                "summary": draft.summary,
                "data": draft.model_dump(),
                "sources_used": draft.sources_used,
            },
            "graph_path": path,
        }

    except LLMInvocationError as exc:
        return _fallback_response(state, path, "LLM_SAFE_RESPONSE_FAILED", str(exc), status)


def _missing_fields_for_safe_response(state: PropertySupportState) -> list[str]:
    """Return human-readable missing fields for safe response generation."""
    context = state.get("context", {}) or {}
    missing_fields: list[str] = []

    if not context.get("building"):
        missing_fields.append("building")

    if not context.get("issue_type"):
        missing_fields.append("issue_type")

    if context.get("domain") and not context.get("active_contract"):
        missing_fields.append("active_contract")

    if context.get("active_contract") and not context.get("provider"):
        missing_fields.append("provider")

    return missing_fields


def _fallback_response(
    state: PropertySupportState,
    path: list[str],
    code: str,
    message: str,
    status: str = ResponseStatus.PARTIAL_ANSWER.value,
) -> dict:
    return {
        "final_response": {
            "status": status,
            "summary": "The incident could not be fully analyzed by the local model.",
            "data": {},
            "sources_used": state.get("sources_used", []),
        },
        "warnings": [*state.get("warnings", []), warning(code, message)],
        "graph_path": path,
    }
