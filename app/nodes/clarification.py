"""
PropertySupport AI - app/nodes/clarification.py

Generates safe clarification responses for vague requests.
"""

from app.application.state import PropertySupportState
from app.domain.enums import ResponseStatus
from app.nodes.common import append_path


def ask_clarification_node(state: PropertySupportState) -> dict:
    path = append_path(state, "ask_clarification")
    response = {
        "status": ResponseStatus.NEEDS_CLARIFICATION.value,
        "summary": "The request is missing information required to answer safely.",
        "clarifying_question": (
            "Can you specify the building concerned and the exact issue to handle?"
        ),
        "data": {},
        "sources_used": [],
    }
    return {"final_response": response, "graph_path": path}
