"""
PropertySupport AI - app/db/repositories.py

Repository layer hiding SQLAlchemy queries from LangGraph nodes.

This module intentionally keeps data access deterministic. The LLM can help
extract entities, but known business entities such as buildings, residents,
contracts and tickets are reconciled through repository methods.
"""

from __future__ import annotations

import unicodedata
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from rapidfuzz import fuzz
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import (
    Building,
    Contract,
    Intervention,
    Procedure,
    Provider,
    Resident,
    Ticket,
    TicketEvent,
    Unit,
)
from app.domain.enums import TicketEventType


def normalize_text(value: str | None) -> str:
    """
    Normalize text for fuzzy matching.

    This function removes accents, lowercases text and collapses whitespace.
    It is kept generic and safe for names, labels and short business strings.
    """
    if not value:
        return ""

    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))

    return " ".join(without_accents.casefold().split())


def normalize_business_label(value: str | None) -> str:
    """
    Normalize a business label for tolerant entity reconciliation.

    Users may write "Érables", "aux Érables" or "Résidence Les Érables" while
    the database stores "Résidence Les Érables". This function removes common
    French domain words and articles only when they appear as separate tokens.
    """
    normalized = normalize_text(value)

    ignored_tokens = {
        "residence",
        "immeuble",
        "batiment",
        "bâtiment",
        "aux",
        "des",
        "les",
        "la",
        "le",
        "du",
        "de",
        "d",
        "l",
        "a",
        "au",
        "dans",
        "sur",
        "chez",
    }

    tokens = [token.strip(" ,.;:!?()[]{}'\"") for token in normalized.replace("'", " ").split()]

    kept_tokens = [token for token in tokens if token and token not in ignored_tokens]

    return " ".join(kept_tokens)


def is_text_match(query: str | None, candidate: str | None, *, threshold: int = 80) -> bool:
    """
    Return True when a free-form query likely refers to a known business label.

    Matching strategy:
    - exact normalized match;
    - partial normalized match;
    - fuzzy partial ratio.
    """
    normalized_query = normalize_business_label(query)
    normalized_candidate = normalize_business_label(candidate)

    if not normalized_query or not normalized_candidate:
        return False

    if normalized_query == normalized_candidate:
        return True

    if normalized_query in normalized_candidate:
        return True

    if normalized_candidate in normalized_query:
        return True

    return fuzz.partial_ratio(normalized_query, normalized_candidate) >= threshold


