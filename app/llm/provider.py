"""
PropertySupport AI - app/llm/provider.py

LLM provider abstraction. V1 supports Ollama.
"""

from dataclasses import dataclass
from typing import TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from app.config import settings
from app.llm.structured_output import StructuredOutputError, parse_model

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class LLMTaskConfig:
    temperature: float
    timeout_seconds: int


class LLMInvocationError(RuntimeError):
    """Raised when an LLM call fails after configured retries."""


class LLMService:
    """Small LangChain-backed LLM service with JSON output parsing."""

    def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
        task_config: LLMTaskConfig,
    ) -> T:
        if settings.llm_provider != "ollama":
            raise LLMInvocationError("V1 currently supports LLM_PROVIDER=ollama only.")

        last_error: Exception | None = None
        for _attempt in range(settings.llm_max_retries + 1):
            try:
                model = ChatOllama(
                    model=settings.llm_model,
                    base_url=settings.llm_base_url,
                    temperature=task_config.temperature,
                    sync_client_kwargs={"timeout": task_config.timeout_seconds},
                )
                response = model.invoke([SystemMessage(system_prompt), HumanMessage(user_prompt)])
                return parse_model(str(response.content), schema)
            except (StructuredOutputError, Exception) as exc:
                last_error = exc
        raise LLMInvocationError(f"LLM invocation failed: {last_error}")


llm_service = LLMService()
