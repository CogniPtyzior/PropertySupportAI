# Goal
Generate a safe response when the system cannot act with enough confidence.

# Rules
- Return only valid JSON.
- Explain what is missing.
- Ask one clear clarification question if needed.
- Do not invent context.
- Keep it concise and professional.

# User request
{{ user_message }}

# Known context
{{ context_json }}

# Missing fields
{{ missing_fields }}

# Output JSON
{
  "status": "needs_clarification | human_validation_required | partial_answer",
  "summary": "short explanation in French",
  "clarifying_question": null,
  "warnings": [],
  "sources_used": []
}
