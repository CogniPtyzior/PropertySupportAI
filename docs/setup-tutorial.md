# PropertySupport AI — Setup Tutorial

This tutorial explains how to install, configure, run, test and inspect the full
PropertySupport AI stack on Windows with PowerShell and Visual Studio Code.

PropertySupport AI is a production-like GenAI backend demo built with:

- FastAPI
- LangGraph
- LangChain
- Ollama
- SQLAlchemy 2.x
- SQLite
- Alembic
- Langfuse
- Pydantic
- pytest
- Ruff
- Pyright
- Docker

The project is designed as a robust local development demo with:

- explicit LangGraph workflows;
- controlled LLM calls;
- safe-mode ticket handling;
- SQLite database seeded with demo data;
- Langfuse observability;
- tests and quality tooling;
- VS Code configuration.

---

## 1. Target setup

Recommended environment:

```text
OS: Windows 10/11
Shell: PowerShell
Editor: Visual Studio Code 2026
Python: 3.11+
LLM runtime: Ollama
Database: SQLite
Observability: Langfuse
Container runtime: Docker Desktop
```

The tutorial is written for **Windows + PowerShell**.

---

## 2. Install system prerequisites

### 2.1 Install Python 3.11+

Download Python:

```text
https://www.python.org/downloads/
```

During installation, check:

```text
Add python.exe to PATH
```

Then open a new PowerShell terminal and run:

```powershell
python --version
```

Expected result:

```text
Python 3.11.x
```

Python 3.12+ should also work, but Python 3.11 is the safest target for this
project.

---

### 2.2 Install Git

Download Git for Windows:

```text
https://git-scm.com/download/win
```

Check installation:

```powershell
git --version
```

Expected result:

```text
git version ...
```

---

### 2.3 Install Visual Studio Code 2026

Download Visual Studio Code:

```text
https://code.visualstudio.com/
```

After installation, check that the `code` command is available:

```powershell
code --version
```

If the command is not found, open VS Code manually, then enable it from the
Command Palette:

```text
Shell Command: Install 'code' command in PATH
```

On Windows, this is usually configured automatically during installation.

---

### 2.4 Install Docker Desktop

Docker is required for:

- running Langfuse locally;
- building the PropertySupport AI container;
- testing the Docker deployment mode.

Download Docker Desktop:

```text
https://www.docker.com/products/docker-desktop/
```

After installation, start Docker Desktop, then run:

```powershell
docker --version
```

```powershell
docker compose version
```

Expected result:

```text
Docker version ...
Docker Compose version ...
```

---

### 2.5 Install Ollama

Download Ollama:

```text
https://ollama.com/
```

After installation, check:

```powershell
ollama --version
```

Start Ollama if needed:

```powershell
ollama serve
```

If Ollama is already running as a background service, this command may say that
the port is already in use. That is fine.

---

### 2.6 Install uv

`uv` is used to create the Python virtual environment and install dependencies.

Install `uv` with PowerShell:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Close and reopen PowerShell, then check:

```powershell
uv --version
```

Expected result:

```text
uv ...
```

If `uv` is not found, restart Windows or check that the uv installation folder is
in your PATH.

---

## 3. Install the local LLM model

The default recommended model is:

```text
mistral-nemo:12b
```

Pull it with Ollama:

```powershell
ollama pull mistral-nemo:12b
```

Optional faster fallback model:

```powershell
ollama pull qwen2.5-coder:7b
```

List installed models:

```powershell
ollama list
```

Quick test:

```powershell
ollama run mistral-nemo:12b
```

Type:

```text
Reply with a short JSON object containing a hello field.
```

Then exit:

```text
/bye
```

---

## 4. Install VS Code extensions

Open the project folder in VS Code later with:

```powershell
code .
```

The repository includes:

```text
.vscode/extensions.json
```

VS Code should automatically suggest the recommended extensions.

Install at least:

```text
Python
Pylance
Ruff
Docker
REST Client
SQLite Viewer
YAML
Even Better TOML
```

### 4.1 Python extension

Search in VS Code Extensions:

```text
Python
```

Publisher:

```text
Microsoft
```

Used for:

- selecting the Python interpreter;
- running/debugging Python;
- test discovery.

---

### 4.2 Pylance

Search:

```text
Pylance
```

Publisher:

```text
Microsoft
```

Used for:

- type analysis;
- autocompletion;
- import resolution.

