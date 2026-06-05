from app.domain.policies import (
    can_suggest_provider_contact,
    decide_ticket_action,
    is_critical_emergency,
    validate_safe_ticket_patch,
)


def test_elevator_blocked_with_person_is_critical():
    assert is_critical_emergency("elevator_blocked_with_person", None, True)


def test_provider_contact_requires_active_contract():
    assert not can_suggest_provider_contact(False, True, True)


def test_decide_ticket_action_updates_existing_ticket():
    assert decide_ticket_action({"id": "T001"}) == "ticket_update_suggestion"


def test_safe_ticket_patch_rejects_status_change():
    is_valid, errors = validate_safe_ticket_patch({"status": "closed"})
    assert not is_valid
    assert errors
