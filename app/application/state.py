"""
PropertySupport AI - app/application/state.py

TypedDict describing the shared LangGraph state.
"""

from typing import Any, TypedDict

from app.schemas.errors import AppIssue


class PropertySupportState(TypedDict, total=False):
    request_id: str
    trace_id: str | None
    user_message: str
    user_id: str | None
    conversation_id: str | None

    intent: str
    selected_branch: str
    confidence: float
    entities: dict[str, Any]

    context: dict[str, Any]
    decision: dict[str, Any]
    final_response: dict[str, Any]
    sources_used: list[str]

    graph_path: list[str]
    warnings: list[AppIssue]
    errors: list[AppIssue]
    debug: dict[str, Any] | None
