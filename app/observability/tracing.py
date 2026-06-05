"""
PropertySupport AI - app/observability/tracing.py

Non-blocking Langfuse observability helpers.

This module uses the current Langfuse SDK style based on get_client() and
start_as_current_observation(). Langfuse must never be a hard dependency for the
API: if it is disabled, misconfigured or temporarily unavailable, the workflow
continues without tracing.
"""

from __future__ import annotations

import os
from contextlib import nullcontext, suppress
from functools import lru_cache
from typing import Any
from uuid import uuid4

from app.config import settings

try:
    from langfuse import get_client
except Exception:  # pragma: no cover - Langfuse is optional at runtime.
    get_client = None  # type: ignore[assignment]


def _configure_langfuse_environment() -> None:
    """Populate environment variables expected by the Langfuse SDK."""
    if settings.langfuse_public_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key

    if settings.langfuse_secret_key:
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key

    base_url = settings.langfuse_base_url or settings.langfuse_host
    if base_url:
        os.environ["LANGFUSE_BASE_URL"] = base_url

    os.environ.setdefault("LANGFUSE_TRACING_ENVIRONMENT", settings.langfuse_environment)
    os.environ.setdefault("LANGFUSE_RELEASE", settings.langfuse_release)


def _is_langfuse_configured() -> bool:
    """Return True when Langfuse has the minimum required configuration."""
    return bool(
        settings.langfuse_enabled
        and settings.langfuse_public_key
        and settings.langfuse_secret_key
        and (settings.langfuse_base_url or settings.langfuse_host)
        and get_client is not None
    )


@lru_cache(maxsize=1)
def _get_langfuse_client() -> Any | None:
    """Return a cached Langfuse client or None when tracing is unavailable."""
    if not _is_langfuse_configured():
        return None

    try:
        _configure_langfuse_environment()
        return get_client()  # type: ignore[misc]
    except Exception:
        return None


class WorkflowTracer:
    """Best-effort Langfuse tracer wrapper."""

    def __init__(self) -> None:
        self.trace_id: str | None = None

    def start_trace(self, request_id: str, message: str) -> str:
        """
        Create a stable local trace identifier for API responses.

        Langfuse generates its own trace identifiers internally. The local id is
        still useful in API responses and ticket events, even if Langfuse is not
        available.
        """
        self.trace_id = f"trace-{uuid4().hex[:12]}"
        return self.trace_id

    def request_observation(
        self,
        *,
        request_id: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ):
        """Start the root Langfuse observation for one /ask request."""
        client = _get_langfuse_client()
        if client is None:
            return nullcontext()

        observation_metadata = {
            "request_id": request_id,
            "environment": settings.app_env,
            "model": settings.llm_model,
            "llm_provider": settings.llm_provider,
            "safe_mode": settings.safe_mode,
            **(metadata or {}),
        }

        try:
            return client.start_as_current_observation(
                name="property-support-ai-request",
                as_type="span",
                input={"message": message},
                metadata=observation_metadata,
            )
        except Exception:
            return nullcontext()

    def observe_node(self, node_name: str, metadata: dict[str, Any]) -> None:
        """Record a short child observation for a workflow node."""
        client = _get_langfuse_client()
        if client is None:
            return

        with (
            suppress(Exception),
            client.start_as_current_observation(
                name=node_name,
                as_type="span",
                input=metadata.get("input"),
                metadata=metadata,
            ) as observation,
        ):
            observation.update(output=metadata.get("output"))

    def update_current_observation(self, output: dict[str, Any]) -> None:
        """Update the current observation output when the SDK exposes it."""
        client = _get_langfuse_client()
        if client is None:
            return

        with suppress(Exception):
            current_observation = client.get_current_observation()
            if current_observation is not None:
                current_observation.update(output=output)

    def score(self, name: str, value: float | bool) -> None:
        """Record a best-effort score on the current trace."""
        client = _get_langfuse_client()
        if client is None:
            return

        with suppress(Exception):
            if hasattr(client, "score_current_trace"):
                client.score_current_trace(name=name, value=value)

    def flush(self) -> None:
        """Flush pending Langfuse events."""
        client = _get_langfuse_client()
        if client is None:
            return

        with suppress(Exception):
            client.flush()


tracer = WorkflowTracer()
