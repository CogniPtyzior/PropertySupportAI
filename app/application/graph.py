"""
PropertySupport AI - app/application/graph.py

Defines and compiles the LangGraph workflow.

The graph deliberately keeps routing deterministic:
- the LLM classifies and extracts entities;
- retrieve_context reconciles business entities from SQLite;
- routing decisions use the deterministic context, not raw LLM output only.
"""

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.application.state import PropertySupportState
from app.domain.enums import Intent
from app.nodes.clarification import ask_clarification_node
from app.nodes.classify import classify_request_node
from app.nodes.communication import generate_message_draft_node
from app.nodes.extract_entities import extract_entities_node
from app.nodes.incident_analysis import (
    decide_incident_action_node,
    generate_incident_response_node,
)
from app.nodes.lookup import generate_lookup_answer_node
from app.nodes.retrieve_context import make_retrieve_context_node
from app.nodes.ticket_workflow import (
    decide_ticket_action_node,
    generate_ticket_suggestion_node,
    make_write_ticket_event_node,
)
from app.nodes.validation import validate_response_node


def route_intent(state: PropertySupportState) -> str:
    """Route the workflow after initial classification and entity extraction."""
    intent = state.get("intent", Intent.CLARIFICATION.value)

    if intent == Intent.LOOKUP.value:
        return "lookup"

    if intent == Intent.COMMUNICATION.value:
        return "communication"

    if intent == Intent.TICKET_WORKFLOW.value:
        return "ticket_workflow"

    if intent == Intent.INCIDENT_ANALYSIS.value:
        return "incident_analysis"

    return "clarification"


def route_after_context(state: PropertySupportState) -> str:
    """
    Route after deterministic context retrieval.

    Important:
    `retrieve_context` may infer missing values that the LLM failed to extract,
    especially `building` and `issue_type`. Therefore routing must use
    `state["context"]`, not only `state["entities"]`.

    Rules:
    - lookup can continue with partial context;
    - communication can continue with available context;
    - ticket_workflow requires building + issue_type;
    - incident_analysis requires building + issue_type;
    - missing critical context routes to clarification.
    """
    intent = state.get("intent", Intent.CLARIFICATION.value)
    context = state.get("context", {}) or {}

    building = context.get("building")
    issue_type = context.get("issue_type")

    if intent == Intent.LOOKUP.value:
        return Intent.LOOKUP.value

    if intent == Intent.COMMUNICATION.value:
        return Intent.COMMUNICATION.value

    if intent == Intent.TICKET_WORKFLOW.value:
        if building and issue_type:
            return Intent.TICKET_WORKFLOW.value

        return Intent.CLARIFICATION.value

    if intent == Intent.INCIDENT_ANALYSIS.value:
        if building and issue_type:
            return Intent.INCIDENT_ANALYSIS.value

        return Intent.CLARIFICATION.value

    return Intent.CLARIFICATION.value


def build_graph(session: Session):
    """Build and compile the workflow graph for a database session."""
    builder = StateGraph(PropertySupportState)

    retrieve_context_node = make_retrieve_context_node(session)
    write_ticket_event_node = make_write_ticket_event_node(session)

    builder.add_node("classify_request", classify_request_node)
    builder.add_node("extract_entities", extract_entities_node)
    builder.add_node("ask_clarification", ask_clarification_node)
    builder.add_node("retrieve_context", retrieve_context_node)

    builder.add_node("generate_lookup_answer", generate_lookup_answer_node)
    builder.add_node("generate_message_draft", generate_message_draft_node)

    builder.add_node("decide_ticket_action", decide_ticket_action_node)
    builder.add_node("generate_ticket_suggestion", generate_ticket_suggestion_node)
    builder.add_node("write_ticket_event", write_ticket_event_node)

    builder.add_node("decide_incident_action", decide_incident_action_node)
    builder.add_node("generate_incident_response", generate_incident_response_node)

    builder.add_node("validate_response", validate_response_node)

    builder.set_entry_point("classify_request")

    builder.add_edge("classify_request", "extract_entities")

    builder.add_conditional_edges(
        "extract_entities",
        route_intent,
        {
            "lookup": "retrieve_context",
            "communication": "retrieve_context",
            "ticket_workflow": "retrieve_context",
            "incident_analysis": "retrieve_context",
            "clarification": "ask_clarification",
        },
    )

    builder.add_conditional_edges(
        "retrieve_context",
        route_after_context,
        {
            Intent.LOOKUP.value: "generate_lookup_answer",
            Intent.COMMUNICATION.value: "generate_message_draft",
            Intent.TICKET_WORKFLOW.value: "decide_ticket_action",
            Intent.INCIDENT_ANALYSIS.value: "decide_incident_action",
            Intent.CLARIFICATION.value: "ask_clarification",
        },
    )

    builder.add_edge("decide_ticket_action", "generate_ticket_suggestion")
    builder.add_edge("generate_ticket_suggestion", "write_ticket_event")

    builder.add_edge("decide_incident_action", "generate_incident_response")

    for node_name in [
        "ask_clarification",
        "generate_lookup_answer",
        "generate_message_draft",
        "write_ticket_event",
        "generate_incident_response",
    ]:
        builder.add_edge(node_name, "validate_response")

    builder.add_edge("validate_response", END)

    return builder.compile()
