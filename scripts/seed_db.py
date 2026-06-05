"""
PropertySupport AI - scripts/seed_db.py

Seed the SQLite database with coherent fictional property support data.
"""

from __future__ import annotations

import argparse

from sqlalchemy import delete

from app.db.models import (
    Building,
    Contract,
    Intervention,
    KnowledgeBaseEntry,
    Procedure,
    Provider,
    Resident,
    Ticket,
    TicketEvent,
    Unit,
)
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Clear demo data before seeding.")
    args = parser.parse_args()

    with SessionLocal() as session:
        if args.reset:
            for model in [
                TicketEvent,
                Intervention,
                Ticket,
                Procedure,
                Contract,
                Unit,
                Provider,
                Resident,
                Building,
                KnowledgeBaseEntry,
            ]:
                session.execute(delete(model))
            session.commit()

        if session.get(Building, "B001"):
            print("Database already seeded. Use --reset to recreate demo data.")
            return

        session.add_all(
            [
                Building(
                    id="B001",
                    name="Résidence Les Érables",
                    city="Annecy",
                    address="12 rue des Tilleuls",
                    postal_code="74000",
                    heating_type="collective_gas",
                    has_elevator=True,
                    has_parking=True,
                ),
                Building(
                    id="B002",
                    name="Résidence Belvédère",
                    city="Chambéry",
                    address="5 avenue du Lac",
                    postal_code="73000",
                    heating_type="district_heating",
                    has_elevator=True,
                    has_parking=False,
                ),
                Building(
                    id="B003",
                    name="Résidence Saint-Victor",
                    city="Aix-les-Bains",
                    address="28 boulevard des Alpes",
                    postal_code="73100",
                    heating_type="individual_electric",
                    has_elevator=False,
                    has_parking=True,
                ),
            ]
        )
        session.add_all(
            [
                Resident(
                    id="R001", first_name="Claire", last_name="Durand", email="claire@example.test"
                ),
                Resident(
                    id="R002", first_name="Nadia", last_name="Martin", email="nadia@example.test"
                ),
                Resident(
                    id="R003", first_name="Hugo", last_name="Bernard", email="hugo@example.test"
                ),
            ]
        )
        session.add_all(
            [
                Unit(
                    id="U001",
                    building_id="B001",
                    reference="A203",
                    floor=2,
                    unit_type="apartment",
                    resident_id="R001",
                ),
                Unit(
                    id="U002",
                    building_id="B001",
                    reference="B102",
                    floor=1,
                    unit_type="apartment",
                    resident_id="R002",
                ),
                Unit(
                    id="U003",
                    building_id="B002",
                    reference="C301",
                    floor=3,
                    unit_type="apartment",
                    resident_id="R003",
                ),
            ]
        )
        session.add_all(
            [
                Provider(
                    id="P001",
                    name="AlpChauffage",
                    domain="heating",
                    email="ops@alpchauffage.test",
                    phone="04 50 00 00 10",
                    emergency_phone="04 50 00 00 99",
                    coverage_area="Annecy / Chambéry",
                ),
                Provider(
                    id="P002",
                    name="LiftSecure",
                    domain="elevator",
                    email="support@liftsecure.test",
                    phone="04 79 00 00 20",
                    emergency_phone="04 79 00 00 99",
                    coverage_area="Savoie",
                ),
                Provider(
                    id="P003",
                    name="AquaDétection",
                    domain="plumbing",
                    email="contact@aquadetection.test",
                    phone="04 56 00 00 30",
                    emergency_phone="04 56 00 00 98",
                    coverage_area="Annecy",
                ),
                Provider(
                    id="P004",
                    name="ElecAlpes",
                    domain="electrical",
                    email="contact@elecalpes.test",
                    phone="04 79 00 00 40",
                    emergency_phone="04 79 00 00 97",
                    coverage_area="Aix-les-Bains",
                ),
                Provider(
                    id="P005",
                    name="Clean&Co",
                    domain="cleaning",
                    email="ops@cleanandco.test",
                    phone="04 50 00 00 50",
                    coverage_area="Annecy",
                ),
                Provider(
                    id="P006",
                    name="BadgeAccess",
                    domain="access",
                    email="support@badgeaccess.test",
                    phone="04 50 00 00 60",
                    coverage_area="Savoie",
                ),
            ]
        )
        session.commit()

        session.add_all(
            [
                Contract(
                    id="C001",
                    building_id="B001",
                    provider_id="P001",
                    domain="heating",
                    status="active",
                    start_date="2025-01-01",
                    sla_hours=4,
                    emergency_coverage=True,
                ),
                Contract(
                    id="C002",
                    building_id="B001",
                    provider_id="P002",
                    domain="elevator",
                    status="active",
                    start_date="2025-01-01",
                    sla_hours=2,
                    emergency_coverage=True,
                ),
                Contract(
                    id="C003",
                    building_id="B002",
                    provider_id="P002",
                    domain="elevator",
                    status="active",
                    start_date="2025-01-01",
                    sla_hours=2,
                    emergency_coverage=True,
                ),
                Contract(
                    id="C004",
                    building_id="B002",
                    provider_id="P001",
                    domain="heating",
                    status="inactive",
                    start_date="2023-01-01",
                    end_date="2024-12-31",
                    sla_hours=8,
                    emergency_coverage=False,
                ),
                Contract(
                    id="C005",
                    building_id="B003",
                    provider_id="P004",
                    domain="electrical",
                    status="active",
                    start_date="2025-01-01",
                    sla_hours=8,
                    emergency_coverage=True,
                ),
            ]
        )

        session.add_all(
            [
                Procedure(
                    id="PROC_HEATING_OUTAGE",
                    code="PROC_HEATING_OUTAGE",
                    category="technical_emergency",
                    issue_type="heating_outage",
                    title="Collective heating outage",
                    description="Handle a suspected collective heating outage.",
                    steps_json=[
                        "Check whether multiple residents are affected.",
                        "Check existing tickets in the last 72 hours.",
                        "Contact the active heating provider if a contract exists.",
                        "Notify residents with a clear status update.",
                    ],
                    requires_emergency_provider=True,
                ),
                Procedure(
                    id="PROC_ELEVATOR_BLOCKED",
                    code="PROC_ELEVATOR_BLOCKED",
                    category="critical_emergency",
                    issue_type="elevator_blocked_with_person",
                    title="Elevator blocked with person inside",
                    description="Handle elevator safety incidents.",
                    steps_json=[
                        "Do not attempt manual intervention.",
                        "Contact the emergency elevator provider immediately.",
                        "Escalate to emergency services if the person is in danger.",
                    ],
                    requires_emergency_provider=True,
                ),
                Procedure(
                    id="PROC_WATER_LEAK",
                    code="PROC_WATER_LEAK",
                    category="technical_emergency",
                    issue_type="water_leak",
                    title="Water leak",
                    description="Handle active or suspected water leaks.",
                    steps_json=[
                        "Identify affected unit and visible damage.",
                        "Check if the leak is active.",
                        "Contact plumbing provider when contract exists.",
                        "Ask for photos if needed.",
                    ],
                    requires_emergency_provider=True,
                ),
            ]
        )

        session.add_all(
            [
                Ticket(
                    id="T001",
                    building_id="B001",
                    category="technical_emergency",
                    issue_type="heating_outage",
                    priority="high",
                    status="open",
                    title="Collective heating outage",
                    summary="Several residents reported no heating since this morning.",
                    assigned_provider_id="P001",
                ),
                Ticket(
                    id="T002",
                    building_id="B001",
                    unit_id="U002",
                    resident_id="R002",
                    category="administrative",
                    issue_type="access_badge",
                    priority="medium",
                    status="open",
                    title="Parking badge replacement",
                    summary="Resident requested a replacement parking badge.",
                    assigned_provider_id="P006",
                ),
                Ticket(
                    id="T003",
                    building_id="B002",
                    category="technical_emergency",
                    issue_type="elevator_outage",
                    priority="high",
                    status="in_progress",
                    title="Elevator unavailable",
                    summary="Elevator stopped between floors, no person reported inside.",
                    assigned_provider_id="P002",
                ),
            ]
        )

        session.add_all(
            [
                Intervention(
                    id="I001",
                    ticket_id="T001",
                    building_id="B001",
                    provider_id="P001",
                    domain="heating",
                    scheduled_at="2026-05-23T08:30:00",
                    status="planned",
                    summary="Heating technician planned.",
                ),
                Intervention(
                    id="I002",
                    ticket_id="T003",
                    building_id="B002",
                    provider_id="P002",
                    domain="elevator",
                    scheduled_at="2026-05-22T14:00:00",
                    status="planned",
                    summary="Elevator diagnostic visit.",
                ),
                KnowledgeBaseEntry(
                    id="KB001",
                    code="SAFE_MODE",
                    title="Safe mode principle",
                    category="safety",
                    content="AI suggestions require human validation.",
                    tags_json=["safe-mode", "tickets"],
                ),
            ]
        )
        session.commit()
        print("Seed completed: 3 buildings, 6 providers, 5 contracts, 3 tickets.")


if __name__ == "__main__":
    main()