---

### 4.3 Ruff

Search:

```text
Ruff
```

Publisher:

```text
Astral Software
```

Used for:

- linting;
- formatting;
- import organization.

The project uses a 100-character line limit.

---

### 4.4 REST Client

Search:

```text
REST Client
```

Publisher:

```text
Huachao Mao
```

Used to run HTTP requests directly from:

```text
http/property-support-ai.http
```

---

### 4.5 SQLite Viewer

Search:

```text
SQLite Viewer
```

Used to inspect:

```text
property_support.db
```

Main tables to inspect:

```text
buildings
tickets
ticket_events
contracts
providers
procedures
```

---

### 4.6 Docker extension

Search:

```text
Docker
```

Publisher:

```text
Microsoft
```

Used to inspect local containers and images.

---

## 5. Optional: install a LangGraph visualizer extension

A LangGraph visualizer extension can help inspect the graph structure inside
VS Code.

Search for:

```text
LangGraph Visualizer
```

If available, install it.

The graph is defined in:

```text
app/application/graph.py
```

The important function is:

```text
build_graph()
```

If the extension does not detect the graph automatically, you can still inspect:

```text
app/application/graph.py
app/application/state.py
app/nodes/
```

Runtime execution is also observable through Langfuse, especially through the
recorded `graph_path`.

---

## 6. Open the project

From PowerShell, go to the project folder:

```powershell
cd C:\Path\To\property-support-genai
```

Open it in VS Code:

```powershell
code .
```

The project root should contain:

```text
README.md
pyproject.toml
alembic.ini
.env.example
app/
scripts/
docs/
tests/
```

---

## 7. Configure PowerShell script execution

If PowerShell blocks local scripts, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then confirm with:

```text
Y
```

This allows local project scripts such as:

```powershell
.\scripts\install.ps1
```

---

## 8. Create the `.env` file

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Open `.env` in VS Code:

```powershell
code .env
```

Recommended local settings:

```env
APP_ENV=local
APP_DEBUG=true
APP_VERSION=0.1.0

DATABASE_URL=sqlite:///./property_support.db
DATABASE_ECHO=false

SAFE_MODE=true
WRITE_TICKET_EVENTS=true
DRY_RUN=false

LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=mistral-nemo:12b
LLM_TIMEOUT_SECONDS=90
LLM_MAX_RETRIES=1

REQUEST_TIMEOUT_SECONDS=120
DATABASE_TIMEOUT_SECONDS=10

LLM_TEMPERATURE_CLASSIFICATION=0.0
LLM_TEMPERATURE_EXTRACTION=0.0
LLM_TEMPERATURE_REASONING=0.1
LLM_TEMPERATURE_WRITING=0.3

LANGFUSE_ENABLED=false
LANGFUSE_HOST=http://localhost:3001
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=

LOG_LEVEL=INFO
LOG_FORMAT=human

API_MAX_MESSAGE_LENGTH=4000
INCLUDE_DEBUG_METADATA=true
INCLUDE_GRAPH_PATH=true
MIN_CLASSIFICATION_CONFIDENCE=0.60
DUPLICATE_TICKET_WINDOW_HOURS=72
MAX_RECENT_TICKETS=20
```

Start with:

```env
LANGFUSE_ENABLED=false
```

You can enable Langfuse later after creating keys.

---

## 9. Install Python dependencies

Run:

```powershell
.\scripts\install.ps1
```

Manual equivalent:

```powershell
uv venv
```

```powershell
uv pip install -e ".[dev]"
```

Activate the virtual environment if needed:

```powershell
.\.venv\Scripts\Activate.ps1
```

Check Python interpreter:

```powershell
python --version
```

Check installed packages:

```powershell
python -m pip list
```

---

## 10. Select the VS Code Python interpreter

In VS Code:

1. Press:

```text
Ctrl+Shift+P
```

2. Search:

```text
Python: Select Interpreter
```

3. Select:

```text
.venv\Scripts\python.exe
```

This ensures VS Code, Pylance, pytest and Ruff use the project virtual
environment.

---

## 11. Run database migrations

Apply Alembic migrations:

```powershell
.\scripts\migrate.ps1
```

Manual equivalent:

```powershell
alembic upgrade head
```

Check current migration:

```powershell
alembic current
```

Show migration history:

```powershell
alembic history
```

If migrations fail, check:

```powershell
Get-Content .env
```

