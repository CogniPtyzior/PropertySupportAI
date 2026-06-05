"""
PropertySupport AI - app/application/workflow_service.py

Application service called by FastAPI routes.
"""

from uuid import uuid4

from sqlalchemy.orm import Session

from app.application.graph import build_graph
from app.application.state import PropertySupportState
from app.config import settings
from app.domain.enums import Intent, ResponseStatus
from app.observability.tracing import tracer
from app.schemas.api import AskRequest, AskResponse
from app.schemas.errors import AppIssue


def _safe_response_status(value: object) -> ResponseStatus:
    """Return a stable response status even when LLM output is unexpected."""
    try:
        return ResponseStatus(str(value))
    except ValueError:
        return ResponseStatus.PARTIAL_ANSWER


def _safe_intent(value: object) -> Intent | None:
    """Return a stable intent enum or None when the value is unexpected."""
    if value is None:
        return None

    try:
        return Intent(str(value))
    except ValueError:
        return None


def process_message(request: AskRequest, session: Session) -> AskResponse:
    """Process one user message through the LangGraph workflow."""
    request_id = f"REQ-{uuid4().hex[:12].upper()}"
    trace_id = tracer.start_trace(request_id=request_id, message=request.message)
    initial_state: PropertySupportState = {
        "request_id": request_id,
        "trace_id": trace_id,
        "user_message": request.message,
        "user_id": request.user_id,
        "conversation_id": request.conversation_id,
        "graph_path": [],
        "warnings": [],
        "errors": [],
        "sources_used": [],
    }

    try:
        with tracer.request_observation(
            request_id=request_id,
            message=request.message,
            metadata={"conversation_id": request.conversation_id, "user_id": request.user_id},
        ):
            state = build_graph(session).invoke(initial_state)
            final = state.get("final_response", {})
            status = _safe_response_status(final.get("status", ResponseStatus.PARTIAL_ANSWER.value))
            intent = _safe_intent(state.get("intent"))
            debug = state.get("debug") if settings.include_debug_metadata else None

            output = {
                "status": status.value,
                "intent": intent.value if intent else None,
                "selected_branch": state.get("selected_branch"),
                "sources_used": final.get("sources_used", []),
                "graph_path": state.get("graph_path", []),
                "warnings_count": len(state.get("warnings", [])),
                "errors_count": len(state.get("errors", [])),
            }
            tracer.update_current_observation(output)
            tracer.score("safe_mode_respected", True)
            tracer.score("sources_present", bool(final.get("sources_used")))

            response = AskResponse(
                request_id=request_id,
                status=status,
                intent=intent,
                selected_branch=state.get("selected_branch"),
                summary=final.get("summary", "No summary was generated."),
                data=final.get("data", {}),
                sources_used=final.get("sources_used", []),
                warnings=state.get("warnings", []),
                errors=state.get("errors", []),
                trace_id=trace_id,
                debug=debug,
            )
            return response
    except Exception as exc:
        return AskResponse(
            request_id=request_id,
            status=ResponseStatus.ERROR,
            intent=None,
            selected_branch=None,
            summary="The request failed due to an internal error.",
            data={},
            sources_used=[],
            warnings=[],
            errors=[AppIssue(code="INTERNAL_ERROR", message=str(exc), recoverable=False)],
            trace_id=trace_id,
            debug=None,
        )
    finally:
        tracer.flush()
