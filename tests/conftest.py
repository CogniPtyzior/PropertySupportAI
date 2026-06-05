import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Building, Contract, Provider, Ticket


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        db.add(
            Building(
                id="B001",
                name="Résidence Les Érables",
                city="Annecy",
                address="x",
                postal_code="74000",
                heating_type="collective_gas",
            )
        )
        db.add(Provider(id="P001", name="AlpChauffage", domain="heating", coverage_area="Annecy"))
        db.add(
            Contract(
                id="C001",
                building_id="B001",
                provider_id="P001",
                domain="heating",
                status="active",
                start_date="2025-01-01",
                sla_hours=4,
                emergency_coverage=True,
            )
        )
        db.add(
            Ticket(
                id="T001",
                building_id="B001",
                category="technical_emergency",
                issue_type="heating_outage",
                priority="high",
                status="open",
                title="Heating outage",
                summary="Open heating outage.",
                assigned_provider_id="P001",
            )
        )
        db.commit()
        yield db
