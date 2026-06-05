"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-05-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "buildings",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("city", sa.String(80), nullable=False),
        sa.Column("address", sa.String(200), nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=False),
        sa.Column("heating_type", sa.String(80), nullable=False),
        sa.Column("has_elevator", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_parking", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_buildings_name", "buildings", ["name"])
    op.create_index("idx_buildings_city", "buildings", ["city"])

    op.create_table(
        "residents",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("email", sa.String(160)),
        sa.Column("phone", sa.String(40)),
        sa.Column("preferred_channel", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_residents_last_name", "residents", ["last_name"])

    op.create_table(
        "providers",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("domain", sa.String(40), nullable=False),
        sa.Column("email", sa.String(160)),
        sa.Column("phone", sa.String(40)),
        sa.Column("emergency_phone", sa.String(40)),
        sa.Column("coverage_area", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_providers_name", "providers", ["name"])
    op.create_index("idx_providers_domain", "providers", ["domain"])

    op.create_table(
        "units",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("building_id", sa.String(20), sa.ForeignKey("buildings.id"), nullable=False),
        sa.Column("reference", sa.String(40), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=False),
        sa.Column("unit_type", sa.String(40), nullable=False),
        sa.Column("resident_id", sa.String(20), sa.ForeignKey("residents.id")),
        sa.Column("owner_name", sa.String(160)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("building_id", "reference", name="uq_units_building_reference"),
    )
    op.create_index("idx_units_reference", "units", ["reference"])

    op.create_table(
        "contracts",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("building_id", sa.String(20), sa.ForeignKey("buildings.id"), nullable=False),
        sa.Column("provider_id", sa.String(20), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("domain", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("start_date", sa.String(20), nullable=False),
        sa.Column("end_date", sa.String(20)),
        sa.Column("sla_hours", sa.Integer()),
        sa.Column("emergency_coverage", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_contracts_domain", "contracts", ["domain"])
    op.create_index("idx_contracts_status", "contracts", ["status"])
    op.create_index(
        "idx_contracts_building_domain_status",
        "contracts",
        [
            "building_id",
            "domain",
            "status",
        ],
    )

    op.create_table(
        "procedures",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("issue_type", sa.String(80), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("steps_json", sa.JSON(), nullable=False),
        sa.Column("requires_emergency_provider", sa.Boolean(), nullable=False),
        sa.Column("requires_human_validation", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_procedures_issue_type", "procedures", ["issue_type"])

    op.create_table(
        "tickets",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("building_id", sa.String(20), sa.ForeignKey("buildings.id"), nullable=False),
        sa.Column("unit_id", sa.String(20), sa.ForeignKey("units.id")),
        sa.Column("resident_id", sa.String(20), sa.ForeignKey("residents.id")),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("issue_type", sa.String(80), nullable=False),
        sa.Column("priority", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("assigned_provider_id", sa.String(20), sa.ForeignKey("providers.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_tickets_building_id", "tickets", ["building_id"])
    op.create_index("idx_tickets_issue_type", "tickets", ["issue_type"])
    op.create_index("idx_tickets_status", "tickets", ["status"])
    op.create_index(
        "idx_tickets_building_issue_status",
        "tickets",
        [
            "building_id",
            "issue_type",
            "status",
        ],
    )

    op.create_table(
        "ticket_events",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("ticket_id", sa.String(20), sa.ForeignKey("tickets.id")),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("content_json", sa.JSON(), nullable=False),
        sa.Column("sources_json", sa.JSON(), nullable=False),
        sa.Column("graph_path_json", sa.JSON(), nullable=False),
        sa.Column("requires_human_validation", sa.Boolean(), nullable=False),
        sa.Column("validated", sa.Boolean(), nullable=False),
        sa.Column("safe_mode", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(80), nullable=False),
        sa.Column("trace_id", sa.String(120)),
        sa.Column("request_id", sa.String(120)),
        sa.Column("llm_model", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_ticket_events_ticket_id", "ticket_events", ["ticket_id"])
    op.create_index("idx_ticket_events_event_type", "ticket_events", ["event_type"])
    op.create_index("idx_ticket_events_trace_id", "ticket_events", ["trace_id"])
    op.create_index("idx_ticket_events_request_id", "ticket_events", ["request_id"])

    op.create_table(
        "interventions",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("ticket_id", sa.String(20), sa.ForeignKey("tickets.id")),
        sa.Column("building_id", sa.String(20), sa.ForeignKey("buildings.id"), nullable=False),
        sa.Column("provider_id", sa.String(20), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("domain", sa.String(40), nullable=False),
        sa.Column("scheduled_at", sa.String(40)),
        sa.Column("completed_at", sa.String(40)),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_interventions_building_id", "interventions", ["building_id"])
    op.create_index("idx_interventions_domain", "interventions", ["domain"])

    op.create_table(
        "knowledge_base_entries",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_knowledge_category", "knowledge_base_entries", ["category"])


def downgrade() -> None:
    op.drop_table("knowledge_base_entries")
    op.drop_table("interventions")
    op.drop_table("ticket_events")
    op.drop_table("tickets")
    op.drop_table("procedures")
    op.drop_table("contracts")
    op.drop_table("units")
    op.drop_table("providers")
    op.drop_table("residents")
    op.drop_table("buildings")