Make sure:

```env
DATABASE_URL=sqlite:///./property_support.db
```

---

## 12. Seed the database

Seed the local SQLite database:

```powershell
.\scripts\seed.ps1 -Reset
```

Manual equivalent:

```powershell
python -m scripts.seed_db --reset
```

Expected result:

```text
Database seeded successfully
```

The seed creates demo data for:

```text
buildings
units
residents
providers
contracts
procedures
tickets
ticket_events
interventions
knowledge_base_entries
```

---

## 13. Inspect the local database

The local database file is:

```text
property_support.db
```

### Option A — VS Code SQLite Viewer

In VS Code:

1. Open Explorer.
2. Click `property_support.db`.
3. Use SQLite Viewer to inspect tables.

Recommended tables:

```text
buildings
providers
contracts
tickets
ticket_events
procedures
```

### Option B — sqlite3 CLI

If sqlite3 is installed:

```powershell
sqlite3 property_support.db
```

Then run:

```sql
.tables
```

```sql
SELECT id, name, city FROM buildings;
```

```sql
SELECT id, title, status FROM tickets;
```

```sql
SELECT id, event_type, created_at FROM ticket_events;
```

Exit:

```sql
.exit
```

---

## 14. Start Ollama

Make sure Ollama is running.

In a dedicated PowerShell terminal:

```powershell
ollama serve
```

In another terminal, verify the model:

```powershell
ollama list
```

Expected:

```text
mistral-nemo:12b
```

If missing:

```powershell
ollama pull mistral-nemo:12b
```

---

## 15. Start the FastAPI application

Run:

```powershell
.\scripts\dev.ps1
```

Manual equivalent:

```powershell
uvicorn app.main:app --reload
```

Expected output:

```text
Uvicorn running on http://127.0.0.1:8001
```

Keep this terminal open.

---

## 16. Open FastAPI documentation

Open Swagger UI:

```text
http://localhost:8001/docs
```

Open ReDoc:

```text
http://localhost:8001/redoc
```

Useful endpoints:

```text
GET  /health
GET  /version
GET  /data-health
GET  /demo/examples
POST /ask
GET  /ticket-events
GET  /ticket-events/{event_id}
```

---

## 17. Check application health

From PowerShell:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8001/health" `
  -Method Get
```

Expected output:

```text
status app version environment
------ --- ------- -----------
ok     ... ...
```

Detailed JSON:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8001/health" `
  -Method Get | ConvertTo-Json -Depth 10
```

---

## 18. Check data health

Run:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8001/data-health" `
  -Method Get | ConvertTo-Json -Depth 10
```

Expected result:

```json
{
  "status": "ok",
  "database": "ok",
  "tables": "ok",
  "seed_data": "ok",
  "graph": "compiled",
  "prompts": "ok"
}
```

If this fails, run again:

```powershell
.\scripts\migrate.ps1
```

```powershell
.\scripts\seed.ps1 -Reset
```

---

## 19. Test `/ask` with Swagger UI

Open:

```text
http://localhost:8001/docs
```

Expand:

```text
POST /ask
```

Click:

```text
Try it out
```

Use:

```json
{
  "message": "Plusieurs résidents n’ont plus de chauffage aux Érables. Que dois-je faire ?"
}
```

Click:

```text
Execute
```

Expected behavior:

- the request is classified;
- entities are extracted;
- the graph selects `incident_analysis`;
- database context is retrieved;
- the LLM generates a structured response;
- the API returns sources.

---

## 20. Test `/ask` with PowerShell

### 20.1 Incident analysis

```powershell
$body = @{
  message = "Plusieurs résidents n’ont plus de chauffage aux Érables. Que dois-je faire ?"
} | ConvertTo-Json

$response = Invoke-RestMethod `
  -Uri "http://localhost:8001/ask" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body

$response | ConvertTo-Json -Depth 10
```

Expected branch:

```text
incident_analysis
```

---

### 20.2 Lookup

```powershell
$body = @{
  message = "Qui est le prestataire chauffage des Érables ?"
} | ConvertTo-Json

$response = Invoke-RestMethod `
  -Uri "http://localhost:8001/ask" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body

$response | ConvertTo-Json -Depth 10
```

Expected branch:

```text
lookup
```

---

### 20.3 Communication

```powershell
$body = @{
  message = "Prépare un message aux résidents pour l’intervention chauffage demain."
} | ConvertTo-Json

