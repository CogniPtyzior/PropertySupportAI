"""
PropertySupport AI - app/api/routes.py

FastAPI routes. Routes are intentionally thin.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.graph import build_graph
from app.application.workflow_service import process_message
from app.config import settings
from app.db.repositories import PropertySupportRepository
from app.db.session import get_session
from app.llm.prompt_loader import validate_required_prompts
from app.schemas.api import AskRequest, AskResponse

router = APIRouter()


@router.get("/health", tags=["Health"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@router.get("/version")
def version() -> dict:
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@router.get("/data-health", tags=["Health"])
def data_health(session: Session = Depends(get_session)) -> dict:
    repo = PropertySupportRepository(session)
    prompt_errors = validate_required_prompts()
    graph_status = "compiled"
    try:
        build_graph(session)
    except Exception as exc:
        graph_status = f"error: {exc}"
    payload = repo.data_health()
    payload["prompts"] = "ok" if not prompt_errors else {"missing": prompt_errors}
    payload["graph"] = graph_status
    return payload


@router.get("/demo/examples")
def demo_examples() -> dict:
    return {
        "examples": [
            "Who is the heating provider for Les Érables?",
            "Prepare a resident message for tomorrow's heating intervention.",
            "Add to the heating ticket that three more residents reported the outage.",
            "Several residents have no heating at Les Érables. What should I do?",
            "There is a problem in the building.",
        ]
    }


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, session: Session = Depends(get_session)) -> AskResponse:
    return process_message(request, session)


@router.get("/ticket-events")
def ticket_events(limit: int = 50, session: Session = Depends(get_session)) -> dict:
    repo = PropertySupportRepository(session)
    events = repo.list_ticket_events(limit=limit)
    return {"items": [_ticket_event_payload(event) for event in events]}


@router.get("/ticket-events/{event_id}")
def ticket_event(event_id: str, session: Session = Depends(get_session)) -> dict:
    repo = PropertySupportRepository(session)
    event = repo.get_ticket_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Ticket event not found")
    return _ticket_event_payload(event, include_graph_path=True)


def _ticket_event_payload(event, include_graph_path: bool = False) -> dict:
    payload = {
        "id": event.id,
        "ticket_id": event.ticket_id,
        "event_type": event.event_type,
        "content": event.content_json,
        "sources": event.sources_json,
        "requires_human_validation": event.requires_human_validation,
        "validated": event.validated,
        "safe_mode": event.safe_mode,
        "trace_id": event.trace_id,
        "request_id": event.request_id,
        "created_at": event.created_at.isoformat(),
    }
    if include_graph_path:
        payload["graph_path"] = event.graph_path_json
    return payload
