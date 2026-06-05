"""
PropertySupport AI - app/nodes/communication.py

Generates safe French message drafts from retrieved context.
"""

import json

from app.application.state import PropertySupportState
from app.config import settings
from app.domain.enums import ResponseStatus
from app.llm.prompt_loader import load_prompt
from app.llm.provider import LLMInvocationError, LLMTaskConfig, llm_service
from app.nodes.common import append_path, warning
from app.schemas.llm import MessageDraft


def generate_message_draft_node(state: PropertySupportState) -> dict:
    path = append_path(state, "generate_message_draft")
    prompt = load_prompt("generate_message_draft.md")
    user_prompt = prompt.replace("{{ user_message }}", state.get("user_message", "")).replace(
        "{{ context_json }}", json.dumps(state.get("context", {}), ensure_ascii=False)
    )

    try:
        draft = llm_service.invoke_json(
            system_prompt="Return valid JSON only. Do not invent facts.",
            user_prompt=user_prompt,
            schema=MessageDraft,
            task_config=LLMTaskConfig(
                temperature=settings.llm_temperature_writing,
                timeout_seconds=settings.llm_timeout_seconds,
            ),
        )
        return {
            "final_response": {
                "status": ResponseStatus.SUCCESS.value,
                "summary": "A message draft was generated.",
                "data": draft.model_dump(),
                "sources_used": draft.sources_used,
            },
            "graph_path": path,
        }
    except LLMInvocationError as exc:
        return {
            "final_response": {
                "status": ResponseStatus.PARTIAL_ANSWER.value,
                "summary": "The message draft could not be generated.",
                "data": {},
                "sources_used": state.get("sources_used", []),
            },
            "warnings": [*state.get("warnings", []), warning("LLM_MESSAGE_FAILED", str(exc))],
            "graph_path": path,
        }