$response = Invoke-RestMethod `
  -Uri "http://localhost:8001/ask" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body

$response | ConvertTo-Json -Depth 10
```

Expected branch:

```text
communication
```

---

### 20.4 Ticket workflow

```powershell
$body = @{
  message = "Ajoute au ticket chauffage que trois résidents supplémentaires ont signalé la panne."
} | ConvertTo-Json

$response = Invoke-RestMethod `
  -Uri "http://localhost:8001/ask" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body

$response | ConvertTo-Json -Depth 10
```

Expected branch:

```text
ticket_workflow
```

Expected behavior:

```text
No direct ticket mutation.
A safe-mode ticket event suggestion is written to ticket_events.
```

Inspect ticket events:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8001/ticket-events" `
  -Method Get | ConvertTo-Json -Depth 10
```

---

### 20.5 Clarification

```powershell
$body = @{
  message = "Il y a un problème dans l’immeuble."
} | ConvertTo-Json

$response = Invoke-RestMethod `
  -Uri "http://localhost:8001/ask" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body

$response | ConvertTo-Json -Depth 10
```

Expected branch:

```text
clarification
```

Expected status:

```text
needs_clarification
```

---

## 21. Test the API with VS Code REST Client

Open:

```text
http/property-support-ai.http
```

You should see several requests, each with:

```text
Send Request
```

Run these scenarios:

1. Healthcheck
2. Data health
3. Demo examples
4. Lookup
5. Communication
6. Ticket workflow
7. Incident analysis
8. Clarification
9. Ticket events

This is the recommended way to run demos from VS Code.

---

## 22. Enable Langfuse locally

Langfuse is optional but recommended for observing GenAI traces.

It helps inspect:

- request id;
- selected branch;
- graph path;
- prompts;
- LLM outputs;
- sources used;
- errors and warnings;
- ticket event metadata.

---

### 22.1 Start Langfuse with Docker Compose

If the project includes a Docker Compose file for Langfuse, run:

```powershell
docker compose up -d
```

Then open:

```text
http://localhost:3001
```

Create a Langfuse account/project in the local UI.

Copy:

```text
Public key
Secret key
```

---

### 22.2 Configure `.env`

Update:

```env
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://localhost:3001
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
```

Restart FastAPI:

```powershell
.\scripts\dev.ps1
```

Run an `/ask` request.

Open Langfuse and inspect the new trace.

---

### 22.3 Disable Langfuse

If Langfuse is unavailable, set:

```env
LANGFUSE_ENABLED=false
```

Restart FastAPI.

The application should continue working normally.

---

## 23. Understand the safe-mode design

PropertySupport AI is intentionally designed as:

```text
LLM-assisted workflow, not autonomous agent.
```

Important rule:

```text
The GenAI workflow never directly modifies tickets.
```

Instead:

```text
tickets       = current ticket state, read-only for GenAI workflow
ticket_events = safe-mode AI suggestions and audit trail
```

For example, when the user asks:

```text
Ajoute au ticket chauffage que trois résidents supplémentaires ont signalé la panne.
```

The application should:

1. identify the related ticket;
2. generate a safe update suggestion;
3. validate the suggestion;
4. write an event to `ticket_events`;
5. return the suggestion to the user.

It should not update the `tickets` table directly.

---

## 24. Understand the LangGraph workflow

Main graph file:

```text
app/application/graph.py
```

State definition:

```text
app/application/state.py
```

Node files:

```text
app/nodes/
```

High-level workflow:

```text
FastAPI /ask
  -> initialize state
  -> classify request
  -> extract entities
  -> route intent
      -> clarification
      -> lookup
      -> communication
      -> ticket_workflow
      -> incident_analysis
  -> validate response
  -> return JSON
```

Main branches:

```text
clarification
lookup
communication
ticket_workflow
incident_analysis
```

Internal branches:

```text
ticket_update_suggestion
ticket_create_suggestion
emergency_escalation
provider_action_plan
human_validation_required
```

---

## 25. Use LangGraph Visualizer

If a LangGraph visualizer extension is installed:

1. Open:

```text
app/application/graph.py
```

2. Locate:

```text
build_graph()
```

3. Use the extension command to visualize the graph.

If visualization does not work, inspect the code manually and use Langfuse
runtime traces.

The graph is intentionally centralized and readable.

---

## 26. Run tests

