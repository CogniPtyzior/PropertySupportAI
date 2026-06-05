"""
PropertySupport AI - app/db/models.py

SQLAlchemy ORM models for the local SQLite demo database.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Building(Base, TimestampMixin):
    __tablename__ = "buildings"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    heating_type: Mapped[str] = mapped_column(String(80), nullable=False)
    has_elevator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_parking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    units: Mapped[list["Unit"]] = relationship(back_populates="building")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="building")


class Resident(Base, TimestampMixin):
    __tablename__ = "residents"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(40))
    preferred_channel: Mapped[str] = mapped_column(String(40), default="email", nullable=False)

    units: Mapped[list["Unit"]] = relationship(back_populates="resident")


class Unit(Base, TimestampMixin):
    __tablename__ = "units"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    building_id: Mapped[str] = mapped_column(ForeignKey("buildings.id"), nullable=False)
    reference: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_type: Mapped[str] = mapped_column(String(40), nullable=False)
    resident_id: Mapped[str | None] = mapped_column(ForeignKey("residents.id"))
    owner_name: Mapped[str | None] = mapped_column(String(160))

    building: Mapped[Building] = relationship(back_populates="units")
    resident: Mapped[Resident | None] = relationship(back_populates="units")


class Provider(Base, TimestampMixin):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(40))
    emergency_phone: Mapped[str | None] = mapped_column(String(40))
    coverage_area: Mapped[str] = mapped_column(String(120), nullable=False)


class Contract(Base, TimestampMixin):
    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    building_id: Mapped[str] = mapped_column(ForeignKey("buildings.id"), nullable=False)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"), nullable=False)
    domain: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    start_date: Mapped[str] = mapped_column(String(20), nullable=False)
    end_date: Mapped[str | None] = mapped_column(String(20))
    sla_hours: Mapped[int | None] = mapped_column(Integer)
    emergency_coverage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    building: Mapped[Building] = relationship()
    provider: Mapped[Provider] = relationship()


class Procedure(Base, TimestampMixin):
    __tablename__ = "procedures"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    steps_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    requires_emergency_provider: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    requires_human_validation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    building_id: Mapped[str] = mapped_column(ForeignKey("buildings.id"), nullable=False, index=True)
    unit_id: Mapped[str | None] = mapped_column(ForeignKey("units.id"))
    resident_id: Mapped[str | None] = mapped_column(ForeignKey("residents.id"))
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_provider_id: Mapped[str | None] = mapped_column(ForeignKey("providers.id"))

    building: Mapped[Building] = relationship(back_populates="tickets")
    provider: Mapped[Provider | None] = relationship()


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    ticket_id: Mapped[str | None] = mapped_column(ForeignKey("tickets.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    content_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    sources_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    graph_path_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    requires_human_validation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    safe_mode: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[str] = mapped_column(String(80), nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(120), index=True)
    request_id: Mapped[str | None] = mapped_column(String(120), index=True)
    llm_model: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Intervention(Base, TimestampMixin):
    __tablename__ = "interventions"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    ticket_id: Mapped[str | None] = mapped_column(ForeignKey("tickets.id"))
    building_id: Mapped[str] = mapped_column(ForeignKey("buildings.id"), nullable=False, index=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"), nullable=False)
    domain: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    scheduled_at: Mapped[str | None] = mapped_column(String(40))
    completed_at: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    provider: Mapped[Provider] = relationship()


class KnowledgeBaseEntry(Base, TimestampMixin):
    __tablename__ = "knowledge_base_entries"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
