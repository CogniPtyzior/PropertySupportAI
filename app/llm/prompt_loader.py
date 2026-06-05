"""
PropertySupport AI - app/llm/prompt_loader.py

Small prompt loader for versioned markdown prompt assets.
"""

from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"

REQUIRED_PROMPTS = [
    "classify_request.md",
    "extract_entities.md",
    "generate_lookup_answer.md",
    "generate_message_draft.md",
    "generate_ticket_suggestion.md",
    "generate_incident_response.md",
    "generate_emergency_response.md",
    "generate_safe_response.md",
]


def load_prompt(name: str) -> str:
    """Load a prompt from the prompt assets directory."""
    path = PROMPT_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def validate_required_prompts() -> list[str]:
    """Return missing prompt names."""
    return [name for name in REQUIRED_PROMPTS if not (PROMPT_DIR / name).exists()]
