import pytest

from app.application.graph import build_graph
from app.domain.enums import Intent, ResponseStatus, TicketAction
from app.llm.provider import LLMInvocationError
from app.nodes.classify import classify_request_node
from app.nodes.communication import generate_message_draft_node
from app.nodes.extract_entities import extract_entities_node
from app.nodes.lookup import generate_lookup_answer_node
from app.nodes.ticket_workflow import generate_ticket_suggestion_node
from app.schemas.llm import (
    ClassificationResult,
    ExtractedEntities,
    LookupAnswerDraft,
    MessageDraft,
    TicketSuggestionDraft,
)


def test_build_graph_compiles(session):
    graph = build_graph(session)
    assert graph is not None


def test_classify_request_node_returns_intent_and_graph_path(monkeypatch):
    def fake_invoke_json(*_, **__):
        return ClassificationResult(intent=Intent.COMMUNICATION, confidence=0.82, reason="Bonne classification")

    monkeypatch.setattr("app.nodes.classify.llm_service.invoke_json", fake_invoke_json)

    result = classify_request_node({"user_message": "Je veux envoyer un message", "graph_path": []})

    assert result["intent"] == Intent.COMMUNICATION.value
    assert result["selected_branch"] == Intent.COMMUNICATION.value
    assert result["confidence"] == 0.82
    assert result["graph_path"] == ["classify_request"]
    assert "warnings" not in result


def test_classify_request_node_low_confidence_routes_to_clarification(monkeypatch):
    def fake_invoke_json(*_, **__):
        return ClassificationResult(intent=Intent.COMMUNICATION, confidence=0.41, reason="Faible confiance")

    monkeypatch.setattr("app.nodes.classify.llm_service.invoke_json", fake_invoke_json)

    result = classify_request_node({"user_message": "J’ai un problème", "warnings": [], "graph_path": []})

    assert result["intent"] == Intent.CLARIFICATION.value
    assert result["selected_branch"] == Intent.CLARIFICATION.value
    assert result["confidence"] == 0.41
    assert result["graph_path"] == ["classify_request"]
    assert result["warnings"][0].code == "LLM_LOW_CONFIDENCE"


def test_extract_entities_node_returns_parsed_entities(monkeypatch):
    def fake_invoke_json(*_, **__):
        return ExtractedEntities(building_name="Résidence Les Érables", issue_type="heating_outage")

    monkeypatch.setattr("app.nodes.extract_entities.llm_service.invoke_json", fake_invoke_json)

    result = extract_entities_node({"user_message": "Le chauffage ne marche plus", "graph_path": []})

    assert result["entities"]["building_name"] == "Résidence Les Érables"
    assert result["entities"]["issue_type"] == "heating_outage"
    assert result["graph_path"] == ["extract_entities"]


def test_generate_message_draft_node_returns_success_response(monkeypatch):
    def fake_invoke_json(*_, **__):
        return MessageDraft(
            message_type="reply",
            draft_message="Bonjour, nous allons envoyer un technicien.",
            missing_information=[],
            sources_used=["contract"],
        )

    monkeypatch.setattr("app.nodes.communication.llm_service.invoke_json", fake_invoke_json)

    result = generate_message_draft_node(
        {
            "user_message": "Mon radiateur ne chauffe plus.",
            "context": {"building": {"name": "Résidence Les Érables"}},
            "graph_path": [],
        }
    )

    assert result["final_response"]["status"] == ResponseStatus.SUCCESS.value
    assert result["final_response"]["data"]["draft_message"] == "Bonjour, nous allons envoyer un technicien."
    assert result["final_response"]["sources_used"] == ["contract"]
    assert result["graph_path"] == ["generate_message_draft"]


def test_generate_message_draft_node_returns_partial_answer_on_failure(monkeypatch):
    def fake_invoke_json(*_, **__):
        raise LLMInvocationError("Service indisponible")

    monkeypatch.setattr("app.nodes.communication.llm_service.invoke_json", fake_invoke_json)

    result = generate_message_draft_node(
        {
            "user_message": "Mon radiateur ne chauffe plus.",
            "context": {"building": {"name": "Résidence Les Érables"}},
            "warnings": [],
            "sources_used": [],
            "graph_path": [],
        }
    )

    assert result["final_response"]["status"] == ResponseStatus.PARTIAL_ANSWER.value
    assert result["warnings"][0].code == "LLM_MESSAGE_FAILED"
    assert result["graph_path"] == ["generate_message_draft"]


def test_generate_lookup_answer_node_produces_partial_when_no_answer(monkeypatch):
    def fake_invoke_json(*_, **__):
        return LookupAnswerDraft(summary="Aucune réponse trouvée.", answer_found=False, sources_used=["contrat"])

    monkeypatch.setattr("app.nodes.lookup.llm_service.invoke_json", fake_invoke_json)

    result = generate_lookup_answer_node(
        {
            "user_message": "Quel est le contrat de chauffage ?",
            "context": {"building": {"name": "Résidence Les Érables"}},
            "graph_path": [],
        }
    )

    assert result["final_response"]["status"] == ResponseStatus.PARTIAL_ANSWER.value
    assert result["final_response"]["data"]["answer_found"] is False
    assert result["graph_path"] == ["generate_lookup_answer"]


def test_generate_ticket_suggestion_node_applies_safe_mode_defaults(monkeypatch):
    def fake_invoke_json(*_, **__):
        return TicketSuggestionDraft(
            action_type=TicketAction.CREATE_SUGGESTION,
            ticket_id=None,
            title=None,
            summary_addition="Le chauffage est en panne.",
            priority_suggestion=None,
            recommended_actions=["Contacter le prestataire"],
            requires_human_validation=False,
            sources_used=["prompt"],
        )

    monkeypatch.setattr("app.nodes.ticket_workflow.llm_service.invoke_json", fake_invoke_json)

    state = {
        "user_message": "Mon chauffage ne fonctionne plus.",
        "context": {"building": {"name": "Résidence Les Érables"}, "issue_type": "heating_outage"},
        "decision": {"ticket_action": TicketAction.CREATE_SUGGESTION.value},
        "sources_used": ["existing"],
        "graph_path": [],
    }

    result = generate_ticket_suggestion_node(state)
    suggestion = result["decision"]["ticket_suggestion"]

    assert suggestion["action_type"] == TicketAction.CREATE_SUGGESTION.value
    assert suggestion["requires_human_validation"] is True
    assert suggestion["ticket_id"] is None
    assert suggestion["title"] == "Heating Outage - Résidence Les Érables"
    assert result["graph_path"] == ["generate_ticket_suggestion"]
