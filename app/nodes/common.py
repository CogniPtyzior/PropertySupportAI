"""
PropertySupport AI - app/nodes/common.py

Shared helpers for LangGraph nodes.
"""

from app.application.state import PropertySupportState
from app.schemas.errors import AppIssue


def append_path(state: PropertySupportState, node_name: str) -> list[str]:
    """Append a node name to the graph path."""
    return [*state.get("graph_path", []), node_name]


def warning(code: str, message: str) -> AppIssue:
    """Create a recoverable warning."""
    return AppIssue(code=code, message=message, recoverable=True)


def error(code: str, message: str) -> AppIssue:
    """Create a non-recoverable error."""
    return AppIssue(code=code, message=message, recoverable=False)
