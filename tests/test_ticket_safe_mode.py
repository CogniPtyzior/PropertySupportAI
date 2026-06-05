from app.db.repositories import PropertySupportRepository
from app.domain.enums import TicketEventType


def test_append_ticket_event_does_not_modify_ticket(session):
    repo = PropertySupportRepository(session)
    event = repo.append_ticket_event(
        event_type=TicketEventType.AI_UPDATE_SUGGESTED,
        content={"summary_addition": "New report."},
        sources=["tickets:T001"],
        ticket_id="T001",
        request_id="REQ-TEST",
        trace_id="trace-test",
        graph_path=["test"],
    )
    assert event.id
    ticket = repo.find_similar_open_ticket("B001", "heating_outage")
    assert ticket is not None
    assert ticket.status == "open"
