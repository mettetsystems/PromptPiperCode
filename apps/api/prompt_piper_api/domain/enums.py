from enum import StrEnum


class SessionState(StrEnum):
    """Workflow stage for a prompt design session."""

    INTAKE = "intake"
    CLARIFYING = "clarifying"
    EDIT = "edit"
    FINALIZED = "finalized"
    SIMILARITY_CHECK = "similarity_check"
    ARTIFACT_GENERATION = "artifact_generation"
    OPTIMIZATION = "optimization"
    APPROVAL = "approval"
    EXPORTED = "exported"
