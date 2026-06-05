# Goal
Extract property support entities from the user message.

# Rules
- Return only valid JSON.
- Do not invent missing values.
- Use null when unknown.
- Keep values short.
- Do not add markdown.

# User message
{{ user_message }}

# Output JSON
{
  "building_name": null,
  "resident_name": null,
  "unit_reference": null,
  "issue_type": null,
  "affected_scope": null,
  "time_hint": null,
  "life_safety_risk": false,
  "requested_action": null
}

# issue_type examples
heating_outage, hot_water_outage, water_leak, major_water_leak,
elevator_outage, elevator_blocked, elevator_blocked_with_person,
electrical_hazard, access_badge, access_blocked, noise_complaint,
cleaning_issue, unknown
