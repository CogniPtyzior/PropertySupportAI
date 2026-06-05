"""
PropertySupport AI - app/nodes/validation.py

Final response validation and normalization.
"""

from app.application.state import PropertySupportState
from app.config import settings
from app.domain.enums import Intent, ResponseStatus
from app.domain.policies import response_needs_sources
from app.nodes.common import append_path, warning


def validate_response_node(state: PropertySupportState) -> dict:
    path = append_path(state, "validate_response")
    final = state.get("final_response") or {
        "status": ResponseStatus.NEEDS_CLARIFICATION.value,
        "summary": "The request could not be completed safely.",
        "data": {},
        "sources_used": [],
    }
    warnings = list(state.get("warnings", []))
    intent = state.get("intent")
    final["status"] = _normalize_status(final.get("status"), warnings)
    final["sources_used"] = _normalize_sources(
        final.get("sources_used"),
        state.get("sources_used", []),
    )

    if response_needs_sources(intent) and not final["sources_used"]:
        warnings.append(warning("SOURCES_MISSING", "No source reference was available."))
        if intent != Intent.CLARIFICATION.value:
            final["status"] = ResponseStatus.PARTIAL_ANSWER.value

    debug = None
    if settings.include_debug_metadata:
        debug = {
            "graph_path": path,
            "context": state.get("context", {}),
            "decision": state.get("decision", {}),
        }
    return {"final_response": final, "warnings": warnings, "graph_path": path, "debug": debug}


def _normalize_status(raw_status, warnings) -> str:
    try:
        return ResponseStatus(raw_status).value
    except ValueError:
        warnings.append(warning("INVALID_RESPONSE_STATUS", f"Invalid status: {raw_status}"))
        return ResponseStatus.PARTIAL_ANSWER.value


def _normalize_sources(raw_sources, deterministic_sources: list[str]) -> list[str]:
    """Prefer deterministic DB source references over LLM-provided references."""
    allowed = set(deterministic_sources)
    if allowed:
        filtered = [source for source in raw_sources or [] if source in allowed]
        return sorted(set(filtered or deterministic_sources))
    return sorted(set(raw_sources or []))
