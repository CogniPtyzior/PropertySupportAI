"""
PropertySupport AI - app/main.py

FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.api.routes import router
from app.application.graph import build_graph
from app.config import settings
from app.db.session import SessionLocal
from app.llm.prompt_loader import validate_required_prompts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate startup assets without making observability a hard dependency."""
    missing_prompts = validate_required_prompts()
    if missing_prompts:
        raise RuntimeError(f"Missing prompt assets: {missing_prompts}")
    with SessionLocal() as session:
        build_graph(session)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="GenAI workflow assistant for property support teams.",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health and status endpoints",
        },
    ],
)
app.include_router(router)

for route in app.routes:
    if isinstance(route, APIRoute):
        print(route.path, route.methods, route.tags)
