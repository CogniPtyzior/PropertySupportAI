# PropertySupport AI - Technical Documentation

## Purpose

PropertySupport AI is a production-like backend demo showing how to build a safe GenAI
workflow application. It uses FastAPI, LangGraph, LangChain, Pydantic, SQLAlchemy,
SQLite, Alembic and Langfuse.

## Design principle

The project is an LLM-assisted workflow, not an autonomous agent. LangGraph controls the
process. Python policies make sensitive decisions. The LLM helps with language tasks.

## Key files

- `app/main.py`: FastAPI entry point.
- `app/api/routes.py`: HTTP endpoints.
- `app/application/graph.py`: LangGraph workflow.
- `app/application/state.py`: shared graph state.
- `app/application/workflow_service.py`: API-to-workflow service.
- `app/db/models.py`: SQLAlchemy ORM models.
- `app/db/repositories.py`: database access layer.
- `app/domain/policies.py`: deterministic business rules.
- `app/schemas/api.py`: FastAPI DTOs.
- `app/schemas/llm.py`: expected LLM JSON schemas.
- `app/llm/provider.py`: LangChain/Ollama wrapper.
- `app/observability/tracing.py`: best-effort Langfuse wrapper.
- `app/prompts/*.md`: versioned prompt assets.

## Workflow branches

- `clarification`
- `lookup`
- `communication`
- `ticket_workflow`
- `incident_analysis`

## Safe mode

The workflow does not mutate `tickets`. It only writes `ticket_events` when a ticket
creation or update suggestion is generated.

## Source references

Responses use compact source references such as:

```text
buildings:B001
contracts:C001
providers:P001
tickets:T001
procedures:PROC_HEATING_OUTAGE
```

## Database

SQLite is managed by SQLAlchemy and Alembic. Demo data is seeded by `scripts/seed_db.py`.

## Error handling

- Business ambiguity returns `needs_clarification`.
- Missing provider/contract returns `human_validation_required`.
- LLM failures return safe partial answers or errors.
- Langfuse failures never break the API.
