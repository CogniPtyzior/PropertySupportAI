"""
PropertySupport AI - app/nodes/classify.py

Classifies the incoming message into one workflow intent.
"""

from app.application.state import PropertySupportState
from app.config import settings
from app.domain.enums import Intent
from app.llm.prompt_loader import load_prompt
from app.llm.provider import LLMInvocationError, LLMTaskConfig, llm_service
from app.nodes.common import append_path, warning
from app.schemas.llm import ClassificationResult


def classify_request_node(state: PropertySupportState) -> dict:
    path = append_path(state, "classify_request")
    prompt = load_prompt("classify_request.md")
    user_prompt = prompt.replace("{{ user_message }}", state.get("user_message", ""))

    try:
        result = llm_service.invoke_json(
            system_prompt="Return valid JSON only.",
            user_prompt=user_prompt,
            schema=ClassificationResult,
            task_config=LLMTaskConfig(
                temperature=settings.llm_temperature_classification,
                timeout_seconds=settings.llm_timeout_seconds,
            ),
        )
        if result.confidence < settings.min_classification_confidence:
            return {
                "intent": Intent.CLARIFICATION.value,
                "selected_branch": Intent.CLARIFICATION.value,
                "confidence": result.confidence,
                "graph_path": path,
                "warnings": [
                    *state.get("warnings", []),
                    warning("LLM_LOW_CONFIDENCE", "Classification confidence is too low."),
                ],
            }
        return {
            "intent": result.intent.value,
            "selected_branch": result.intent.value,
            "confidence": result.confidence,
            "graph_path": path,
        }
    except LLMInvocationError as exc:
        return {
            "intent": Intent.CLARIFICATION.value,
            "selected_branch": Intent.CLARIFICATION.value,
            "confidence": 0.0,
            "graph_path": path,
            "warnings": [
                *state.get("warnings", []),
                warning("LLM_CLASSIFICATION_FAILED", str(exc)),
            ],
        }
