"""
PropertySupport AI - app/domain/enums.py

Stable application and domain enums.
"""

from enum import StrEnum


class Intent(StrEnum):
    LOOKUP = "lookup"
    COMMUNICATION = "communication"
    TICKET_WORKFLOW = "ticket_workflow"
    INCIDENT_ANALYSIS = "incident_analysis"
    CLARIFICATION = "clarification"


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL_ANSWER = "partial_answer"
    NEEDS_CLARIFICATION = "needs_clarification"
    HUMAN_VALIDATION_REQUIRED = "human_validation_required"
    TICKET_EVENT_CREATED = "ticket_event_created"
    ERROR = "error"


class Priority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_PROVIDER = "waiting_provider"
    CLOSED = "closed"


class TicketAction(StrEnum):
    UPDATE_SUGGESTION = "ticket_update_suggestion"
    CREATE_SUGGESTION = "ticket_create_suggestion"
    NONE = "none"


class IncidentAction(StrEnum):
    EMERGENCY_ESCALATION = "emergency_escalation"
    PROVIDER_ACTION_PLAN = "provider_action_plan"
    HUMAN_VALIDATION_REQUIRED = "human_validation_required"
    CLARIFICATION = "clarification"


class TicketEventType(StrEnum):
    AI_UPDATE_SUGGESTED = "ai_update_suggested"
    AI_CREATION_SUGGESTED = "ai_creation_suggested"
    HUMAN_COMMENT_ADDED = "human_comment_added"
