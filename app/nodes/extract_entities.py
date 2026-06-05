"""
PropertySupport AI - app/nodes/extract_entities.py

Extracts lightweight business entities from the user message.
"""

from app.application.state import PropertySupportState
from app.config import settings
from app.llm.prompt_loader import load_prompt
from app.llm.provider import LLMInvocationError, LLMTaskConfig, llm_service
from app.nodes.common import append_path, warning
from app.schemas.llm import ExtractedEntities


def extract_entities_node(state: PropertySupportState) -> dict:
    path = append_path(state, "extract_entities")
    prompt = load_prompt("extract_entities.md")
    user_prompt = prompt.replace("{{ user_message }}", state.get("user_message", ""))

    try:
        result = llm_service.invoke_json(
            system_prompt="Return valid JSON only. Do not invent missing values.",
            user_prompt=user_prompt,
            schema=ExtractedEntities,
            task_config=LLMTaskConfig(
                temperature=settings.llm_temperature_extraction,
                timeout_seconds=settings.llm_timeout_seconds,
            ),
        )
        return {"entities": result.model_dump(), "graph_path": path}
    except LLMInvocationError as exc:
        return {
            "entities": {},
            "graph_path": path,
            "warnings": [
                *state.get("warnings", []),
                warning("LLM_ENTITY_EXTRACTION_FAILED", str(exc)),
            ],
        }