Run all tests:

```powershell
.\scripts\test.ps1
```

Manual equivalent:

```powershell
pytest
```

Run tests with coverage:

```powershell
pytest --cov=app --cov-report=term-missing
```

Optional Ollama tests, if defined:

```powershell
pytest -m ollama
```

Standard tests should not require external LLM calls.

---

## 27. Run quality checks

Run linting:

```powershell
.\scripts\lint.ps1
```

Manual equivalent:

```powershell
ruff check .
```

Format code:

```powershell
.\scripts\format.ps1
```

Manual equivalent:

```powershell
ruff format .
```

Run type checking:

```powershell
.\scripts\typecheck.ps1
```

Manual equivalent:

```powershell
pyright
```

Run the full quality pipeline:

```powershell
.\scripts\quality.ps1
```

This should run:

```text
ruff check
pyright
pytest
```

---

## 28. Create a new database migration

After modifying SQLAlchemy models, create a migration:

```powershell
.\scripts\new-migration.ps1 -Message "add new field"
```

Manual equivalent:

```powershell
alembic revision --autogenerate -m "add new field"
```

Review the generated migration under:

```text
alembic/versions/
```

Then apply it:

```powershell
.\scripts\migrate.ps1
```

Never blindly trust autogenerated migrations. Always inspect them.

---

## 29. Reset the local database

Stop FastAPI first if needed.

Remove the database:

```powershell
Remove-Item .\property_support.db -ErrorAction SilentlyContinue
```

Apply migrations:

```powershell
.\scripts\migrate.ps1
```

Seed data:

```powershell
.\scripts\seed.ps1 -Reset
```

Restart FastAPI:

```powershell
.\scripts\dev.ps1
```

Verify:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8001/data-health" `
  -Method Get | ConvertTo-Json -Depth 10
```

---

## 30. Build the Docker image

Build:

```powershell
.\scripts\docker-build.ps1
```

Manual equivalent:

```powershell
docker build -t property-support-genai:latest .
```

---

## 31. Run the Docker container

Run:

```powershell
.\scripts\docker-run.ps1
```

Manual equivalent:

```powershell
docker run --rm `
  -p 8001:8001 `
  --env-file .env `
  property-support-genai:latest
```

Open:

```text
http://localhost:8001/docs
```

---

## 32. Docker demo mode with embedded SQLite

The Docker demo mode may embed a seeded SQLite database in the image.

Recommended behavior:

```text
Build time:
  - run Alembic migrations
  - run seed script
  - create property_support_seed.db

Runtime:
  - copy seed DB to /tmp/property_support.db
  - run FastAPI
```

This makes the container demo reproducible.

Important limitation:

```text
Ticket events written at runtime are temporary.
They are lost when the container restarts or is redeployed.
```

This is acceptable for a demo, not for persistent production.

---

## 33. Demo flow for interviews

Use this sequence during a technical presentation.

### 33.1 Start services

Start Ollama:

```powershell
ollama serve
```

Start FastAPI:

```powershell
.\scripts\dev.ps1
```

Optional Langfuse:

```powershell
docker compose up -d
```

---

### 33.2 Open Swagger

Open:

```text
http://localhost:8001/docs
```

Show:

```text
/health
/data-health
/ask
/ticket-events
```

---

### 33.3 Run data-health

Call:

```text
GET /data-health
```

Explain:

```text
The application validates that the database, seed data, prompts and graph are ready.
```

---

### 33.4 Run lookup scenario

Prompt:

```text
Qui est le prestataire chauffage des Érables ?
```

Expected:

```text
lookup branch
factual sourced answer
```

---

### 33.5 Run incident analysis scenario

Prompt:

```text
Plusieurs résidents n’ont plus de chauffage aux Érables. Que dois-je faire ?
```

Expected:

```text
incident_analysis branch
action plan
provider context
ticket context
sources
```

---

### 33.6 Run ticket workflow scenario

Prompt:

```text
Ajoute au ticket chauffage que trois résidents supplémentaires ont signalé la panne.
```

Expected:

```text
ticket_workflow branch
safe-mode update suggestion
ticket_event created
tickets table not directly modified
```

Then show:

```text
GET /ticket-events
```

---

### 33.7 Show Langfuse trace

If Langfuse is enabled, open:

```text
http://localhost:3001
```

Show:

- selected branch;
- graph path;
- LLM calls;
- context sources;
- generated response;
- warnings/errors if any.

