"""
PropertySupport AI - app/nodes/retrieve_context.py

Retrieves deterministic business context from SQLite via repositories.

This node reconciles extracted LLM entities with known business data. It also
uses deterministic fallback matching on the original user message when the LLM
does not extract a building name or issue type reliably.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.application.state import PropertySupportState
from app.db.repositories import PropertySupportRepository, normalize_text
from app.domain.enums import Intent
from app.domain.policies import issue_domain, normalize_priority
from app.nodes.common import append_path, warning


def make_retrieve_context_node(session: Session):
    """Create the retrieve context node with a DB session closure."""

    def retrieve_context_node(state: PropertySupportState) -> dict:
        path = append_path(state, "retrieve_context")

        repo = PropertySupportRepository(session)
        entities = state.get("entities", {}) or {}
        user_message = state.get("user_message")

        issue_type = entities.get("issue_type")

        if not issue_type:
            issue_type = infer_issue_type_from_text(user_message)

        domain = issue_domain(issue_type)

        building_name = entities.get("building_name")
        resident_name = entities.get("resident_name")
        unit_reference = entities.get("unit_reference")

        building = repo.find_building_by_name(building_name)

        if building is None:
            building = repo.find_building_in_text(user_message)

        resident = repo.find_resident_by_name(resident_name)

        unit = repo.find_unit_by_reference(
            building.id if building else None,
            unit_reference,
        )

        contract = repo.find_active_contract(building.id, domain) if building and domain else None
        provider = repo.find_provider_by_id(contract.provider_id) if contract else None
        procedure = repo.find_procedure_by_issue_type(issue_type)
        tickets = repo.find_open_tickets_by_building(building.id) if building else []
        similar_ticket = (
            repo.find_similar_open_ticket(building.id, issue_type) if building else None
        )
        interventions = repo.find_recent_interventions(building.id, domain) if building else []

        sources = _sources(building, contract, provider, procedure, similar_ticket)
        warnings = list(state.get("warnings", []))
        intent = state.get("intent")

        if not building and intent not in {Intent.CLARIFICATION.value, None}:
            warnings.append(warning("BUILDING_NOT_FOUND", "No matching building was found."))

        if building and domain and not contract:
            warnings.append(warning("NO_ACTIVE_CONTRACT", "No active contract was found."))

        context = {
            "building": _model_summary(building),
            "resident": _model_summary(resident),
            "unit": _model_summary(unit),
            "issue_type": issue_type,
            "domain": domain,
            "active_contract": _model_summary(contract),
            "provider": _model_summary(provider),
            "procedure": _procedure_summary(procedure),
            "open_tickets": [_ticket_summary(ticket) for ticket in tickets],
            "similar_ticket": _ticket_summary(similar_ticket),
            "recent_interventions": [_model_summary(item) for item in interventions],
            "priority": normalize_priority(issue_type, state.get("priority")),
        }

        deterministic_sources: list[str] = [*state.get("sources_used", []), *sources]

        return {
            "context": context,
            "sources_used": sorted(set(deterministic_sources)),
            "warnings": warnings,
            "graph_path": path,
        }

    return retrieve_context_node


def infer_issue_type_from_text(text: str | None) -> str | None:
    """
    Infer an issue type from the raw user message using deterministic keywords.

    This fallback is intentionally simple. It prevents the workflow from losing
    critical business context when a local LLM fails to extract issue_type.
    """
    normalized = normalize_text(text)

    if not normalized:
        return None

    heating_keywords = {
        "chauffage",
        "radiateur",
        "radiateurs",
        "chaudiere",
        "chaudière",
        "temperature",
        "température",
        "froid",
        "heating",
    }

    hot_water_keywords = {
        "eau chaude",
        "ballon",
        "hot water",
    }

    elevator_with_person_keywords = {
        "personne bloquee",
        "personne bloquée",
        "bloque avec une personne",
        "bloqué avec une personne",
        "person stuck",
    }

    elevator_keywords = {
        "ascenseur",
        "elevator",
        "monte charge",
        "monte-charge",
    }

    water_leak_keywords = {
        "fuite",
        "degat des eaux",
        "dégât des eaux",
        "infiltration",
        "plafond humide",
        "water leak",
        "leak",
    }

    electrical_keywords = {
        "electricite",
        "électricité",
        "electrique",
        "électrique",
        "disjoncteur",
        "court circuit",
        "court-circuit",
        "electrical",
    }

    badge_keywords = {
        "badge",
        "acces",
        "accès",
        "parking",
        "porte",
        "telecommande",
        "télécommande",
    }

    noise_keywords = {
        "bruit",
        "nuisance",
        "tapage",
        "noise",
    }

    cleaning_keywords = {
        "menage",
        "ménage",
        "nettoyage",
        "sale",
        "proprete",
        "propreté",
        "cleaning",
    }

    if _contains_any(normalized, elevator_with_person_keywords):
        return "elevator_blocked_with_person"

    if _contains_any(normalized, heating_keywords):
        return "heating_outage"

    if _contains_any(normalized, hot_water_keywords):
        return "hot_water_outage"

    if _contains_any(normalized, elevator_keywords):
        return "elevator_outage"

    if _contains_any(normalized, water_leak_keywords):
        return "water_leak"

    if _contains_any(normalized, electrical_keywords):
        return "electrical_hazard"

    if _contains_any(normalized, badge_keywords):
        return "access_badge"

    if _contains_any(normalized, noise_keywords):
        return "noise_complaint"

    if _contains_any(normalized, cleaning_keywords):
        return "cleaning_issue"

    return None


def _contains_any(normalized_text: str, keywords: set[str]) -> bool:
    normalized_keywords = {normalize_text(keyword) for keyword in keywords}

    return any(keyword in normalized_text for keyword in normalized_keywords)


def _sources(building, contract, provider, procedure, ticket) -> list[str]:
    sources = []

    if building:
        sources.append(f"buildings:{building.id}")

    if contract:
        sources.append(f"contracts:{contract.id}")

    if provider:
        sources.append(f"providers:{provider.id}")

    if procedure:
        sources.append(f"procedures:{procedure.id}")

    if ticket:
        sources.append(f"tickets:{ticket.id}")

    return sources


def _json_safe(value: Any) -> Any:
    """Return a JSON-serializable representation for prompt context payloads."""
    if isinstance(value, datetime | date):
        return value.isoformat()

    if isinstance(value, list):
        return [_json_safe(item) for item in value]

    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}

    return value


def _model_summary(model):
    """Convert a SQLAlchemy model into a small JSON-safe dictionary."""
    if model is None:
        return None

    columns = model.__table__.columns.keys()

    return {key: _json_safe(getattr(model, key)) for key in columns}


def _procedure_summary(procedure):
    if procedure is None:
        return None

    return {
        "id": procedure.id,
        "code": procedure.code,
        "issue_type": procedure.issue_type,
        "title": procedure.title,
        "description": procedure.description,
        "steps": procedure.steps_json,
        "requires_emergency_provider": procedure.requires_emergency_provider,
        "requires_human_validation": procedure.requires_human_validation,
    }


def _ticket_summary(ticket):
    if ticket is None:
        return None

    return {
        "id": ticket.id,
        "building_id": ticket.building_id,
        "category": ticket.category,
        "issue_type": ticket.issue_type,
        "priority": ticket.priority,
        "status": ticket.status,
        "title": ticket.title,
        "summary": ticket.summary,
        "assigned_provider_id": ticket.assigned_provider_id,
    }
