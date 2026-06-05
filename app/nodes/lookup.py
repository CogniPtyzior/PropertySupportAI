"""
PropertySupport AI - app/nodes/lookup.py

Generates factual answers from retrieved database context.
"""

import json

from app.application.state import PropertySupportState
from app.config import settings
from app.domain.enums import ResponseStatus
from app.llm.prompt_loader import load_prompt
from app.llm.provider import LLMInvocationError, LLMTaskConfig, llm_service
from app.nodes.common import append_path, warning
from app.schemas.llm import LookupAnswerDraft


def generate_lookup_answer_node(state: PropertySupportState) -> dict:
    path = append_path(state, "generate_lookup_answer")
    prompt = load_prompt("generate_lookup_answer.md")
    user_prompt = prompt.replace("{{ user_message }}", state.get("user_message", "")).replace(
        "{{ context_json }}", json.dumps(state.get("context", {}), ensure_ascii=False)
    )

    try:
        draft = llm_service.invoke_json(
            system_prompt="Return valid JSON only. Use only the provided context.",
            user_prompt=user_prompt,
            schema=LookupAnswerDraft,
            task_config=LLMTaskConfig(
                temperature=settings.llm_temperature_reasoning,
                timeout_seconds=settings.llm_timeout_seconds,
            ),
        )
        status = ResponseStatus.SUCCESS if draft.answer_found else ResponseStatus.PARTIAL_ANSWER
        return {
            "final_response": {
                "status": status.value,
                "summary": draft.summary,
                "data": {"answer_found": draft.answer_found},
                "sources_used": draft.sources_used,
            },
            "graph_path": path,
        }
    except LLMInvocationError as exc:
        return {
            "final_response": {
                "status": ResponseStatus.PARTIAL_ANSWER.value,
                "summary": "The answer could not be generated from the local model.",
                "data": {},
                "sources_used": state.get("sources_used", []),
            },
            "warnings": [*state.get("warnings", []), warning("LLM_LOOKUP_FAILED", str(exc))],
            "graph_path": path,
        }
