"""
PropertySupport AI - app/llm/structured_output.py

Utilities for extracting and validating JSON returned by local LLMs.
"""

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class StructuredOutputError(ValueError):
    """Raised when an LLM output cannot be parsed into the expected schema."""


def extract_first_json_object(raw_text: str) -> dict:
    """Extract the first balanced JSON object from raw LLM output."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[4:].strip()

    start = text.find("{")
    if start == -1:
        raise StructuredOutputError("No JSON object found in LLM output.")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if char == "\\" and in_string:
            escaped = not escaped
            continue
        if char == '"' and not escaped:
            in_string = not in_string
        escaped = False
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : index + 1])
                except json.JSONDecodeError as exc:
                    raise StructuredOutputError("Invalid JSON object in LLM output.") from exc
    raise StructuredOutputError("Unbalanced JSON object in LLM output.")


def parse_model(raw_text: str, schema: type[T]) -> T:
    """Parse and validate raw LLM output against a Pydantic schema."""
    try:
        payload = extract_first_json_object(raw_text)
        return schema.model_validate(payload)
    except (StructuredOutputError, ValidationError) as exc:
        raise StructuredOutputError(str(exc)) from exc