class PropertySupportRepository:
    """Application repository used by workflow nodes."""

    def __init__(self, session: Session):
        self.session = session

    def find_building_by_name(self, name: str | None) -> Building | None:
        """
        Find a building by extracted name using tolerant matching.

        This method is used when the LLM has extracted a candidate building name.
        It deliberately accepts variations such as "Érables", "Les Érables" or
        "Résidence Les Érables".
        """
        if not name:
            return None

        buildings = self.session.scalars(select(Building)).all()

        for building in buildings:
            if is_text_match(name, building.name):
                return building

        normalized = normalize_business_label(name)
        scored = [
            (fuzz.partial_ratio(normalized, normalize_business_label(building.name)), building)
            for building in buildings
        ]

        if not scored:
            return None

        score, building = max(scored, key=lambda item: item[0])

        return building if score >= 70 else None

    def find_building_in_text(self, text: str | None) -> Building | None:
        """
        Find a known building mentioned in a free-form user message.

        This deterministic fallback is important because local LLMs may fail to
        extract `building_name` even when the building is clearly present in the
        user message.
        """
        if not text:
            return None

        buildings = self.session.scalars(select(Building)).all()

        for building in buildings:
            if is_text_match(text, building.name):
                return building

        normalized_text = normalize_business_label(text)
        scored = [
            (
                fuzz.partial_ratio(normalized_text, normalize_business_label(building.name)),
                building,
            )
            for building in buildings
        ]

        if not scored:
            return None

        score, building = max(scored, key=lambda item: item[0])

        return building if score >= 70 else None

    def find_resident_by_name(self, name: str | None) -> Resident | None:
        if not name:
            return None

        residents = self.session.scalars(select(Resident)).all()
        normalized = normalize_text(name)

        for resident in residents:
            full_name = f"{resident.first_name} {resident.last_name}"

            if fuzz.partial_ratio(normalized, normalize_text(full_name)) >= 75:
                return resident

        return None

    def find_unit_by_reference(self, building_id: str | None, reference: str | None) -> Unit | None:
        if not building_id or not reference:
            return None

        units = self.session.scalars(select(Unit).where(Unit.building_id == building_id)).all()
        normalized = normalize_text(reference)

        for unit in units:
            if normalize_text(unit.reference) == normalized:
                return unit

        return None

    def find_active_contract(self, building_id: str, domain: str | None) -> Contract | None:
        if not domain:
            return None

        statement = select(Contract).where(
            Contract.building_id == building_id,
            Contract.domain == domain,
            Contract.status == "active",
        )

        return self.session.scalars(statement).first()

    def find_provider_by_id(self, provider_id: str | None) -> Provider | None:
        if not provider_id:
            return None

        return self.session.get(Provider, provider_id)

    def find_procedure_by_issue_type(self, issue_type: str | None) -> Procedure | None:
        if not issue_type:
            return None

        statement = select(Procedure).where(Procedure.issue_type == issue_type)

        return self.session.scalars(statement).first()

    def find_open_tickets_by_building(self, building_id: str) -> list[Ticket]:
        statement = (
            select(Ticket)
            .where(Ticket.building_id == building_id)
            .where(Ticket.status.in_(["open", "in_progress", "waiting_provider"]))
            .limit(settings.max_recent_tickets)
        )

        return list(self.session.scalars(statement).all())

    def find_similar_open_ticket(self, building_id: str, issue_type: str | None) -> Ticket | None:
        if not issue_type:
            return None

        for ticket in self.find_open_tickets_by_building(building_id):
            if ticket.issue_type == issue_type or ticket.category == issue_type:
                return ticket

        return None

    def find_recent_interventions(self, building_id: str, domain: str | None) -> list[Intervention]:
        if not domain:
            return []

        statement = (
            select(Intervention)
            .where(Intervention.building_id == building_id, Intervention.domain == domain)
            .limit(5)
        )

        return list(self.session.scalars(statement).all())

    def append_ticket_event(
        self,
        event_type: TicketEventType,
        content: dict[str, Any],
        sources: list[str],
        ticket_id: str | None,
        request_id: str,
        trace_id: str | None,
        graph_path: list[str],
    ) -> TicketEvent:
        event = TicketEvent(
            id=f"E-{uuid4().hex[:10].upper()}",
            ticket_id=ticket_id,
            event_type=event_type.value,
            content_json=content,
            sources_json=sources,
            graph_path_json=graph_path,
            requires_human_validation=True,
            validated=False,
            safe_mode=True,
            created_by="PropertySupport AI",
            trace_id=trace_id,
            request_id=request_id,
            llm_model=settings.llm_model,
            created_at=datetime.now(UTC),
        )

        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)

        return event

    def list_ticket_events(self, limit: int = 50) -> list[TicketEvent]:
        statement = select(TicketEvent).order_by(TicketEvent.created_at.desc()).limit(limit)

        return list(self.session.scalars(statement).all())

    def get_ticket_event(self, event_id: str) -> TicketEvent | None:
        return self.session.get(TicketEvent, event_id)

    def data_health(self) -> dict[str, Any]:
        tables = {
            "buildings": self.session.scalar(select(func.count()).select_from(Building)),
            "providers": self.session.scalar(select(func.count()).select_from(Provider)),
            "contracts": self.session.scalar(select(func.count()).select_from(Contract)),
            "procedures": self.session.scalar(select(func.count()).select_from(Procedure)),
            "tickets": self.session.scalar(select(func.count()).select_from(Ticket)),
            "ticket_events": self.session.scalar(select(func.count()).select_from(TicketEvent)),
        }

        errors: list[str] = []

        for contract in self.session.scalars(select(Contract)).all():
            if not self.session.get(Building, contract.building_id):
                errors.append(f"Contract {contract.id} references missing building")

            if not self.session.get(Provider, contract.provider_id):
                errors.append(f"Contract {contract.id} references missing provider")

        for ticket in self.session.scalars(select(Ticket)).all():
            if not self.session.get(Building, ticket.building_id):
                errors.append(f"Ticket {ticket.id} references missing building")

        return {
            "status": "ok" if not errors else "error",
            "tables": tables,
            "errors": errors,
        }
