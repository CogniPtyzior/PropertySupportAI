# PropertySupport AI

PropertySupport AI is a production-like GenAI workflow API for property support teams.
It receives a natural-language support request, classifies it, retrieves business context
from SQLite, runs an explicit LangGraph workflow, validates LLM outputs with Pydantic,
and returns a sourced JSON response.

The project is deliberately **not** a free autonomous agent. It is an LLM-assisted
workflow: Python policies and repositories handle sensitive business decisions, while
the LLM helps with classification, extraction, synthesis and drafting.

## Stack

- FastAPI
- Pydantic
- LangGraph
- LangChain
- Ollama
- SQLAlchemy 2.x
- SQLite
- Alembic
- Langfuse
- pytest
- Ruff
- Pyright
- Docker

## Safe mode

The GenAI workflow never modifies `tickets` directly. It only writes suggestions to
`ticket_events` when `SAFE_MODE=true` and `WRITE_TICKET_EVENTS=true`.

## Quickstart on Windows PowerShell

```powershell
Copy-Item .env.example .env
.\scripts\install.ps1
.\scripts\migrate.ps1
.\scripts\seed.ps1 -Reset
.\scripts\dev.ps1
```

Open:

- Swagger UI: <http://localhost:8001/docs>
- ReDoc: <http://localhost:8001/redoc>
- Health: <http://localhost:8001/health>
- Data health: <http://localhost:8001/data-health>

## Ollama

Recommended local model:

```powershell
ollama pull mistral-nemo:12b
ollama run mistral-nemo:12b
```

Default `.env`:

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=mistral-nemo:12b
```

## Database

Apply migrations:

```powershell
.\scripts\migrate.ps1
```

Create a new migration:

```powershell
.\scripts\new-migration.ps1 -Message "add new field"
```

Seed database:

```powershell
.\scripts\seed.ps1 -Reset
```

Reset local database:

```powershell
.\scripts\reset-db.ps1
```

## API testing

Use Swagger UI at <http://localhost:8001/docs> or the VS Code REST Client file:

```text
http/property-support-ai.http
```

PowerShell example:

```powershell
$response = Invoke-RestMethod `
  -Uri "http://localhost:8001/ask" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message":"Several residents have no heating at Les Érables. What should I do?"}'

$response | ConvertTo-Json -Depth 10
```

## Endpoints

| Method | URL | Purpose |
|---|---|---|
| GET | `/health` | Basic healthcheck |
| GET | `/version` | Version metadata |
| GET | `/data-health` | Database, prompts and graph checks |
| GET | `/demo/examples` | Demo prompts |
| POST | `/ask` | Main GenAI workflow endpoint |
| GET | `/ticket-events` | List safe-mode ticket suggestions |
| GET | `/ticket-events/{event_id}` | Read one ticket event |

## Quality

```powershell
.\scripts\test.ps1
.\scripts\lint.ps1
.\scripts\format.ps1
.\scripts\typecheck.ps1
.\scripts\quality.ps1
```

## Docker demo mode

The Docker image embeds a seed SQLite database at build time. At runtime, it copies the
seed database to `/tmp/property_support.db`. Ticket events are writable during the
container lifetime but reset on container restart.

```powershell
.\scripts\docker-build.ps1
.\scripts\docker-run.ps1
```

## Demo script

1. Open `/docs`.
2. Call `/data-health`.
3. Run the lookup example.
4. Run the incident analysis example.
5. Run the ticket workflow example.
6. Open `/ticket-events` to show the safe-mode suggestion.
7. Open Langfuse and inspect the trace if configured.
8. Explain that this is not an autonomous agent: LangGraph controls the workflow.

## Troubleshooting

| Problem | Fix |
|---|---|
| Ollama connection refused | Run `ollama serve` or `ollama run mistral-nemo:12b` |
| Model missing | Run `ollama pull mistral-nemo:12b` |
| Missing tables | Run `./scripts/migrate.ps1` |
| Empty database | Run `./scripts/seed.ps1 -Reset` |
| Langfuse unavailable | Set `LANGFUSE_ENABLED=false` or configure keys |
| Port 8001 busy | Run uvicorn with another port |

## Documentation

- Setup tutorial: `docs/setup-tutorial.md`
- Technical documentation: `docs/technical-documentation.md`
- User guide: `docs/user-guide.html`
