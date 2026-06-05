from app.db.repositories import PropertySupportRepository


def test_find_building_by_name(session):
    repo = PropertySupportRepository(session)
    building = repo.find_building_by_name("Les Erables")
    assert building is not None
    assert building.id == "B001"


def test_find_active_contract(session):
    repo = PropertySupportRepository(session)
    contract = repo.find_active_contract("B001", "heating")
    assert contract is not None
    assert contract.id == "C001"


def test_find_similar_open_ticket(session):
    repo = PropertySupportRepository(session)
    ticket = repo.find_similar_open_ticket("B001", "heating_outage")
    assert ticket is not None
    assert ticket.id == "T001"