Explain:

```text
This is an LLM-assisted workflow, not an autonomous agent.
LangGraph controls the workflow.
The LLM helps classify, extract and draft.
Business decisions remain deterministic and safe.
```

---

## 34. Troubleshooting

### 34.1 PowerShell blocks scripts

Error:

```text
running scripts is disabled on this system
```

Fix:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

### 34.2 `uv` is not found

Check:

```powershell
uv --version
```

If missing, reinstall:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Restart PowerShell.

---

### 34.3 Ollama is not reachable

Check:

```powershell
ollama list
```

Start Ollama:

```powershell
ollama serve
```

Check `.env`:

```env
LLM_BASE_URL=http://localhost:11434
```

---

### 34.4 Ollama model is missing

List models:

```powershell
ollama list
```

Pull the model:

```powershell
ollama pull mistral-nemo:12b
```

---

### 34.5 FastAPI port already in use

Run on another port:

```powershell
uvicorn app.main:app --reload --port 8001
```

Open:

```text
http://localhost:8001/docs
```

---

### 34.6 Database tables are missing

Run:

```powershell
.\scripts\migrate.ps1
```

Then:

```powershell
.\scripts\seed.ps1 -Reset
```

---

### 34.7 Seed fails

Check migration state:

```powershell
alembic current
```

Re-run seed:

```powershell
python -m scripts.seed_db --reset
```

---

### 34.8 Langfuse is unavailable

Disable Langfuse:

```env
LANGFUSE_ENABLED=false
```

Restart FastAPI:

```powershell
.\scripts\dev.ps1
```

Langfuse must not block the application.

---

### 34.9 LLM returns invalid JSON

Local models can sometimes return malformed output.

The application should:

- extract the first JSON object if possible;
- validate it with Pydantic;
- fallback to a safe response if invalid.

You can reduce randomness:

```env
LLM_TEMPERATURE_CLASSIFICATION=0.0
LLM_TEMPERATURE_EXTRACTION=0.0
LLM_TEMPERATURE_REASONING=0.1
```

---

### 34.10 VS Code does not detect `.venv`

Select interpreter manually:

1. Press:

```text
Ctrl+Shift+P
```

2. Select:

```text
Python: Select Interpreter
```

3. Choose:

```text
.venv\Scripts\python.exe
```

---

### 34.11 REST Client does not show `Send Request`

Install the REST Client extension.

Open:

```text
http/property-support-ai.http
```

---

### 34.12 LangGraph Visualizer does not detect the graph

Open:

```text
app/application/graph.py
```

Look for:

```text
build_graph()
```

If visualization still fails, use Langfuse runtime traces and inspect
`graph_path`.

---

## 35. Common command summary

Install dependencies:

```powershell
.\scripts\install.ps1
```

Apply migrations:

```powershell
.\scripts\migrate.ps1
```

Seed database:

```powershell
.\scripts\seed.ps1 -Reset
```

Run API:

```powershell
.\scripts\dev.ps1
```

Run tests:

```powershell
.\scripts\test.ps1
```

Run quality checks:

```powershell
.\scripts\quality.ps1
```

Open Swagger:

```text
http://localhost:8001/docs
```

Open ReDoc:

```text
http://localhost:8001/redoc
```

Inspect ticket events:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8001/ticket-events" `
  -Method Get | ConvertTo-Json -Depth 10
```

Reset database:

```powershell
Remove-Item .\property_support.db -ErrorAction SilentlyContinue
.\scripts\migrate.ps1
.\scripts\seed.ps1 -Reset
```

Build Docker image:

```powershell
.\scripts\docker-build.ps1
```

Run Docker container:

```powershell
.\scripts\docker-run.ps1
```

---

## 36. Final mental model

PropertySupport AI follows this architecture:

```text
FastAPI
  -> Pydantic request validation
  -> LangGraph workflow
  -> SQLAlchemy repositories
  -> SQLite business context
  -> controlled LangChain / LLM calls
  -> Pydantic response validation
  -> safe-mode ticket events
  -> Langfuse observability
```

The core design principle is:

```text
LLM-assisted workflow, not autonomous agent.
```

The most important safety rule is:

```text
The GenAI workflow never directly modifies tickets.
It only writes human-validation suggestions to ticket_events.
```

This makes the project suitable as a serious production-like GenAI backend demo.
